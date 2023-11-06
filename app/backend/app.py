import io
import json
import logging
import mimetypes
import os
from typing import AsyncGenerator
import aiohttp
import openai
from fastapi import Depends, FastAPI, APIRouter, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, FileResponse, JSONResponse

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.retrievethenread import RetrieveThenReadApproach
from routers.documents import document_router
from core.db import close_db_connect, connect_and_init_db
from core.context import get_auth_helper, get_azure_credential, get_blob_container_client, get_search_client


# Replace these with your own values, either in environment variables or directly here
OPENAI_HOST = os.getenv("OPENAI_HOST", "azure")
OPENAI_CHATGPT_MODEL = os.environ["AZURE_OPENAI_CHATGPT_MODEL"]
OPENAI_EMB_MODEL = os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-ada-002")
# Used with Azure OpenAI deployments
AZURE_OPENAI_SERVICE = os.environ["AZURE_OPENAI_SERVICE"]
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.environ["AZURE_OPENAI_CHATGPT_DEPLOYMENT"]
AZURE_OPENAI_EMB_DEPLOYMENT = os.environ["AZURE_OPENAI_EMB_DEPLOYMENT"]
# Used only with non-Azure OpenAI deployments
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_ORGANIZATION = os.environ["OPENAI_ORGANIZATION"]
KB_FIELDS_CONTENT = os.getenv("KB_FIELDS_CONTENT", "content")
KB_FIELDS_SOURCEPAGE = os.getenv("KB_FIELDS_SOURCEPAGE", "sourcepage")

env = os.getenv("AZURE_ENV_NAME", "dev")
app = FastAPI(debug=env == "dev")
app.mount("/assets", StaticFiles(directory="static/assets", html=True), name="assets")


@app.on_event("startup")
def startup_event():
    logging.info("Starting up...")
    connect_and_init_db()


@app.on_event("shutdown")
def shutdown_event():
    logging.info("Shutting down...")
    close_db_connect()


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
async def content_file(path, blob_container_client=Depends(get_blob_container_client)):
    blob = await blob_container_client.get_blob_client(path).download_blob()
    if not blob.properties or not blob.properties.has_key("content_settings"):
        return {"error": "Blob not found"}, 404
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    blob_file = io.BytesIO()
    await blob.readinto(blob_file)
    blob_file.seek(0)
    return StreamingResponse(blob_file, media_type=mime_type)


# Send MSAL.js settings to the client UI
@api_router.get("/auth_setup")
def auth_setup(auth_helper=Depends(get_auth_helper)):
    return auth_helper.get_auth_setup_for_client()


@api_router.post("/ask")
async def ask(request: Request, search_client=Depends(get_search_client)):
    try:
        if request.headers.get("Content-Type") != "application/json":
            raise HTTPException(status_code=415, detail="Request must be JSON")

        request_json = await request.json()
        auth_helper = get_auth_helper()
        auth_claims = await auth_helper.get_auth_claims_if_enabled({"Authorization": f"Bearer {openai.api_key}"})

        impl = RetrieveThenReadApproach(
            search_client,
            OPENAI_HOST,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            OPENAI_CHATGPT_MODEL,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            OPENAI_EMB_MODEL,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT,
        )
        # Workaround for: https://github.com/openai/openai-python/issues/371
        async with aiohttp.ClientSession() as s:
            openai.aiosession.set(s)
            r = await impl.run(request_json["question"], request_json.get("overrides") or {}, auth_claims)
        return r
    except Exception as e:
        logging.exception("Exception in /ask")
        return {"error": str(e)}, 500


@api_router.post("/chat")
async def chat(request: Request, search_client=Depends(get_search_client)):
    try:
        if request.headers.get("Content-Type") != "application/json":
            raise HTTPException(status_code=415, detail="Request must be JSON")

        auth_helper = get_auth_helper()
        auth_claims = await auth_helper.get_auth_claims_if_enabled(request.headers)

        request_json = await request.json()

        impl = ChatReadRetrieveReadApproach(
            search_client,
            OPENAI_HOST,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            OPENAI_CHATGPT_MODEL,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            OPENAI_EMB_MODEL,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT,
        )
        # Workaround for: https://github.com/openai/openai-python/issues/371
        async with aiohttp.ClientSession() as s:
            openai.aiosession.set(s)
            r = await impl.run_without_streaming(
                request_json["history"], request_json.get("overrides", {}), auth_claims
            )
        return r
    except Exception as e:
        logging.exception("Exception in /chat")
        return {"error": str(e)}, 500


async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    async for event in r:
        yield json.dumps(event, ensure_ascii=False) + "\n"


@api_router.post("/chat_stream")
async def chat_stream(request: Request, search_client=Depends(get_search_client)):
    try:
        if request is None:
            raise HTTPException(status_code=400, detail="Request must not be None")

        if request.headers.get("Content-Type") != "application/json":
            raise HTTPException(status_code=415, detail="Request must be JSON")

        request_json = await request.json()
        auth_helper = get_auth_helper()
        auth_claims = await auth_helper.get_auth_claims_if_enabled(request.headers)

        impl = ChatReadRetrieveReadApproach(
            search_client,
            OPENAI_HOST,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            OPENAI_CHATGPT_MODEL,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            OPENAI_EMB_MODEL,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT,
        )
        response_generator = impl.run_with_streaming(
            request_json["history"], request_json.get("overrides", {}), auth_claims
        )

        return StreamingResponse(format_as_ndjson(response_generator), media_type="application/x-ndjson")
    except Exception as e:
        logging.exception("Exception in /chat")
        return {"error": str(e)}, 500


@app.middleware("http")
async def before_request(request: Request, call_next):
    # Used by the OpenAI SDK
    try:
        openai.api_type = "azure_ad"
        openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
        openai.api_version = "2023-07-01-preview"

        azure_credential = get_azure_credential()
        openai_token = await azure_credential.get_token("https://cognitiveservices.azure.com/.default")
        openai.api_key = openai_token.token

        # Store on request.state for later use inside requests
        request.state.openai_token = openai_token
        return await call_next(request)
    except Exception as e:
        logging.exception("Exception in before_request")
        return JSONResponse(content={"error": str(e)}, status_code=500)


def create_app():
    app.include_router(api_router, prefix="/api")
    app.include_router(document_router, prefix="/api/documents")
    app.include_router(root_router)

    # Level should be one of https://docs.python.org/3/library/logging.html#logging-levels
    default_level = "INFO"  # In development, log more verbosely
    if os.getenv("WEBSITE_HOSTNAME"):  # In production, don't log as heavily
        default_level = "WARNING"
    logging.basicConfig(level=os.getenv("APP_LOG_LEVEL", default_level))

    if allowed_origin := os.getenv("ALLOWED_ORIGIN"):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[allowed_origin],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logging.info("CORS enabled for %s", allowed_origin)

    return app
