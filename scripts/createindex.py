import argparse
import base64
import glob
import html
import io
import os
import re
import tempfile
import time
from typing import Any, Optional, Union

import openai
import tiktoken
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.identity import AzureDeveloperCliCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswParameters,
    PrioritizedFields,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticSettings,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
)
from azure.storage.blob import BlobServiceClient
from azure.storage.filedatalake import (
    DataLakeServiceClient,
)
from pypdf import PdfReader, PdfWriter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

args = argparse.Namespace(
    verbose=False,
    openaihost="azure",
    datalakestorageaccount=None,
    datalakefilesystem=None,
    datalakepath=None,
    remove=False,
    useacls=False,
    skipblobs=False,
    storageaccount=None,
    container=None,
)
adls_gen2_creds = None
storage_creds = None

MAX_SECTION_LENGTH = 1000
SENTENCE_SEARCH_LIMIT = 100
SECTION_OVERLAP = 100

open_ai_token_cache: dict[str, Any] = {}
CACHE_KEY_TOKEN_CRED = "openai_token_cred"
CACHE_KEY_CREATED_TIME = "created_time"
CACHE_KEY_TOKEN_TYPE = "token_type"


def create_search_index():
    if args.verbose:
        print(f"Ensuring search index {args.index} exists")
    index_client = SearchIndexClient(
        endpoint=f"https://{args.searchservice}.search.windows.net/", credential=search_creds
    )
    fields = [
        SimpleField(name="id", type="Edm.String", key=True),
        SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            hidden=False,
            searchable=True,
            filterable=False,
            sortable=False,
            facetable=False,
            vector_search_dimensions=1536,
            vector_search_configuration="default",
        ),
        SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="sourcepage", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True),
    ]
    if args.useacls:
        fields.append(
            SimpleField(name="oids", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True)
        )
        fields.append(
            SimpleField(name="groups", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True)
        )

    if args.index not in index_client.list_index_names():
        index = SearchIndex(
            name=args.index,
            fields=fields,
            semantic_settings=SemanticSettings(
                configurations=[
                    SemanticConfiguration(
                        name="default",
                        prioritized_fields=PrioritizedFields(
                            title_field=None, prioritized_content_fields=[SemanticField(field_name="content")]
                        ),
                    )
                ]
            ),
            vector_search=VectorSearch(
                algorithm_configurations=[
                    VectorSearchAlgorithmConfiguration(
                        name="default", kind="hnsw", hnsw_parameters=HnswParameters(metric="cosine")
                    )
                ]
            ),
        )
        if args.verbose:
            print(f"Creating {args.index} search index")
        index_client.create_index(index)
    else:
        if args.verbose:
            print(f"Search index {args.index} already exists")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare documents by extracting content from PDFs, splitting content into sections, uploading to blob storage, and indexing in a search index.",
        epilog="Example: prepdocs.py '..\data\*' --storageaccount myaccount --container mycontainer --searchservice mysearch --index myindex -v",
    )
    parser.add_argument("files", nargs="?", help="Files to be processed")
    parser.add_argument(
        "--datalakestorageaccount", required=False, help="Optional. Azure Data Lake Storage Gen2 Account name"
    )
    parser.add_argument(
        "--datalakefilesystem",
        required=False,
        default="gptkbcontainer",
        help="Optional. Azure Data Lake Storage Gen2 filesystem name",
    )
    parser.add_argument(
        "--datalakepath",
        required=False,
        help="Optional. Azure Data Lake Storage Gen2 filesystem path containing files to index. If omitted, index the entire filesystem",
    )
    parser.add_argument(
        "--datalakekey", required=False, help="Optional. Use this key when authenticating to Azure Data Lake Gen2"
    )
    parser.add_argument(
        "--useacls", action="store_true", help="Store ACLs from Azure Data Lake Gen2 Filesystem in the search index"
    )
    parser.add_argument(
        "--category", help="Value for the category field in the search index for all sections indexed in this run"
    )
    parser.add_argument(
        "--skipblobs", action="store_true", help="Skip uploading individual pages to Azure Blob Storage"
    )
    parser.add_argument("--storageaccount", help="Azure Blob Storage account name")
    parser.add_argument("--container", help="Azure Blob Storage container name")
    parser.add_argument(
        "--storagekey",
        required=False,
        help="Optional. Use this Azure Blob Storage account key instead of the current user identity to login (use az login to set current user for Azure)",
    )
    parser.add_argument(
        "--tenantid", required=False, help="Optional. Use this to define the Azure directory where to authenticate)"
    )
    parser.add_argument(
        "--searchservice",
        help="Name of the Azure Cognitive Search service where content should be indexed (must exist already)",
    )
    parser.add_argument(
        "--index",
        help="Name of the Azure Cognitive Search index where content should be indexed (will be created if it doesn't exist)",
    )
    parser.add_argument(
        "--searchkey",
        required=False,
        help="Optional. Use this Azure Cognitive Search account key instead of the current user identity to login (use az login to set current user for Azure)",
    )
    parser.add_argument("--openaihost", help="Host of the API used to compute embeddings ('azure' or 'openai')")
    parser.add_argument("--openaiservice", help="Name of the Azure OpenAI service used to compute embeddings")
    parser.add_argument(
        "--openaideployment",
        help="Name of the Azure OpenAI model deployment for an embedding model ('text-embedding-ada-002' recommended)",
    )
    parser.add_argument(
        "--openaimodelname", help="Name of the Azure OpenAI embedding model ('text-embedding-ada-002' recommended)"
    )
    parser.add_argument(
        "--novectors",
        action="store_true",
        help="Don't compute embeddings for the sections (e.g. don't call the OpenAI embeddings API during indexing)",
    )
    parser.add_argument(
        "--disablebatchvectors", action="store_true", help="Don't compute embeddings in batch for the sections"
    )
    parser.add_argument(
        "--openaikey",
        required=False,
        help="Optional. Use this Azure OpenAI account key instead of the current user identity to login (use az login to set current user for Azure). This is required only when using non-Azure endpoints.",
    )
    parser.add_argument("--openaiorg", required=False, help="This is required only when using non-Azure endpoints.")
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove references to this document from blob storage and the search index",
    )
    parser.add_argument(
        "--removeall",
        action="store_true",
        help="Remove all blobs from blob storage and documents from the search index",
    )
    parser.add_argument(
        "--localpdfparser",
        action="store_true",
        help="Use PyPdf local PDF parser (supports only digital PDFs) instead of Azure Form Recognizer service to extract text, tables and layout from the documents",
    )
    parser.add_argument(
        "--formrecognizerservice",
        required=False,
        help="Optional. Name of the Azure Form Recognizer service which will be used to extract text, tables and layout from the documents (must exist already)",
    )
    parser.add_argument(
        "--formrecognizerkey",
        required=False,
        help="Optional. Use this Azure Form Recognizer account key instead of the current user identity to login (use az login to set current user for Azure)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Use the current user identity to connect to Azure services unless a key is explicitly set for any of them
    azd_credential = (
        AzureDeveloperCliCredential()
        if args.tenantid is None
        else AzureDeveloperCliCredential(tenant_id=args.tenantid, process_timeout=60)
    )
    adls_gen2_creds = azd_credential if args.datalakekey is None else AzureKeyCredential(args.datalakekey)
    search_creds: Union[TokenCredential, AzureKeyCredential] = azd_credential
    if args.searchkey is not None:
        search_creds = AzureKeyCredential(args.searchkey)
    use_vectors = not args.novectors

    if not args.skipblobs:
        storage_creds = azd_credential if args.storagekey is None else args.storagekey
    if not args.localpdfparser:
        # check if Azure Form Recognizer credentials are provided
        if args.formrecognizerservice is None:
            print(
                "Error: Azure Form Recognizer service is not provided. Please provide formrecognizerservice or use --localpdfparser for local pypdf parser."
            )
            exit(1)
        formrecognizer_creds: Union[TokenCredential, AzureKeyCredential] = azd_credential
        if args.formrecognizerkey is not None:
            formrecognizer_creds = AzureKeyCredential(args.formrecognizerkey)

    if use_vectors:
        if args.openaihost != "openai":
            if not args.openaikey:
                openai.api_key = azd_credential.get_token("https://cognitiveservices.azure.com/.default").token
                openai.api_type = "azure_ad"
                open_ai_token_cache[CACHE_KEY_CREATED_TIME] = time.time()
                open_ai_token_cache[CACHE_KEY_TOKEN_CRED] = azd_credential
                open_ai_token_cache[CACHE_KEY_TOKEN_TYPE] = "azure_ad"
            else:
                openai.api_key = args.openaikey
                openai.api_type = "azure"
            openai.api_base = f"https://{args.openaiservice}.openai.azure.com"
            openai.api_version = "2023-05-15"
        else:
            print("using normal openai")
            openai.api_key = args.openaikey
            openai.organization = args.openaiorg
            openai.api_type = "openai"

    create_search_index()
