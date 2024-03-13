import base64
import os
import re
from bs4 import BeautifulSoup
from llama_index.core.readers import download_loader

from typing import Any

from core.logger import logger
from core.db import get_db
from core.types import Document, Log

SimpleWebPageReader = download_loader("SimpleWebPageReader")

adls_gen2_creds = None
storage_creds = None

MAX_SECTION_LENGTH = 1000
SENTENCE_SEARCH_LIMIT = 100
SECTION_OVERLAP = 100
SENTENCE_ENDINGS = [".", "!", "?"]
WORDS_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]

open_ai_token_cache: dict[str, Any] = {}
CACHE_KEY_TOKEN_CRED = "openai_token_cred"
CACHE_KEY_CREATED_TIME = "created_time"
CACHE_KEY_TOKEN_TYPE = "token_type"

# Embedding batch support section
SUPPORTED_BATCH_AOAI_MODEL = {
    "text-embedding-ada-002": {"token_limit": 8100, "max_batch_size": 16}
}


def blob_name_from_file_page(filename, page=0):
    return os.path.splitext(filename)[0] + f"-{page}" + ".pdf"


def filename_to_id(filename):
    filename_ascii = re.sub("[^0-9a-zA-Z_-]", "_", filename)
    filename_hash = base64.b16encode(filename.encode("utf-8")).decode("ascii")
    return f"file-{filename_ascii}-{filename_hash}"


def scrape_url(url):
    try:
        logger.info("Begin scraping content from url")

        loader = SimpleWebPageReader()
        documents = loader.load_data(urls=[url])

        page_source = ""
        for doc in documents:
            page_source += doc.text

        # Parse the HTML content of the response
        soup = BeautifulSoup(page_source, "html.parser")

        for tag in soup(
            [
                "header",
                "footer",
                "a",
                "button",
                "img",
                "script",
                "style",
                "noscript",
                "form",
                "input",
                "svg",
            ]
        ):
            tag.decompose()

        for tag in soup.select(
            "[class*=breadcrumbs], [class*=tags], [id*=chat], [class*=related]"
        ):
            tag.decompose()

        # Extract the text of the HTML body
        selector_markup = soup.main

        if selector_markup is None:
            selector_markup = soup.find(id="main")

        if selector_markup is None:
            selector_markup = soup.find(id="content")

        if selector_markup is None:
            selector_markup = soup.body

        text = selector_markup.get_text()

        logger.info("Done scraping content from url")

        return text.replace("\n", " ").replace("\t", " ").replace("\r", " ")

    except Exception as ex:
        logger.exception("Error in scrape_url: {}".format(ex))
        raise ex


def process_file(id, file_data):
    try:
        logger.info("Begin processing document")
        db = get_db()

        doc = db.documents.find_one({"id": id})
        doc = Document(**doc)

        # if doc.file is not None and doc.file_pages is not None:
        #     for page in doc.file_pages:
        #         remove_from_index(page, search_client)

        # if doc.file_pages:
        #     blob_container_client.delete_blobs(*doc.file_pages)

        filename = file_data["filename"]

        # update document
        doc.file = filename
        doc.file_pages = file_data["file_pages"]
        doc.logs.append(
            Log(user=doc.owner, change="update_file", message="File updated")
        )

        db.documents.update_one({"id": id}, {"$set": doc.model_dump()})

        logger.info("Done processing document")

    except Exception as e:
        logger.exception("Failed to process document: {}".format(e))
