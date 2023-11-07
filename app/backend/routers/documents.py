import datetime
import logging
import os
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from core.db import get_db


class Log(BaseModel):
    user: str = Field(default="admin")
    change: str = "created"
    id: str = Field(default_factory=uuid.uuid4)
    message: str = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class Document(BaseModel):
    id: str = Field(default_factory=uuid.uuid4)
    title: Optional[str] = Field(default=None)
    owner: str = Field(default="admin")
    classification: str = Field(default="public")
    logs: List[Log] = Field(default=[])
    frequency: str = Field(default="none")
    flagged: bool = Field(default=False)
    type: str = Field(default="pdf")
    file: Optional[str] = Field(default=None)
    file_pages: List[str] = Field(default=[])
    url: Optional[str] = Field(default=None)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    def __init__(self, **data):
        data.pop("_id", None)  # Remove _id from the data if it exists
        super().__init__(**data)

    class Config:
        extra = "allow"

    @property
    def title(self):
        if self.file is not None and self.title is None:
            return os.path.basename(self.file)
        else:
            return self.title


document_router = APIRouter()


# Create a new document
@document_router.post("/")
def create_document(doc: Document, db=Depends(get_db)):
    try:
        db.documents.insert_one(doc)

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
            query["flagged"] = True

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
        return {"error": "Exception: {}".format(ex)}


# Get a specific document by ID
@document_router.get("/{id}")
def get_document(id, db=Depends(get_db)):
    if not id:
        return {"error": "Document not found"}

    doc = db.documents.find_one({"id": id})

    if doc:
        return Document(**doc)
    else:
        return {"error": "Document not found"}


# Update a specific document by ID
@document_router.post("/{id}")
def update_document(id, request: Request, db=Depends(get_db)):
    doc = db.documents.find_one({"id": id})

    data = request.json()

    if doc:
        for key, value in data.items():
            setattr(doc, key, value)
        return doc
    else:
        return {"error": "Document not found"}


# Delete a specific document by ID
@document_router.delete("/{id}")
def delete_document(id, db=Depends(get_db)):
    if not id:
        return {"error": "Document not found"}

    db.documents.updateOne({"id": id, "$set": {"deleted": True}})

    return {"message": "Document deleted"}


# Add a log to a specific document by ID
@document_router.post("/{id}/logs")
async def add_log(id, request: Request, db=Depends(get_db)):
    data = await request.get_json()
    doc = db.documents.find_one({"id": id})
    if doc:
        log = Log(**data)
        db.documents.update_one({"id": id}, {"$push": {"logs": log}})
        return await log
    else:
        return await {"error": "Document not found"}


# Change the status of a specific log in a specific document by ID and log ID
@document_router.post("/{id}/logs/{log_id}")
async def change_log_status(id, log_id, request: Request, db=Depends(get_db)):
    data = await request.get_json()
    doc = db.documents.find_one({"id": id})
    if doc:
        log = next((log for log in doc.logs if log.id == log_id), None)
        if log:
            log.status = data["status"]
            return await log.__dict__
        else:
            return await {"error": "Log not found"}
    else:
        return await {"error": "Document not found"}


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
        search_term = request.args.get("q", "")
        search_results = await search_client.search(search_text=search_term, select=["id", "sourcepage", "sourcefile"])

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
