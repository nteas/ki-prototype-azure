from typing import List
from quart import (
    Blueprint,
    current_app,
    request,
    jsonify,
)


class Log:
    def __init__(self, id: str, created_at: str, user: str, change: str, status: str, message: str = None):
        self.id = id
        self.created_at = created_at
        self.user = user
        self.change = change
        self.message = message
        self.status = status


class Document:
    def __init__(
        self,
        type: str,
        title: str,
        name: str,
        owner: str,
        classification: str,
        updated: str,
        frequency: str,
        id: str,
        flagged: bool,
        logs: List[Log],
        file: str = None,
        url: str = None,
    ):
        self.type = type
        self.title = title
        self.name = name
        self.owner = owner
        self.classification = classification
        self.updated = updated
        self.file = file
        self.url = url
        self.frequency = frequency
        self.id = id
        self.flagged = flagged
        self.logs = logs


document_router = Blueprint("documents", __name__, url_prefix="/documents")

# In-memory storage for documents
documents = []


# Create a new document
@document_router.route("/documents", methods=["POST"])
def create_document():
    data = request.json
    doc = Document(**data)
    documents.append(doc)
    return jsonify(doc.__dict__)


# Get all documents
@document_router.route("/documents", methods=["GET"])
def get_documents():
    return jsonify([doc.__dict__ for doc in documents])


# Get a specific document by ID
@document_router.route("/documents/<id>", methods=["GET"])
def get_document(id):
    doc = next((doc for doc in documents if doc.id == id), None)
    if doc:
        return jsonify(doc.__dict__)
    else:
        return jsonify({"error": "Document not found"})


# Update a specific document by ID
@document_router.route("/documents/<id>", methods=["PUT"])
def update_document(id):
    data = request.json
    doc = next((doc for doc in documents if doc.id == id), None)
    if doc:
        for key, value in data.items():
            setattr(doc, key, value)
        return jsonify(doc.__dict__)
    else:
        return jsonify({"error": "Document not found"})


# Delete a specific document by ID
@document_router.route("/documents/<id>", methods=["DELETE"])
def delete_document(id):
    global documents
    documents = [doc for doc in documents if doc.id != id]
    return jsonify({"message": "Document deleted"})


# Add a log to a specific document by ID
@document_router.route("/documents/<id>/logs", methods=["POST"])
async def add_log(id):
    data = await request.get_json()
    doc = next((doc for doc in documents if doc.id == id), None)
    if doc:
        log = Log(**data)
        doc.logs.append(log)
        return await jsonify(log.__dict__)
    else:
        return await jsonify({"error": "Document not found"})


# Change the status of a specific log in a specific document by ID and log ID
@document_router.route("/documents/<id>/logs/<log_id>", methods=["PUT"])
async def change_log_status(id, log_id):
    data = await request.get_json()
    doc = next((doc for doc in documents if doc.id == id), None)
    if doc:
        log = next((log for log in doc.logs if log.id == log_id), None)
        if log:
            log.status = data["status"]
            return await jsonify(log.__dict__)
        else:
            return await jsonify({"error": "Log not found"})
    else:
        return await jsonify({"error": "Document not found"})


# get list og files from blob storage
@document_router.route("/files", methods=["GET"])
async def get_files():
    from app import CONFIG_BLOB_CONTAINER_CLIENT

    blob_container_client = current_app.config[CONFIG_BLOB_CONTAINER_CLIENT]
    blob_list = blob_container_client.list_blobs()
    # convert blob_list from AsyncItemPaged to list
    blob_list = [blob async for blob in blob_list]

    blob_names = []
    for blob in blob_list:
        blob_names.append(blob.name)
    return {"files": blob_names}


# search for file name in cognitive search
@document_router.route("/search", methods=["GET"])
async def search():
    from app import CONFIG_SEARCH_CLIENT

    search_client = current_app.config[CONFIG_SEARCH_CLIENT]
    search_term = request.args.get("q")
    search_results = await search_client.search(search_text=search_term, include_total_count=True)
    search_results = [result async for result in search_results]
    return {"results": search_results}
