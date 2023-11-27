import logging
import sys
from opencensus.ext.azure.log_exporter import AzureLogHandler
import os
from azure.search.documents.aio import SearchClient
from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential
from core.authentication import AuthenticationHelper

# Level should be one of https://docs.python.org/3/library/logging.html#logging-levels
handlers = [logging.StreamHandler(sys.stdout)]
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", None):
    handlers.append(AzureLogHandler(connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]))

logging.basicConfig(level=os.getenv("APP_LOG_LEVEL", "WARNING"), handlers=handlers)
logger = logging.getLogger(__name__)


def get_auth_helper():
    return AuthenticationHelper(
        use_authentication=os.getenv("AZURE_USE_AUTHENTICATION", "").lower() == "true",
        server_app_id=os.getenv("AZURE_SERVER_APP_ID"),
        server_app_secret=os.getenv("AZURE_SERVER_APP_SECRET"),
        client_app_id=os.getenv("AZURE_CLIENT_APP_ID"),
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        token_cache_path=os.getenv("TOKEN_CACHE_PATH"),
    )


def get_azure_credential():
    return DefaultAzureCredential(
        exclude_environment_credential=True, exclude_shared_token_cache_credential=True, logging_level=logging.ERROR
    )


async def get_search_client():
    azure_credential = get_azure_credential()
    search_client = SearchClient(
        endpoint=f"https://{os.environ['AZURE_SEARCH_SERVICE']}.search.windows.net",
        index_name=os.environ["AZURE_SEARCH_INDEX"],
        credential=azure_credential,
    )
    await azure_credential.close()
    return search_client


async def get_blob_container_client():
    azure_credential = get_azure_credential()
    blob_client = BlobServiceClient(
        account_url=f"https://{os.environ['AZURE_STORAGE_ACCOUNT']}.blob.core.windows.net",
        credential=azure_credential,
    )
    await azure_credential.close()
    return blob_client
