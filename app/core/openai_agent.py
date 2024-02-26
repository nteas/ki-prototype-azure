import os
import tempfile
from llama_index import (
    Document,
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
    set_global_service_context,
    download_loader,
)
from llama_index.node_parser import SentenceSplitter
from llama_index.llms import AzureOpenAI, MessageRole, ChatMessage
from llama_index.embeddings import AzureOpenAIEmbedding
from llama_index.vector_stores import PineconeVectorStore
from llama_index.chat_engine import CondenseQuestionChatEngine
from llama_index.prompts.base import PromptTemplate
from pinecone import Pinecone, ServerlessSpec
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext


from core.types import Status
from core.utilities import scrape_url
from core.db import get_db
from core.logger import logger

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "vectors")

SYSTEM_PROMPT = """
            You are a customer support agent at NTE, a telecom provider in Norway. 
            Never reply that the user should contact anyone else. 
            Always use your sources to answer a question. 
            Answer ONLY with the facts listed in your sources. 
            If the answer is not in the sources, then politely respond that you do not know the answer.
            if the sources are not helpful to answer the question, then politely respond that you do not know the answer.
            Always give detailed and helpful information, in a easy to read format.
            Always answer all questions in norwegian.
            Return the response as markdown.
            Do not list the sources in the response.
        """

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
    temperature=0,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    max_retries=15,
    system_prompt=SYSTEM_PROMPT,
)

embed_model = AzureOpenAIEmbedding(
    model=os.getenv("AZURE_OPENAI_EMB_MODEL_NAME"),
    deployment_name=os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT"),
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=OPENAI_API_VERSION,
    max_retries=15,
)


def initialize_service_context():
    logger.info("Initializing service context")

    service_context = ServiceContext.from_defaults(
        llm=llm,
        embed_model=embed_model,
        node_parser=SentenceSplitter(chunk_size=max_tokens),
    )

    set_global_service_context(service_context)


def get_pinecone():
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def initialize_pinecone():
    pinecone_client = get_pinecone()

    if PINECONE_INDEX_NAME not in pinecone_client.list_indexes().names():
        logger.info("Index does not exist, creating...")
        pinecone_client.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-west-2"),
        )

    initialize_service_context()


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


TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET")
SITE_NAME = os.getenv("SHAREPOINT_SITE_NAME")
RESOURCE = "https://nteholding.sharepoint.com"


def fetch_and_index_files():
    db = get_db()

    try:
        logger.info("Fetching and indexing files")

        logger.info("Add document in db for indexing status")
        db.jobs.insert_one({"type": "files_sync"})

        logger.info("Remove all files from index")
        remove_document_from_index(value="sharepoint")

        folder_url = os.getenv("SHAREPOINT_FOLDER_PATH")
        site_url = f"{RESOURCE}/sites/{SITE_NAME}"

        client_credentials = ClientCredential(CLIENT_ID, CLIENT_SECRET)
        ctx = ClientContext(site_url).with_credentials(client_credentials)

        files = ctx.web.get_folder_by_server_relative_path(folder_url).get_files(
            recursive=True
        )

        ctx.load(files)
        ctx.execute_query()

        if len(files) == 0:
            raise Exception("No files fount")

        logger.info(f"Files found: {len(files)}")

        PDFReader = download_loader("PDFReader")
        pdf_loader = PDFReader()
        DocxReader = download_loader("DocxReader")
        docx_loader = DocxReader()
        PptxReader = download_loader("PptxReader")
        pptx_loader = PptxReader()

        logger.info("Downloading files")
        count_indexed_nodes = 0
        index = get_index()

        for file in files:
            filetype = str(file).split(".")[-1]
            if filetype != "pdf" and filetype != "docx" and filetype != "pptx":
                continue

            logger.info(f"Downloading file: {file.properties['ServerRelativeUrl']}")

            temp_file = tempfile.NamedTemporaryFile(suffix=f".{filetype}", delete=False)
            file.download(temp_file).execute_query()
            temp_file.close()

            logger.info("file downloaded")
            docs = []
            url = file.linking_uri
            temp_file = open(temp_file.name, "rb")
            if filetype == "pdf":
                url = f"{RESOURCE}{file.properties['ServerRelativeUrl']}"
                docs = pdf_loader.load_data(temp_file)
            elif filetype == "docx":
                docs = docx_loader.load_data(temp_file)
            elif filetype == "pptx":
                docs = pptx_loader.load_data(temp_file)

            file_pages = []
            for doc in docs:
                if doc.text is None or len(doc.text) == 0:
                    continue
                file_pages.append(doc.get_doc_id())
                # add metadata to the document
                doc.metadata["title"] = str(file)
                doc.metadata["ref_id"] = "sharepoint"
                doc.metadata["type"] = "file"
                doc.metadata["url"] = url
                count_indexed_nodes += 1
                # add document to the index
                index.insert(document=doc)

        db.jobs.delete_many({"type": "files_sync"})

        logger.info(f"Files indexed: {count_indexed_nodes}")
    except Exception as e:
        db.jobs.delete_many({"type": "files_sync"})
        logger.exception("Failed to index documents: {}".format(e))
        raise e


def index_web_documents():
    try:
        db = get_db()

        db_docs = db.documents.find(
            {
                "type": "web",
                "deleted": {"$ne": True},
                "urls": {"$exists": True, "$ne": []},
            }
        )

        if db_docs is None:
            logger.info("No documents found")
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
    except Exception as e:
        logger.exception("Failed to index documents: {}".format(e))
        raise e


def index_web_document(id, urls=[]):
    try:
        db = get_db()

        doc = db.documents.find_one({"id": id})

        if doc is None:
            logger.info("No documents found")
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
        top_k=1000,
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


def get_engine(messages=[]):
    index = get_index()

    chat_history = []

    if len(messages) > 0:
        for message in messages:
            chat_message = ChatMessage(
                role=(
                    MessageRole.USER
                    if message["role"] == "user"
                    else MessageRole.ASSISTANT
                ),
                content=message["content"],
            )
            chat_history.append(chat_message)

    engine = index.as_query_engine(streaming=True, similarity_top_k=3)

    return CondenseQuestionChatEngine.from_defaults(
        query_engine=engine,
        chat_history=chat_history,
    )
