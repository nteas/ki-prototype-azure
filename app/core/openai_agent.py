import os
from llama_index import (
    Document,
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
    set_global_service_context,
)
from llama_index.node_parser import SentenceSplitter
from llama_index.llms import AzureOpenAI
from llama_index.embeddings import AzureOpenAIEmbedding
from llama_index.vector_stores import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from core.types import Status
from core.utilities import scrape_url
from core.db import get_db
from core.logger import logger

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "vectors")

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
    api_key=AZURE_OPENAI_API_KEY,
    api_version=OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    max_retries=15,
    system_prompt="""
    You are a helpful assistant that helps customer support agents employeed at a telecom company. Questions will be related to customer support questions, and internal guidelines for customer support.
    Be brief in your answers.
    Always answer all questions in norwegian.
    Answer ONLY with the facts listed in your sources. If there isn't enough information in the sources, just say you don't know the answer. Do not generate answers that don't use the sources. If asking a clarifying question would help then ask the question.
    Return the response as markdown, excluding the sources.
    Each source has metadata attached to it. If you use the source, you must include it in the bottom of the answer.
    Use square brackets to reference the source, e.g. [filename.pdf]. Don't combine sources, list each source separately, e.g. [filename-1.pdf][filename-2.pdf]. If it is a web url use the complete url as the source name, e.g. [https://www.example.com].
    """,
)

embed_model = AzureOpenAIEmbedding(
    model=os.getenv("AZURE_OPENAI_EMB_MODEL_NAME"),
    deployment_name=os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT"),
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=OPENAI_API_VERSION,
    max_retries=15,
)


def get_pinecone():
    pc_api_key = os.getenv("PINECONE_API_KEY")

    return Pinecone(api_key=pc_api_key)


def initialize_pinecone():
    pinecone_client = get_pinecone()

    if PINECONE_INDEX_NAME not in pinecone_client.list_indexes().names():
        print("Index does not exist, creating...")
        pinecone_client.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-west-2"),
        )


def get_pinecone_index():
    pc = get_pinecone()

    return pc.Index(PINECONE_INDEX_NAME)


def get_vector_store():
    pinecone_index = get_pinecone_index()
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    return vector_store


def get_index():
    vector_store = get_vector_store()

    return VectorStoreIndex.from_vector_store(vector_store=vector_store)


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
        {"type": "web", "deleted": {"$ne": True}, "urls": {"$exists": True, "$ne": []}}
    )

    if db_docs is None:
        print("No documents found")
        raise Exception("No documents found")

    documents = []
    for doc in db_docs:
        for url in doc["urls"]:
            text = scrape_url(url)

            documents.append(
                Document(
                    text=text,
                    metadata={
                        "url": url,
                        "ref_id": doc["id"],
                        "title": doc["title"],
                        "type": "web",
                    },
                )
            )

    storage_context = get_storage_context()

    VectorStoreIndex.from_documents(documents, storage_context=storage_context)


def index_web_document(id, urls=[]):
    try:
        db = get_db()

        doc = db.documents.find_one({"id": id})

        if doc is None:
            print("No documents found")
            raise Exception("No documents found")

        db.documents.update_one(
            {"id": id}, {"$set": {"status": Status.processing.value}}
        )

        index_urls = doc["urls"] if len(urls) == 0 else urls

        index = get_index()
        for url in index_urls:
            text = scrape_url(url)

            document = Document(
                text=text,
                metadata={
                    "url": url,
                    "ref_id": doc["id"],
                    "title": doc["title"],
                    "type": "web",
                },
            )

            index.insert(document=document)

        db.documents.update_one({"id": id}, {"$set": {"status": Status.done.value}})
    except Exception as e:
        logger.exception("Failed to index document: {}".format(e))
        db.documents.update_one({"id": id}, {"$set": {"status": Status.error.value}})


def get_index_documents_by_field(value=None, field="ref_id"):
    pinecone_index = get_pinecone_index()
    matches = pinecone_index.query(
        vector=[0.0] * 1536,  # [0.0, 0.0, 0.0, 0.0, 0.0
        top_k=1,
        filter={field: value},
    )

    if len(matches["matches"]) == 0:
        return []

    docs_ids = [match.id for match in matches["matches"]]

    return docs_ids


def remove_document_from_index(value=None, field="ref_id"):
    doc_ids = get_index_documents_by_field(value=value, field=field)

    if len(doc_ids) == 0:
        return

    index = get_pinecone_index()

    index.delete(ids=doc_ids)


def get_engine():
    index = get_index()

    return index.as_query_engine(streaming=True)