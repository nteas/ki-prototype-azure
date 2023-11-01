import os
from azure.search.documents.aio import SearchClient
from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential
from core.authentication import AuthenticationHelper


def get_auth_helper():
    auth_helper = AuthenticationHelper(
        use_authentication=os.getenv("AZURE_USE_AUTHENTICATION", "").lower() == "true",
        server_app_id=os.getenv("AZURE_SERVER_APP_ID"),
        server_app_secret=os.getenv("AZURE_SERVER_APP_SECRET"),
        client_app_id=os.getenv("AZURE_CLIENT_APP_ID"),
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        token_cache_path=os.getenv("TOKEN_CACHE_PATH"),
    )

    return auth_helper


def get_azure_credential():
    return DefaultAzureCredential(exclude_shared_token_cache_credential=True)


def get_search_client():
    azure_credential = get_azure_credential()
    return SearchClient(
        endpoint=f"https://{os.environ['AZURE_SEARCH_SERVICE']}.search.windows.net",
        index_name=os.environ("AZURE_SEARCH_INDEX"),
        credential=azure_credential,
    )


def get_blob_container_client():
    azure_credential = get_azure_credential()
    blob_client = BlobServiceClient(
        account_url=f"https://{os.environ('AZURE_STORAGE_ACCOUNT')}.blob.core.windows.net", credential=azure_credential
    )

    return blob_client.get_container_client(os.environ["AZURE_STORAGE_CONTAINER"])
