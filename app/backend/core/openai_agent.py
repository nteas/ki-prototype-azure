import os
from llama_index import (
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
    download_loader,
    load_index_from_storage,
    set_global_service_context,
)
from llama_index.tools import QueryEngineTool, ToolMetadata, FunctionTool
from llama_index.node_parser import SimpleFileNodeParser, SentenceSplitter
from llama_index.llms import AzureOpenAI
from llama_index.embeddings import AzureOpenAIEmbedding
from llama_index.storage.docstore import RedisDocumentStore
from llama_index.storage.index_store import RedisIndexStore
from llama_index.vector_stores import RedisVectorStore

from core.db import get_db
from core.logger import logger

BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")

api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("ASURE_OPENAI_ENDPOINT")
api_version = "2023-07-01-preview"

MODELS_2_TOKEN_LIMITS = {
    "gpt-35-turbo": 4000,
    "gpt-3.5-turbo": 4000,
    "gpt-35-turbo-16k": 16000,
    "gpt-3.5-turbo-16k": 16000,
    "gpt-4": 8100,
    "gpt-4-32k": 32000,
}

max_tokens = MODELS_2_TOKEN_LIMITS[os.getenv("AZURE_OPENAI_CHATGPT_MODEL")]

llm = AzureOpenAI(
    model=os.getenv("AZURE_OPENAI_CHATGPT_MODEL"),
    deployment_name=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT"),
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
    system_prompt="""
    Assistant helps customer support agents employeed at NTE (a telecom company) with customer support questions, and internal guidelines for customer support. 
    Be brief in your answers.
    Answer ONLY with the facts listed in the list of sources. If there isn't enough information in the sources, just say you don't know the answer. Do not generate answers that don't use the sources. If asking a clarifying question to the user would help, ask the question.
    Return data as html, except source data. Do not return a wall of text, and do not return markdown format. Always answer all questions in norwegian.
    Each source has metadata attached to it. If you use the source, you must include the metadata in the bottom of the answer. If you don't use the source, you must not include the metadata in the answer.
    """,
)

# You need to deploy your own embedding model as well as your own chat completion model
embed_model = AzureOpenAIEmbedding(
    model=os.getenv("AZURE_OPENAI_EMB_MODEL_NAME"),
    deployment_name=os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT"),
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
)
service_context = ServiceContext.from_defaults(
    llm=llm,
    embed_model=embed_model,
    node_parser=SentenceSplitter(chunk_size=max_tokens),
)

set_global_service_context(service_context=service_context)

persist_dir = "./storage"

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)


def get_storage_context():
    storage_context = StorageContext.from_defaults(
        docstore=RedisDocumentStore.from_host_and_port(host=REDIS_HOST, port=REDIS_PORT, namespace="docstore"),
        index_store=RedisIndexStore.from_host_and_port(host=REDIS_HOST, port=REDIS_PORT, namespace="index_store"),
        vector_store=RedisVectorStore(
            index_name="documents",
            redis_url="redis://localhost:6379",  # Default
            overwrite=True,
        ),
    )

    return storage_context


def index_web_documents():
    loader = BeautifulSoupWebReader()

    db = get_db()

    db_docs = db.documents.find(
        {
            "type": "web",
            "deleted": {"$ne": True},
        }
    ).limit(1)

    if db_docs is None:
        print("No documents found")
        raise Exception("No documents found")

    documents = []
    for doc in db_docs:
        urls = [url["url"] for url in doc["urls"]]
        loaded_docs = loader.load_data(urls=urls)
        for loaded_doc in loaded_docs:
            loaded_doc.metadata["document_id"] = doc["id"]

        documents.extend(loaded_docs)

    storage_context = get_storage_context()

    VectorStoreIndex.from_documents(documents, storage_context=storage_context)


def get_engine():
    storage_context = get_storage_context()

    index = VectorStoreIndex.from_vector_store(vector_store=storage_context.vector_store)

    return index.as_query_engine(streaming=True)
