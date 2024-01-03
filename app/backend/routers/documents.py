import asyncio
import datetime
import os
import io
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel, Field
from pypdf import PdfReader, PdfWriter
from sse_starlette.sse import EventSourceResponse
from concurrent.futures import ThreadPoolExecutor


from core.db import get_db
from core.types import Document, Log, Status
from core.logger import logger
from core.utilities import (
    blob_name_from_file_page,
    get_document_text,
    get_filename_from_url,
    hash_text_md5,
    remove_from_index,
    scrape_url,
    update_embeddings_in_batch,
    create_sections,
    index_sections,
    create_sections_string,
)


document_router = APIRouter()
executor = ThreadPoolExecutor(max_workers=5)


# Create a new document
@document_router.post("/")
async def create_document(request: Request, db=Depends(get_db)):
    try:
        data = await request.json()
        doc = Document(**data)
        doc = doc.model_dump()

        if doc["type"] == "web":
            doc["file"] = get_filename_from_url(doc["url"])

            asyncio.create_task(index_and_save_async(doc, db, request.app.search_client))

        doc["status"] = Status.processing.value
        db.documents.insert_one(doc)

        del doc["_id"]

        return doc
    except Exception as ex:
        logger.info("Failed to create document")
        logger.info("Exception: {}".format(ex))
        return {"error": "Exception: {}".format(ex)}


async def index_and_save_async(doc, db, search_client):
    url = doc["url"]

    if url is None:
        return

    text = await scrape_url(url)

    hashed_text = hash_text_md5(text)

    pages = list(
        create_sections_string(
            url,
            text,
        )
    )

    logger.info("Got sections. updating embeddings")

    sections = update_embeddings_in_batch(pages)

    logger.info("Updated embeddings. indexing sections")
    filename = get_filename_from_url(url)
    await index_sections(filename, sections, search_client)

    db.documents.update_one({"id": doc["id"]}, {"$set": {"status": Status.done.value, "hash": hashed_text}})


# typing for get all documents request
class GetDocumentsRequest(BaseModel):
    limit: int = 10
    skip: int = 0
    search: str = ""
    flagged: str = "false"
    pdf: str = "true"
    web: str = "true"
    order_by: str = "updated_at"
    order: str = "desc"


# Get all documents
@document_router.get("/")
async def get_documents(params: GetDocumentsRequest = Depends(), db=Depends(get_db)):
    try:
        logger.info("Getting documents")
        typeQuery = []
        if params.pdf == "true":
            typeQuery.append("pdf")

        if params.web == "true":
            typeQuery.append("web")

        query = {
            "deleted": {"$ne": True},
            "type": {"$in": typeQuery},
        }

        if params.search:
            query["$or"] = [
                {"title": {"$regex": params.search, "$options": "i"}},
                {"file": {"$regex": params.search, "$options": "i"}},
                {"url": {"$regex": params.search, "$options": "i"}},
            ]

        if params.flagged == "true":
            query["flagged_pages"] = {"$exists": True, "$ne": []}

        cursor = db.documents.find(query)
        total = db.documents.count_documents(query)

        if params.limit:
            cursor = cursor.limit(params.limit)

        if params.skip > 0:
            cursor = cursor.skip(params.skip)

        if params.order_by and params.order:
            order = 1 if params.order == "asc" else -1
            cursor = cursor.sort(params.order_by, order)

        if not cursor:
            raise Exception("No documents found")

        documents = [Document(**doc) for doc in cursor]

        return {"documents": documents, "total": total}
    except Exception as ex:
        logger.error("Failed to get documents")
        logger.error("Exception: {}".format(ex))
        raise HTTPException(status_code=404, detail="Document not found")


# Get a specific document by ID
@document_router.get("/{id}")
def get_document(id: str, db=Depends(get_db)):
    if not id:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = db.documents.find_one({"id": id})

    if doc:
        doc["logs"] = sorted(doc["logs"], key=lambda x: x["created_at"], reverse=True)

        return Document(**doc)
    else:
        raise HTTPException(status_code=404, detail="Document not found")


@document_router.get("/status/{id}")
async def get_document_status_events(id: str, db=Depends(get_db)):
    if not id:
        raise HTTPException(status_code=404, detail="No id provided")

    async def event_generator():
        while True:
            # Check for updates on the document status
            doc = db.documents.find_one({"id": id})
            doc = Document(**doc)

            if not doc:
                break

            yield {"data": doc.status}

            if doc.status != Status.processing.value:
                break

            # Wait for a short time before checking again
            await asyncio.sleep(10)

    return EventSourceResponse(event_generator())


# Check if document is flagged based on citation / file_page
@document_router.get("/flag/{citation}")
def get_document(citation, db=Depends(get_db)):
    if not citation:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = db.documents.find_one({"flagged_pages": citation})

    if doc:
        return {"flagged": True}
    else:
        return {"flagged": False}


class FlagCitations(BaseModel):
    citations: List[str] = Field(default=[])
    message: str = Field(default=None)


# Flag a specific document by citation / file_page
@document_router.post("/flag")
def flag_document(request: Request, data: FlagCitations, db=Depends(get_db)):
    if not data.citations:
        raise HTTPException(status_code=404, detail="Document not found")

    for citation in data.citations:
        doc = db.documents.find_one({"$or": [{"file": citation}, {"file_pages": citation}, {"url": citation}]})

        if doc is None:
            logger.info("Document not found")
            continue

        change = "flagged"
        message = data.message + ": " + citation
        log = Log(user=request.app.userId, change=change, message=message)

        db.documents.update_one(
            {"id": doc["id"]},
            {
                "$set": {"updated_at": datetime.datetime.now()},
                "$push": {"logs": log.model_dump(), "flagged_pages": citation},
            },
        )

    return {"message": "Documents flagged"}


# Update a specific document by ID
@document_router.put("/{id}")
async def update_document(id: str, request: Request, db=Depends(get_db)):
    try:
        doc = db.documents.find_one({"id": id})

        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = Document(**doc)
        update_data = doc.model_dump()

        data = await request.json()
        for key, value in data.items():
            update_data[key] = value

        update_data["flagged_pages"] = []

        if update_data["type"] == "web":
            asyncio.create_task(remove_from_index(update_data["file"], search_client=request.app.search_client))
            logger.info("Getting content from url")
            update_data["file"] = get_filename_from_url(update_data["url"])
            update_data["file_pages"] = []
            asyncio.create_task(index_and_save_async(update_data, db, request.app.search_client))

        log = Log(change="updated", message="Document updated")

        update_data["logs"].append(log.model_dump())

        update_data["updated_at"] = datetime.datetime.now()

        del update_data["status"]

        db.documents.update_one({"id": id}, {"$set": update_data})

        return
    except Exception as ex:
        logger.error("Failed to update document")
        logger.error("Exception: {}".format(ex))
        raise HTTPException(status_code=500, detail="Failed to update document")


# Upload a file to blob storage and update document
@document_router.post("/{id}/file")
async def upload_file(
    id,
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    doc = db.documents.find_one({"id": id})

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.documents.update_one({"id": id}, {"$set": {"status": Status.processing.value}})

    if doc["file"]:
        asyncio.create_task(remove_from_index(doc["file"], search_client=request.app.search_client))

    asyncio.create_task(
        upload_file(
            id=id,
            doc=doc,
            request=request,
            file=file,
            db=db,
            blob_container_client=request.app.blob_container_client,
        ),
    )

    return {"success", True}


async def upload_file(
    id,
    doc,
    request,
    file,
    db,
    blob_container_client,
):
    try:
        if doc["file_pages"]:
            for page in doc["file_pages"]:
                try:
                    logger.info(f"Removing blob {page}")
                    blob_container_client.get_container_client(os.environ["AZURE_STORAGE_CONTAINER"]).delete_blob(page)
                except Exception as ex:
                    logger.info("Failed to remove blob from storage {}".format(ex))

        filename = file.filename
        pdf = file.read()
        file.close()
        file_pages = []

        # upload file to blob storage
        if os.path.splitext(filename)[1].lower() != ".pdf":
            raise HTTPException(status_code=500, detail="File is not a PDF")

        reader = PdfReader(io.BytesIO(pdf))
        pages = reader.pages
        for i in range(len(pages)):
            blob_name = blob_name_from_file_page(filename, i)
            f = io.BytesIO()
            writer = PdfWriter()
            writer.add_page(pages[i])
            writer.write(f)
            f.seek(0)

            blob_container_client.get_container_client(os.environ["AZURE_STORAGE_CONTAINER"]).upload_blob(
                blob_name, f, overwrite=True
            )

            file_pages.append(blob_name)

        # update document
        doc["file"] = filename
        doc["file_pages"] = file_pages
        doc["logs"].append(Log(user=request.app.userId, change="update_file", message="File updated"))
        doc = Document(**doc)
        del doc.status

        db.documents.update_one({"id": id}, {"$set": doc.model_dump()})

        # update index

        logger.info("Getting document text")

        page_map = get_document_text(pdf)

        logger.info("Got text. creating sections")

        sections = list(
            create_sections(
                filename,
                page_map,
            )
        )
        logger.info("Got sections. updating embeddings")

        sections = update_embeddings_in_batch(sections)

        logger.info("Updated embeddings. indexing sections")
        await index_sections(filename, sections, search_client=request.app.search_client)

        db.documents.update_one({"id": id}, {"$set": {"status": Status.done.value}})

        return doc
    except Exception as ex:
        logger.error("Failed to upload file")
        message = "Exception: {}".format(ex)
        logger.error(message)
        db.documents.update_one({"id": id}, {"$set": {"status": Status.error.value}})
        raise HTTPException(status_code=500, detail=message)


# Delete a specific document by ID
@document_router.delete("/{id}")
async def delete_document(id, request: Request, db=Depends(get_db)):
    try:
        if not id:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = db.documents.find_one({"id": id})

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info("Removing document from index: {}".format(doc["file"]))
        asyncio.create_task(remove_from_index(doc["file"], search_client=request.app.search_client))

        if doc["file_pages"]:
            for page in doc["file_pages"]:
                logger.info(f"Removing blob {page}")
                await request.app.blob_container_client.get_container_client(
                    os.environ["AZURE_STORAGE_CONTAINER"]
                ).delete_blob(page)

        log = Log(user=request.app.userId, change="deleted", message="Document deleted")

        db.documents.update_one({"id": id}, {"$set": {"deleted": True}, "$push": {"logs": log.model_dump()}})

        return {"message": "Document deleted"}
    except Exception as ex:
        logger.info("Failed to delete document")
        logger.info("Exception: {}".format(ex))
        raise HTTPException(status_code=500, detail="Failed to delete document")


# Add a log to a specific document by ID
@document_router.post("/{id}/logs")
async def add_log(id: str, request: Request, db=Depends(get_db)):
    data = await request.get_json()
    data["user"] = request.app.userId
    doc = db.documents.find_one({"id": id})
    if doc:
        log = Log(**data)
        db.documents.update_one({"id": id}, {"$push": {"logs": log}})
        return await log
    else:
        raise HTTPException(status_code=404, detail="Document not found")


# Change the status of a specific log in a specific document by ID and log ID
@document_router.post("/{id}/logs/{log_id}")
async def change_log_status(id: str, log_id, request: Request, db=Depends(get_db)):
    data = await request.get_json()
    data["user"] = request.app.userId
    doc = db.documents.find_one({"id": id})
    if doc:
        log = next((log for log in doc.logs if log.id == log_id), None)
        if log:
            log.status = data["status"]
            return await log.__dict__
        else:
            raise HTTPException(status_code=404, detail="Log not found")
    else:
        raise HTTPException(status_code=404, detail="Document not found")


# get list og files from blob storage
# @document_router.get("/files")
# async def get_files(request: Request):
#     blob_container_client = request.state.blob_container_client
#     blob_list = blob_container_client.get_container_client(os.environ["AZURE_STORAGE_CONTAINER"]).list_blobs()
#     # convert blob_list from AsyncItemPaged to list
#     blob_list = [blob async for blob in blob_list]
#     blob_names = []
#     for blob in blob_list:
#         blob_names.append(blob.name)
#     return {"files": blob_names}
