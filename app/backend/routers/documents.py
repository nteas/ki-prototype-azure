import copy
import time
import datetime
import os
import io
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from fastapi import HTTPException
from pypdf import PdfReader, PdfWriter


from core.types import Document, Log, Status
from core.logger import logger
from core.utilities import (
    remove_from_index,
    process_file,
    process_web,
    blob_name_from_file_page,
)


document_router = APIRouter()


# Create a new document
@document_router.post("/")
async def create_document(request: Request, background_tasks: BackgroundTasks):
    try:
        db = request.app.db
        data = await request.json()
        doc = Document(**data)

        doc.status = Status.processing.value
        db.documents.insert_one(doc.model_dump())

        if doc.type == "web":
            logger.info("-------------add job - process web-------------")
            background_tasks.add_task(process_web, doc.id, search_client=request.app.search_client)

        return doc.client_data()
    except Exception as ex:
        logger.info("Failed to create document")
        logger.exception("Exception: {}".format(ex))
        return {"error": "Exception: {}".format(ex)}


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
async def get_documents(request: Request, params: GetDocumentsRequest = Depends()):
    try:
        db = request.app.db
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

        documents = [Document(**doc).client_data() for doc in cursor]

        return {"documents": documents, "total": total}
    except Exception as ex:
        logger.error("Failed to get documents")
        logger.exception("Exception: {}".format(ex))
        raise HTTPException(status_code=404, detail="Document not found")


# Get a specific document by ID
@document_router.get("/{id}")
def get_document(id: str, request: Request):
    if not id:
        raise HTTPException(status_code=404, detail="Document not found")

    db = request.app.db
    doc = db.documents.find_one({"id": id})

    if doc:
        doc["logs"] = sorted(doc["logs"], key=lambda x: x["created_at"], reverse=True)

        return Document(**doc).client_data()
    else:
        raise HTTPException(status_code=404, detail="Document not found")


# Stream document status events
@document_router.get("/status/{id}")
async def get_document_status_events(id: str, request: Request):
    if not id:
        raise HTTPException(status_code=404, detail="No id provided")

    db = request.app.db

    def event_generator():
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
            time.sleep(5)

    return EventSourceResponse(event_generator())


# Check if document is flagged based on citation / file_page
@document_router.get("/flag/")
def get_document(
    request: Request, citation: str = Query(None, description="Citation to check if flagged", example="123")
):
    if not citation:
        raise HTTPException(status_code=404, detail="Document not found")

    db = request.app.db
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
def flag_document(request: Request, data: FlagCitations):
    if not data.citations:
        raise HTTPException(status_code=404, detail="No citations supplied")

    db = request.app.db
    for citation in data.citations:
        doc = db.documents.find_one(
            {"deleted": {"$ne": True}, "$or": [{"file": citation}, {"file_pages": citation}, {"urls.url": citation}]}
        )

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
async def update_document(id: str, request: Request, background_tasks: BackgroundTasks):
    try:
        db = request.app.db
        doc = db.documents.find_one({"id": id})

        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = Document(**doc)
        update_data = doc.model_dump()

        stored_urls = copy.copy(update_data["urls"])
        logger.info("Stored urls: {}".format(stored_urls))

        stored_urls = [url["url"] for url in stored_urls]

        data = await request.json()
        for key, value in data.items():
            update_data[key] = value

        update_data["flagged_pages"] = []

        if update_data["type"] == "web":
            update_data["file"] = ""
            update_data["file_pages"] = []

            should_reindex = False
            for index, url in enumerate(data["urls"]):
                if url != stored_urls[index]:
                    should_reindex = True
                    break

            if should_reindex:
                logger.info("-------------add job - process web-------------")
                background_tasks.add_task(process_web, id, search_client=request.app.search_client)

        log = Log(change="updated", message="Document updated")

        update_data["logs"].append(log.model_dump())

        update_data["updated_at"] = datetime.datetime.now()

        if doc.file != update_data["file"] or should_reindex:
            update_data["status"] = Status.processing.value

        db.documents.update_one({"id": id}, {"$set": Document(**update_data).model_dump()})

        return {"message": "Document updated"}
    except Exception as ex:
        logger.error("Failed to update document")
        logger.exception("Exception: {}".format(ex))
        db.documents.update_one({"id": id}, {"$set": {"status": Status.error.value}})
        raise HTTPException(status_code=500, detail="Failed to update document")


# Upload a file to blob storage and update document
@document_router.post("/{id}/file")
async def upload_file(
    id,
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    db = request.app.db

    try:
        logger.info("Begin upload file")

        doc = db.documents.find_one({"id": id})

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        db.documents.update_one({"id": id}, {"$set": {"status": Status.processing.value}})

        filename = file.filename
        pdf = await file.read()
        await file.close()
        file_pages = []
        blobs = []
        logger.info("File read")

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
            blobs.append({"blob_name": blob_name, "blob": f})
            file_pages.append(blob_name)

        logger.info("-------------add job - upload blobs-------------")
        background_tasks.add_task(upload_blobs, blobs, blob_container_client=request.app.blob_container_client)

        logger.info("-------------add job - process file-------------")
        file_data = {"filename": filename, "file_pages": file_pages, "pdf": pdf}
        background_tasks.add_task(
            process_file,
            id,
            file_data,
            search_client=request.app.search_client,
            blob_container_client=request.app.blob_container_client,
        )

        return {"success", True}
    except Exception as ex:
        logger.error("Failed to upload file")
        message = "Exception: {}".format(ex)
        logger.exception(message)
        db.documents.update_one({"id": id}, {"$set": {"status": Status.error.value}})
        raise HTTPException(status_code=500, detail=message)


def upload_blobs(blobs, blob_container_client):
    for blob in blobs:
        blob_container_client.upload_blob(name=blob["blob_name"], data=blob["blob"])


# Delete a specific document by ID
@document_router.delete("/{id}")
async def delete_document(id, request: Request, background_tasks: BackgroundTasks):
    try:
        if not id:
            raise HTTPException(status_code=404, detail="Document not found")

        db = request.app.db
        doc = db.documents.find_one({"id": id})
        doc = Document(**doc)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info("-------------add job - remove from index-------------")
        background_tasks.add_task(remove_all_from_index, doc.file, search_client=request.app.search_client)

        if doc.file_pages:
            request.app.blob_container_client.delete_blobs(*doc.file_pages)

        log = Log(user=request.app.userId, change="deleted", message="Document deleted")

        db.documents.update_one({"id": id}, {"$set": {"deleted": True}, "$push": {"logs": log.model_dump()}})

        return {"message": "Document deleted"}
    except Exception as ex:
        logger.info("Failed to delete document")
        logger.exception("Exception: {}".format(ex))
        raise HTTPException(status_code=500, detail="Failed to delete document")


def remove_all_from_index(pages, search_client):
    for page in pages:
        remove_from_index(page, search_client)


# Add a log to a specific document by ID
@document_router.post("/{id}/logs")
async def add_log(id: str, request: Request):
    db = request.app.db
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
async def change_log_status(id: str, log_id, request: Request):
    data = await request.get_json()
    data["user"] = request.app.userId
    db = request.app.db
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
