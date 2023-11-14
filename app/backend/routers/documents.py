import datetime
import logging
import os
import io
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel, Field
from pypdf import PdfReader, PdfWriter
from azure.identity import AzureDeveloperCliCredential

from core.db import get_db
from core.context import get_azure_credential, get_blob_container_client
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
        super().__init__(**data)
        self._title = self.title

    class Config:
        extra = "allow"

    @property
    def title(self):
        if hasattr(self, "_title"):
            if self.file is not None and self._title is None:
                return os.path.basename(self.file)
            else:
                return self._title
        else:
            return None


document_router = APIRouter()


# Create a new document
@document_router.post("/")
def create_document(doc: Document, db=Depends(get_db)):
    try:
        db.documents.insert_one(doc.model_dump())

        return doc
    except Exception as ex:
        print("Failed to create document")
        print("Exception: {}".format(ex))
        return {"error": "Exception: {}".format(ex)}


# typing for get all documents request
class GetDocumentsRequest(BaseModel):
    limit: int = 10
    skip: int = 0
    search: str = ""
    flagged: str = "false"
    pdf: str = "true"
    web: str = "true"


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

        if not cursor:
            raise Exception("No documents found")

        documents = [Document(**doc) for doc in cursor]

        return {"documents": documents, "total": total}
    except Exception as ex:
        print("Failed to get documents")
        print("Exception: {}".format(ex))
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

        azure_credentials = get_azure_credential()

        if doc["file_pages"]:
            try:
                prefix = os.path.splitext(doc["file"])[0]
                blobs = blob_container_client.list_blob_names(name_starts_with=prefix)
                for b in blobs:
                    print(f"\tRemoving blob {b}")
                    await blob_container_client.delete_blob(b)
                for page in doc["file_pages"]:
                    logging.info("Removing page from index: {}".format(page))
                    remove_from_index(page, azure_credentials)
            except Exception as ex:
                print("Failed to remove pages from index")

        filename = file.filename
        pdf = await file.read()
        file_pages = []

        # upload file to blob storage
        if os.path.splitext(filename)[1].lower() == ".pdf":
            reader = PdfReader(io.BytesIO(pdf))
            pages = reader.pages
            for i in range(len(pages)):
                blob_name = blob_name_from_file_page(filename, i)
                f = io.BytesIO()
                writer = PdfWriter()
                writer.add_page(pages[i])
                writer.write(f)
                f.seek(0)

                await blob_container_client.upload_blob(blob_name, f, overwrite=True)

                file_pages.append(blob_name)
        else:
            blob_name = blob_name_from_file_page(filename)

            blob_container_client.upload_blob(blob_name, pdf, overwrite=True)

        # update document
        doc["file"] = filename
        doc["file_pages"] = file_pages
        doc["logs"].append(Log(user=request.state.userId, change="update_file", message="File updated"))
        doc = Document(**doc)

        db.documents.update_one({"id": id}, {"$set": doc.model_dump()})

        # update index
        file_bytes = await file.read()

        print("Getting document text")

        AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
        formrecognizer_creds = AzureDeveloperCliCredential(tenant_id=AZURE_TENANT_ID, process_timeout=60)
        page_map = get_document_text(file_bytes, formrecognizer_creds)

        print("Got text. creating sections")

        sections = create_sections(
            os.path.basename(filename),
            page_map,
            True,
            True,
            os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-ada-002"),
        )
        print("Got sections. updating embeddings")

        sections = update_embeddings_in_batch(sections)

        print("Updated embeddings. indexing sections")
        index_sections(os.path.basename(filename), sections)

        print("Indexed sections")

        return doc
    except Exception as ex:
        print("Failed to upload file")
        print("Exception: {}".format(ex))
        raise HTTPException(status_code=500, detail="Failed to upload file")


# Delete a specific document by ID
@document_router.delete("/{id}")
async def delete_document(
    id, request: Request, db=Depends(get_db), blob_container_client=Depends(get_blob_container_client)
):
    if not id:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = db.documents.find_one({"id": id})

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        azure_credentials = get_azure_credential()

        if doc["file_pages"]:
            try:
                prefix = os.path.splitext(doc["file"])[0]
                blobs = blob_container_client.list_blob_names(name_starts_with=prefix)
                for b in blobs:
                    print(f"\tRemoving blob {b}")
                    await blob_container_client.delete_blob(b)
                for page in doc["file_pages"]:
                    logging.info("Removing page from index: {}".format(page))
                    remove_from_index(page, azure_credentials)
            except Exception as ex:
                print("Failed to remove pages from index")

        if doc["file"]:
            blob_container_client.delete_blob(doc["file"])
    except Exception as ex:
        print("Failed to delete file on azure blob storage and search index")
        print("Exception: {}".format(ex))

    log = Log(user=request.state.userId, change="deleted", message="Document deleted")

    db.documents.update_one({"id": id}, {"$set": {"deleted": True}, "$push": {"logs": log.model_dump()}})

    return {"message": "Document deleted"}


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
@document_router.get("/files")
async def get_files(request: Request):
    blob_container_client = request.state.blob_container_client
    blob_list = blob_container_client.list_blobs()
    # convert blob_list from AsyncItemPaged to list
    blob_list = [blob async for blob in blob_list]
    blob_names = []
    for blob in blob_list:
        blob_names.append(blob.name)
    return {"files": blob_names}


# migrate files in cognitive search to own database
@document_router.get("/migrate")
async def search(request: Request, db=Depends(get_db)):
    try:
        search_client = request.state.search_client
        search_results = await search_client.search(search_text="", select=["id", "sourcepage", "sourcefile"])

        # Iterate over the search results using the get_next method
        docs = []
        async for result in search_results:
            docs.append(result)
            doc = Document(file=result.get("sourcefile")).to_dict()

            doc.pop("id", None)
            doc.pop("file_pages", None)

            db.documents.update_one(
                {"file": result.get("sourcefile")},
                {
                    "$setOnInsert": doc,
                    "$addToSet": {"file_pages": result.get("sourcepage")},
                },
                upsert=True,
            )

        return {"success": True}
    except Exception as ex:
        print("Failed to migrate documents")
        print("Exception: {}".format(ex))
        return {"success": False}
