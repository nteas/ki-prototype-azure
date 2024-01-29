import io
import mimetypes
import os
from fastapi import FastAPI, APIRouter, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, FileResponse, JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler

from routers.documents import document_router
from core.db import close_db_connect, connect_and_init_db, get_db
from core.logger import logger
from core.openai_agent import get_engine, index_web_documents
from worker import worker

env = os.getenv("AZURE_ENV_NAME", "dev")
app = FastAPI(debug=env == "dev")
app.mount("/assets", StaticFiles(directory="static/assets", html=True), name="assets")


# Set up worker
worker_cron = BackgroundScheduler()


def migrate_data():
    db = get_db()

    docs = db.documents.find({"type": "web", "deleted": {"$ne": True}})

    if docs is None:
        print("No daily documents found")
        return

    docs = list(docs)

    for doc in docs:
        urls = doc.get("urls")

        if urls is None:
            continue

        updated_urls = []
        for url in urls:
            updated_urls.append(url["url"])

        db.documents.update_one({"id": doc["id"]}, {"$set": {"urls": updated_urls}})

    logger.info(f"Migrated {len(docs)} documents")
    logger.info("Done migrating data")


@app.on_event("startup")
def startup_event():
    logger.info("Starting the api")
    app.db = connect_and_init_db()

    # index_web_documents()
    # migrate_data()

    if os.getenv("AZURE_ENVIRONMENT", "production") != "development":
        logger.info("Starting the worker")
        worker_cron.add_job(worker, "cron", hour=4)
        worker_cron.start()


@app.on_event("shutdown")
def shutdown_event():
    close_db_connect()

    if worker_cron.running:
        worker_cron.shutdown()

    logger.info("Shutting down the api and worker")


root_router = APIRouter()


@root_router.get("/redirect")
async def redirect():
    return ""


@root_router.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")


@root_router.get("/")
@root_router.get("/{path:path}")
async def index(path: str = ""):
    return FileResponse("static/index.html")


api_router = APIRouter()


# # Serve content files from blob storage from within the app to keep the example self-contained.
# # *** NOTE *** this assumes that the content files are public, or at least that all users of the app
# # can access all the files. This is also slow and memory hungry.
@api_router.get("/content/{path}")
async def content_file(path, request: Request):
    try:
        blob = request.app.blob_container_client.get_blob_client(path).download_blob()
        if not blob.properties or not blob.properties.has_key("content_settings"):
            return {"error": "Blob not found"}, 404
        mime_type = blob.properties["content_settings"]["content_type"]
        if mime_type == "application/octet-stream":
            mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        blob_file = io.BytesIO()
        await blob.readinto(blob_file)
        blob_file.seek(0)
        return StreamingResponse(blob_file, media_type=mime_type)
    except Exception as e:
        logger.exception("Exception in /content")
        return {"error": str(e)}, 500


@api_router.post("/chat_stream")
async def chat_stream(request: Request):
    try:
        request_json = await request.json()

        chat_engine = get_engine()

        streaming_response = chat_engine.query(request_json["question"])

        def generator():
            for text in streaming_response.response_gen:
                logger.info(f"Response: {text}")
                yield text

        return StreamingResponse(generator(), media_type="text/plain")
    except Exception as e:
        logger.exception("Exception in /chat")
        return {"error": str(e)}, 500


@app.middleware("http")
async def before_request(request: Request, call_next):
    try:
        app.userId = request.headers.get("userId")

        response = await call_next(request)

        return response
    except Exception as e:
        logger.exception("Exception in before_request")
        return JSONResponse(content={"error": str(e)}, status_code=500)


app.include_router(api_router, prefix="/api")
app.include_router(document_router, prefix="/api/documents")
app.include_router(root_router)

if allowed_origin := os.getenv("ALLOWED_ORIGIN"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[allowed_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS enabled for %s", allowed_origin)
