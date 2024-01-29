import os
from llama_index import (
    Document,
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
    set_global_service_context,
)
from llama_index.node_parser import SentenceSplitter
from llama_index.llms import AzureOpenAI
from llama_index.embeddings import AzureOpenAIEmbedding
from llama_index.vector_stores.types import ExactMatchFilter, MetadataFilters

from core.types import Status
from core.utilities import scrape_url
from core.db import get_db
from core.logger import logger

api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
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


def get_index():
    storage_context = StorageContext.from_defaults(persist_dir="storage")

    index = load_index_from_storage(storage_context)

    return index


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

    index = VectorStoreIndex.from_documents(documents)

    index.storage_context.persist(persist_dir="storage")


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

        documents = []
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

            documents.append(document)

        node_parser = SentenceSplitter.from_defaults(chunk_size=max_tokens)
        nodes = node_parser.get_nodes_from_documents(documents)

        index = get_index()
        index.insert_nodes(nodes)

        db.documents.update_one({"id": id}, {"$set": {"status": Status.done.value}})
    except Exception as e:
        logger.exception("Failed to index document: {}".format(e))
        db.documents.update_one({"id": id}, {"$set": {"status": Status.error.value}})


def get_index_documents_by_field(value=None, field="ref_id"):
    index = get_index()

    matches = index.as_query_engine(
        filters=MetadataFilters(filters=[ExactMatchFilter(key=field, value=value)])
    )

    ids = []
    for match in matches:
        ids.append(match["metadata"]["ref_doc_id"])

    return ids


def remove_document_from_index(value=None, field="ref_id"):
    index = get_index()

    if field == "doc_id":
        index.delete(value)
        return

    docs_ids = get_index_documents_by_field(value=value, field=field)

    for doc_id in docs_ids:
        index.delete(doc_id)


def get_engine():
    index = get_index()

    return index.as_query_engine(streaming=True)
