import os
from llama_index import (
    Document,
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
    set_global_service_context,
)
from llama_index.node_parser import SimpleFileNodeParser, SentenceSplitter
from llama_index.llms import AzureOpenAI
from llama_index.embeddings import AzureOpenAIEmbedding
from llama_index.storage.docstore import RedisDocumentStore
from llama_index.vector_stores import RedisVectorStore
from redis.client import Redis

from core.types import Status
from core.utilities import scrape_url
from core.db import get_db
from core.logger import logger

api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("ASURE_OPENAI_ENDPOINT")
api_version = os.getenv("OPENAI_API_VERSION")

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
    engine=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT"),
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint,
    max_retries=15,
    system_prompt="""
    You are a helpful assistant that helps customer support agents employeed at a telecom company. Questions will be related to customer support questions, and internal guidelines for customer support.
    Be brief in your answers.
    Always answer all questions in norwegian.
    Answer ONLY with the facts listed in your sources. If there isn't enough information in the sources, just say you don't know the answer. Do not generate answers that don't use the sources. If asking a clarifying question would help then ask the question.
    Return data as html, except source data. Do not return a wall of text, and do not return markdown format.
    Each source has metadata attached to it. If you use the source, you must include it in the bottom of the answer.
    Use square brackets to reference the source, e.g. [filename.pdf]. Don't combine sources, list each source separately, e.g. [filename-1.pdf][filename-2.pdf]. If it is a web url use the complete url as the source name, e.g. [https://www.example.com].
    """,
)

embed_model = AzureOpenAIEmbedding(
    model=os.getenv("AZURE_OPENAI_EMB_MODEL_NAME"),
    deployment_name=os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT"),
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
    max_retries=15,
)


REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)


def get_redis():
    return Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_vector_store():
    return RedisVectorStore(
        index_name="documents",
        index_prefix="vector_store",
        redis_url="redis://localhost:6379",  # Default
        overwrite=True,
    )


def get_storage_context():
    vector_store = get_vector_store()

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
    )

    return storage_context


service_context = ServiceContext.from_defaults(
    llm=llm,
    embed_model=embed_model,
    node_parser=SentenceSplitter(chunk_size=max_tokens),
)

set_global_service_context(service_context)


def index_web_documents():
    db = get_db()

    db_docs = db.documents.find(
        {
            "type": "web",
            "deleted": {"$ne": True},
        }
    )

    if db_docs is None:
        print("No documents found")
        raise Exception("No documents found")

    documents = []
    for doc in db_docs:
        for url in doc["urls"]:
            text = scrape_url(url)

            documents.append(
                Document(text=text, metadata={"url": url, "ref_id": doc["id"], "title": doc["title"], "type": "web"})
            )

    storage_context = get_storage_context()

    VectorStoreIndex.from_documents(documents, storage_context=storage_context)


def index_web_document(id, urls=[]):
    db = get_db()

    doc = db.documents.find_one({"id": id})

    if doc is None:
        print("No documents found")
        raise Exception("No documents found")

    db.documents.update_one({"id": id}, {"$set": {"status": Status.processing.value}})

    index_urls = doc["urls"] if len(urls) == 0 else urls

    documents = []
    for url in index_urls:
        text = scrape_url(url)

        documents.append(
            Document(text=text, metadata={"url": url, "ref_id": doc["id"], "title": doc["title"], "type": "web"})
        )

    storage_context = get_storage_context()

    VectorStoreIndex.from_documents(documents, storage_context=storage_context)

    doc = db.documents.update_one({"id": id}, {"$set": {"status": Status.done.value}})


def get_index_documents_by_field(value=None, field="ref_id"):
    r = get_redis()

    matches = []
    for key in r.scan_iter():  # Iterate over all keys
        if r.type(key) != "hash":
            continue
        if r.hget(key, field) != value:
            continue

        values = r.hmget(key, ["doc_id", "ref_id", "url"])

        matches.append({"name": key, "doc_id": values[0], "ref_id": values[1], "url": values[2]})

    return matches


def remove_document_from_index(doc_id):
    r = get_redis()

    docs = get_index_documents_by_field(doc_id)

    for doc in docs:
        r.delete(doc["name"])


def get_engine():
    vector_store = get_vector_store()

    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    return index.as_query_engine(streaming=True)
