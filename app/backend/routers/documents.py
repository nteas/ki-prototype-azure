import datetime
import logging
import os
import io
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel, Field
from pypdf import PdfReader, PdfWriter

from core.db import get_db
from core.context import get_blob_container_client
from core.utilities import (
    blob_name_from_file_page,
    get_document_text,
    remove_from_index,
    update_embeddings_in_batch,
    create_sections,
    index_sections,
)


class Log(BaseModel):
    user: str = Field(default="admin")
    change: str = "created"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(default=None)
    owner: str = Field(default="admin")
    classification: str = Field(default="public")
    logs: List[Log] = Field(default=[])
    frequency: Optional[str] = Field(default="none")
    flagged_pages: List[str] = Field(default=[])
    type: str = Field(default="pdf")
    file: Optional[str] = Field(default=None)
    file_pages: List[str] = Field(default=[])
    url: Optional[str] = Field(default=None)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    def __init__(self, **data):
        data.pop("_id", None)  # Remove _id from the data if it exists
        if data.get("title") is None and data.get("file") is not None:
            data["title"] = os.path.basename(data["file"])

        super().__init__(**data)

    class Config:
        extra = "allow"


document_router = APIRouter()


# Create a new document
@document_router.post("/")
def create_document(doc: Document, db=Depends(get_db)):
    try:
        db.documents.insert_one(doc.model_dump())

        return doc
    except Exception as ex:
        logging.info("Failed to create document")
        logging.info("Exception: {}".format(ex))
        return {"error": "Exception: {}".format(ex)}


# typing for get all documents request
class GetDocumentsRequest(BaseModel):
    limit: int = 10
    skip: int = 0
    search: str = ""
    flagged: str = "false"
    pdf: str = "true"
    web: str = "true"
    order_by: str = "created_at"
    order: int = -1


# Get all documents
@document_router.get("/")
async def get_documents(params: GetDocumentsRequest = Depends(), db=Depends(get_db)):
    try:
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
            cursor = cursor.sort(params.order_by, params.order)

        if not cursor:
            raise Exception("No documents found")

        documents = [Document(**doc) for doc in cursor]

        return {"documents": documents, "total": total}
    except Exception as ex:
        logging.info("Failed to get documents")
        logging.info("Exception: {}".format(ex))
        raise HTTPException(status_code=404, detail="Document not found")


# Get a specific document by ID
@document_router.get("/{id}")
def get_document(id, db=Depends(get_db)):
    if not id:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = db.documents.find_one({"id": id})

    if doc:
        doc["logs"] = sorted(doc["logs"], key=lambda x: x["created_at"], reverse=True)

        return Document(**doc)
    else:
        raise HTTPException(status_code=404, detail="Document not found")


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
        doc = db.documents.find_one({"file_pages": citation})

        if doc:
            change = "flagged"
            message = data.message + ": " + citation
            log = Log(user=request.state.userId, change=change, message=message)

            db.documents.update_one({"id": doc["id"]}, {"$push": {"logs": log.model_dump(), "flagged_pages": citation}})
        else:
            logging.info("Document not found")

    return {"message": "Documents flagged"}


# Update a specific document by ID
@document_router.put("/{id}")
async def update_document(id, request: Request, db=Depends(get_db)):
    # get request body
    data = await request.json()

    doc = db.documents.find_one({"id": id})

    if doc:
        doc = Document(**doc)
        update_data = doc.model_dump()

        for key, value in data.items():
            update_data[key] = value

        update_data["flagged_pages"] = []

        log = Log(change="updated", message="Document updated")

        update_data["logs"].append(log.model_dump())

        db.documents.update_one({"id": id}, {"$set": update_data})

        return
    else:
        raise HTTPException(status_code=404, detail="Document not found")


# Upload a file to blob storage and update document
@document_router.post("/{id}/file")
async def upload_file(
    id,
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db),
    blob_container_client=Depends(get_blob_container_client),
):
    try:
        doc = db.documents.find_one({"id": id})

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if doc["file_pages"]:
            try:
                await remove_from_index(doc["file"])
            except Exception as ex:
                logging.info("Failed to remove from index {}".format(ex))

            for page in doc["file_pages"]:
                try:
                    logging.info(f"Removing blob {page}")
                    await blob_container_client.get_container_client(os.environ["AZURE_STORAGE_CONTAINER"]).delete_blob(
                        page
                    )
                except Exception as ex:
                    logging.info("Failed to remove blob from storage {}".format(ex))

        filename = file.filename
        pdf = await file.read()
        await file.close()
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

            await blob_container_client.get_container_client(os.environ["AZURE_STORAGE_CONTAINER"]).upload_blob(
                blob_name, f, overwrite=True
            )

            file_pages.append(blob_name)

        # update document
        doc["file"] = filename
        doc["file_pages"] = file_pages
        doc["logs"].append(Log(user=request.state.userId, change="update_file", message="File updated"))
        doc = Document(**doc)

        db.documents.update_one({"id": id}, {"$set": doc.model_dump()})

        # update index

        logging.info("Getting document text")

        page_map = get_document_text(pdf, azure_credentials)

        logging.info("Got text. creating sections")

        sections = list(
            create_sections(
                filename,
                page_map,
                os.environ["AZURE_OPENAI_EMB_DEPLOYMENT"],
                os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-ada-002"),
            )
        )
        logging.info("Got sections. updating embeddings")

        sections = update_embeddings_in_batch(sections)

        logging.info("Updated embeddings. indexing sections")
        await index_sections(filename, sections, azure_credentials)

        logging.info("Indexed sections")

        return doc
    except Exception as ex:
        logging.info("Failed to upload file")
        message = "Exception: {}".format(ex)
        logging.info(message)
        raise HTTPException(status_code=500, detail=message)

    finally:
        await blob_container_client.close()


# Delete a specific document by ID
@document_router.delete("/{id}")
async def delete_document(
    id, request: Request, db=Depends(get_db), blob_container_client=Depends(get_blob_container_client)
):
    try:
        if not id:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = db.documents.find_one({"id": id})

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        logging.info("Removing document from index: {}".format(doc["file"]))

        if doc["file_pages"]:
            try:
                await remove_from_index(doc["file"])
            except Exception as ex:
                logging.info("Failed to remove from index {}".format(ex))

            for page in doc["file_pages"]:
                try:
                    logging.info(f"Removing blob {page}")
                    await blob_container_client.get_container_client(os.environ["AZURE_STORAGE_CONTAINER"]).delete_blob(
                        page
                    )
                except Exception as ex:
                    logging.info("Failed to remove blob from storage {}".format(ex))

        log = Log(user=request.state.userId, change="deleted", message="Document deleted")

        db.documents.update_one({"id": id}, {"$set": {"deleted": True}, "$push": {"logs": log.model_dump()}})

        return {"message": "Document deleted"}
    except Exception as ex:
        logging.info("Failed to delete document")
        logging.info("Exception: {}".format(ex))
        raise HTTPException(status_code=500, detail="Failed to delete document")
    finally:
        await blob_container_client.close()


# Add a log to a specific document by ID
@document_router.post("/{id}/logs")
async def add_log(id, request: Request, db=Depends(get_db)):
    data = await request.get_json()
    data["user"] = request.state.userId
    doc = db.documents.find_one({"id": id})
    if doc:
        log = Log(**data)
        db.documents.update_one({"id": id}, {"$push": {"logs": log}})
        return await log
    else:
        raise HTTPException(status_code=404, detail="Document not found")


# Change the status of a specific log in a specific document by ID and log ID
@document_router.post("/{id}/logs/{log_id}")
async def change_log_status(id, log_id, request: Request, db=Depends(get_db)):
    data = await request.get_json()
    data["user"] = request.state.userId
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
