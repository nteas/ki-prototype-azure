import datetime
import logging
import os
from typing import List
from fastapi import APIRouter, Depends, Request
from bson import ObjectId

from core.db import get_db


class Log:
    def __init__(
        self,
        user: str = "admin",
        change: str = "created",
        _id: str = ObjectId(),
        message: str = None,
        created_at: str = datetime.datetime.now(),
    ):
        self.user = user
        self.change = change
        self._id = _id
        self.message = message
        self.created_at = created_at


class Document:
    def __init__(
        self,
        _id: ObjectId = None,
        title: str = None,
        owner: str = "admin",
        classification: str = "public",
        logs: List[Log] = [],
        frequency: str = "none",
        flagged: bool = False,
        type: str = "file",
        file: str = None,
        file_pages: [str] = [],
        url: str = None,
        created_at: str = datetime.datetime.now(),
        updated_at: str = datetime.datetime.now(),
        **kwargs,
    ):
        self._id = _id
        self.type = type
        self.owner = owner
        self.classification = classification
        self.file = file
        self.file_pages = file_pages
        self.url = url
        self.frequency = frequency
        self.flagged = flagged
        self.logs = logs
        self.created_at = created_at
        self.updated_at = updated_at

        if self.file is not None and title is None:
            self.title = os.path.basename(self.file)
        else:
            self.title = title

        # Handle unexpected keyword arguments
        self.extra_properties = {k: v for k, v in kwargs.items()}

    def to_dict(self):
        return {
            "type": self.type,
            "owner": self.owner,
            "classification": self.classification,
            "logs": self.logs,
            "frequency": self.frequency,
            "flagged": self.flagged,
            "file": self.file,
            "file_pages": self.file_pages,
            "url": self.url,
            "_id": str(self._id),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "title": self.title,
        }


document_router = APIRouter()


# Create a new document
@document_router.post("/")
def create_document(request: Request):
    data = request.json
    doc = Document(**data)
    documents.append(doc)
    return doc.__dict__


# Get all documents
@document_router.get("/")
async def get_documents(request: Request, db=Depends(get_db)):
    try:
        limit = int(request.get("limit", 10))
        skip = int(request.get("skip", 0))

        cursor = db.documents.find()
        total = db.documents.count_documents({})

        if limit:
            cursor = cursor.limit(limit)

        if skip > 0:
            cursor = cursor.skip(skip)

        if not cursor:
            raise Exception("No documents found")

        documents = [Document(**doc).to_dict() for doc in cursor]

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

    doc = db.documents.find_one({"_id": ObjectId(id)})

    if doc:
        return Document(**doc).to_dict()
    else:
        return {"error": "Document not found"}


# Update a specific document by ID
@document_router.post("/{id}")
def update_document(id, request: Request):
    data = request.json
    doc = next((doc for doc in documents if doc.id == id), None)
    if doc:
        for key, value in data.items():
            setattr(doc, key, value)
        return doc.__dict__
    else:
        return {"error": "Document not found"}


# Delete a specific document by ID
@document_router.post("/{id}")
def delete_document(id):
    global documents
    documents = [doc for doc in documents if doc.id != id]
    return {"message": "Document deleted"}


# Add a log to a specific document by ID
@document_router.post("/{id}/logs")
async def add_log(id, request: Request):
    data = await request.get_json()
    doc = next((doc for doc in documents if doc.id == id), None)
    if doc:
        log = Log(**data)
        doc.logs.append(log)
        return await log.__dict__
    else:
        return await {"error": "Document not found"}


# Change the status of a specific log in a specific document by ID and log ID
@document_router.post("/{id}/logs/{log_id}")
async def change_log_status(id, log_id, request: Request):
    data = await request.get_json()
    doc = next((doc for doc in documents if doc.id == id), None)
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

            doc.pop("_id", None)
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
