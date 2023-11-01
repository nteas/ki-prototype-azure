import io
import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import AsyncGenerator

import aiohttp
import openai
from fastapi import Depends, FastAPI, APIRouter, Request
from fastapi.staticfiles import StaticFiles

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.retrievethenread import RetrieveThenReadApproach

from routers.documents import document_router
from core.context import get_auth_helper, get_azure_credential, get_blob_container_client, get_search_client


CONFIG_OPENAI_TOKEN = "openai_token"
CONFIG_CREDENTIAL = "azure_credential"
CONFIG_ASK_APPROACH = "ask_approach"
CONFIG_CHAT_APPROACH = "chat_approach"
CONFIG_BLOB_CONTAINER_CLIENT = "blob_container_client"
CONFIG_AUTH_CLIENT = "auth_client"
CONFIG_SEARCH_CLIENT = "search_client"
CONFIG_MONGODB = "mongodb"
CONFIG_DB_NAME = "ki-prototype"
# Replace these with your own values, either in environment variables or directly here
AZURE_STORAGE_ACCOUNT = os.environ["AZURE_STORAGE_ACCOUNT"]
AZURE_STORAGE_CONTAINER = os.environ["AZURE_STORAGE_CONTAINER"]
AZURE_SEARCH_SERVICE = os.environ["AZURE_SEARCH_SERVICE"]
AZURE_SEARCH_INDEX = os.environ["AZURE_SEARCH_INDEX"]
# Shared by all OpenAI deployments
OPENAI_HOST = os.getenv("OPENAI_HOST", "azure")
OPENAI_CHATGPT_MODEL = os.environ["AZURE_OPENAI_CHATGPT_MODEL"]
OPENAI_EMB_MODEL = os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-ada-002")
# Used with Azure OpenAI deployments
AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT")
# Used only with non-Azure OpenAI deployments
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")
AZURE_USE_AUTHENTICATION = os.getenv("AZURE_USE_AUTHENTICATION", "").lower() == "true"
AZURE_SERVER_APP_ID = os.getenv("AZURE_SERVER_APP_ID")
AZURE_SERVER_APP_SECRET = os.getenv("AZURE_SERVER_APP_SECRET")
AZURE_CLIENT_APP_ID = os.getenv("AZURE_CLIENT_APP_ID")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
TOKEN_CACHE_PATH = os.getenv("TOKEN_CACHE_PATH")

KB_FIELDS_CONTENT = os.getenv("KB_FIELDS_CONTENT", "content")
KB_FIELDS_SOURCEPAGE = os.getenv("KB_FIELDS_SOURCEPAGE", "sourcepage")


app = FastAPI(debug=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

api_router = APIRouter()


# Empty page is recommended for login redirect to work.
# See https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/initialization.md#redirecturi-considerations for more information
@app.get("/redirect")
async def redirect():
    return ""


@app.get("/favicon.ico")
async def favicon():
    return await app.send_static_file("favicon.ico")


@app.get("/assets/<path:path>")
async def assets(path):
    return await app.send_static_file(Path("assets") / path)


@app.get("/")
@app.get("/<path:path>")
async def index(path=""):
    return await app.send_static_file("index.html")


# Serve content files from blob storage from within the app to keep the example self-contained.
# *** NOTE *** this assumes that the content files are public, or at least that all users of the app
# can access all the files. This is also slow and memory hungry.
@api_router.get("/content/<path>")
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
    return await api_router.send_file(blob_file, mimetype=mime_type, as_attachment=False, attachment_filename=path)


# Send MSAL.js settings to the client UI
@api_router.get("/auth_setup")
def auth_setup():
    logging.info("---------------------------------------------------------")
    return "data"


@api_router.post("/ask")
async def ask(request: Request, search_client=Depends(get_search_client)):
    if not request.is_json:
        return {"error": "request must be json"}, 415
    request_json = await request.get_json()
    auth_helper = get_auth_helper()
    auth_claims = await auth_helper.get_auth_claims_if_enabled({"Authorization": f"Bearer {openai.api_key}"})

    try:
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
    if not request.is_json:
        return {"error": "request must be json"}, 415
    request_json = await request.get_json()
    auth_helper = get_auth_helper()
    auth_claims = await auth_helper.get_auth_claims_if_enabled(request.headers)
    try:
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
    if not request.is_json:
        return {"error": "request must be json"}, 415
    request_json = await request.get_json()
    auth_helper = get_auth_helper()
    auth_claims = await auth_helper.get_auth_claims_if_enabled(request.headers)
    try:
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
        response = await format_as_ndjson(response_generator)
        response.timeout = None  # type: ignore
        return response
    except Exception as e:
        logging.exception("Exception in /chat")
        return {"error": str(e)}, 500


@app.middleware("http")
async def before_request(request: Request, call_next):
    # Used by the OpenAI SDK
    try:
        if OPENAI_HOST == "azure":
            openai.api_type = "azure_ad"
            openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
            openai.api_version = "2023-07-01-preview"

            azure_credential = get_azure_credential()
            openai_token = await azure_credential.get_token("https://cognitiveservices.azure.com/.default")
            openai.api_key = openai_token.token

            # Store on request.state for later use inside requests
            request.state.openai_token = openai_token
        else:
            openai.api_type = "openai"
            openai.api_key = OPENAI_API_KEY
            openai.organization = OPENAI_ORGANIZATION

        return await call_next(request)
    except Exception as e:
        logging.exception("Exception in before_request")
        return {"error": str(e)}, 500


def create_app():
    api_router.include_router(document_router, prefix="/documents")
    app.include_router(api_router, prefix="/api")

    # Level should be one of https://docs.python.org/3/library/logging.html#logging-levels
    default_level = "INFO"  # In development, log more verbosely
    if os.getenv("WEBSITE_HOSTNAME"):  # In production, don't log as heavily
        default_level = "WARNING"
    logging.basicConfig(level=os.getenv("APP_LOG_LEVEL", default_level))

    if allowed_origin := os.getenv("ALLOWED_ORIGIN"):
        logging.info("CORS enabled for %s", allowed_origin)

    return app
