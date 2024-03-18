from typing import Optional
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)
from fastapi import HTTPException
from pydantic import BaseModel

from core.openai_agent import get_pinecone_index
from core.logger import logger


files_router = APIRouter()


# Get all documents
@files_router.get("/")
async def get_documents():
    try:
        pinecone_index = get_pinecone_index()

        matches = pinecone_index.query(
            vector=[0.0] * 1536,  # [0.0, 0.0, 0.0, 0.0, 0.0
            top_k=1000,
            filter={"ref_id": "sharepoint"},
            include_metadata=True,
        )

        files = []
        unique_files = set()
        for match in matches["matches"]:
            if match.metadata["url"] not in unique_files:
                unique_files.add(match.metadata["url"])
                files.append(
                    {
                        "title": match.metadata["title"],
                        "url": match.metadata["url"],
                        "flagged": match.metadata.get("flagged", False),
                    }
                )

        # sort by title
        files = sorted(files, key=lambda x: x["title"])

        return {"files": files}
    except Exception as e:
        logger.exception("Exception in /file-index")
        return HTTPException(status_code=500, detail=str(e))


# Check if document is flagged based on citation / file_page
@files_router.get("/flag/")
def get_document(request: Request):
    url = request.query_params.get("url")

    if not url:
        return {"error": "url is required"}, 400

    pinecone_index = get_pinecone_index()

    url = url.replace(" ", "%20")

    matches = pinecone_index.query(
        vector=[0.0] * 1536,  # [0.0, 0.0, 0.0, 0.0, 0.0
        top_k=1000,
        filter={"ref_id": "sharepoint", "url": url, "flagged": True},
    )

    print(matches["matches"])

    if matches["matches"]:
        return {"flagged": True}
    else:
        return {"flagged": False}


class Item(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None


# Flag a specific document by citation / file_page
@files_router.post("/flag")
def flag_document(item: Item):
    if not item.url:
        return {"error": "url is required"}, 400

    pinecone_index = get_pinecone_index()

    url = item.url.replace(" ", "%20")

    matches = pinecone_index.query(
        vector=[0.0] * 1536,  # [0.0, 0.0, 0.0, 0.0, 0.0
        top_k=1000,
        filter={
            "ref_id": "sharepoint",
            "url": url,
        },
    )

    for match in matches["matches"]:
        pinecone_index.update(
            id=match.id,
            set_metadata={"flagged": True},
        )

    return {"message": "Documents flagged"}


@files_router.post("/unflag")
def unflag_document(item: Item):
    pinecone_index = get_pinecone_index()

    title = item.title

    if not title:
        return {"error": "title is required"}, 400

    matches = pinecone_index.query(
        vector=[0.0] * 1536,  # [0.0, 0.0, 0.0, 0.0, 0.0
        top_k=1000,
        filter={
            "ref_id": "sharepoint",
            "title": title,
        },
    )

    for match in matches["matches"]:
        pinecone_index.update(
            id=match.id,
            set_metadata={"flagged": False},
        )

    return {"message": "Documents unflagged"}
