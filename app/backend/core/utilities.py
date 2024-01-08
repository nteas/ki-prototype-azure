import base64
import html
import os
import re
import time

import openai
import tiktoken
import hashlib
from typing import Any
from bs4 import BeautifulSoup
from selenium import webdriver
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from core.logger import logger
from core.db import get_db
from core.types import Document, Log, Status, UrlDocument, get_title_from_url

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
SUPPORTED_BATCH_AOAI_MODEL = {"text-embedding-ada-002": {"token_limit": 8100, "max_batch_size": 16}}


def hash_text_md5(text):
    # Create a new md5 hash object
    hash_object = hashlib.md5()

    # Update the hash object with the bytes of the text
    hash_object.update(text.encode("utf-8"))

    # Get the hexadecimal representation of the hash
    hash_hex = hash_object.hexdigest()

    return hash_hex


def calculate_tokens_emb_aoai(input: str):
    encoding = tiktoken.encoding_for_model(os.getenv("AZURE_OPENAI_EMB_MODEL_NAME"))
    return len(encoding.encode(input))


def blob_name_from_file_page(filename, page=0):
    return os.path.splitext(filename)[0] + f"-{page}" + ".pdf"


def migrate_data():
    db = get_db()

    docs = db.documents.find({"type": "web", "deleted": {"$ne": True}})

    if docs is None:
        print("No daily documents found")
        return

    docs = list(docs)

    for doc in docs:
        url = doc.get("url")
        hash = doc.get("hash") or None

        doc["urls"] = [UrlDocument(url=url, hash=hash)]

        del doc["url"]

        db.documents.update_one({"_id": doc["_id"]}, {"$set": doc, "$unset": {"url": ""}})

    logger.info(f"Migrated {len(docs)} documents")
    logger.info("Done migrating data")


def table_to_html(table):
    table_html = "<table>"
    rows = [
        sorted([cell for cell in table.cells if cell.row_index == i], key=lambda cell: cell.column_index)
        for i in range(table.row_count)
    ]
    for row_cells in rows:
        table_html += "<tr>"
        for cell in row_cells:
            tag = "th" if (cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
            cell_spans = ""
            if cell.column_span > 1:
                cell_spans += f" colSpan={cell.column_span}"
            if cell.row_span > 1:
                cell_spans += f" rowSpan={cell.row_span}"
            table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
        table_html += "</tr>"
    table_html += "</table>"
    return table_html


def get_document_text(file):
    logger.info("Begin extracting document text")

    AZURE_FORMRECOGNIZER_SERVICE = os.getenv("AZURE_FORMRECOGNIZER_SERVICE")
    formrecognizer_creds = AzureKeyCredential(os.environ["AZURE_FORMRECOGNIZER_KEY"])
    form_recognizer_client = DocumentAnalysisClient(
        endpoint=f"https://{AZURE_FORMRECOGNIZER_SERVICE}.cognitiveservices.azure.com/",
        credential=formrecognizer_creds,
        headers={"x-ms-useragent": "azure-search-chat-demo/1.0.0"},
    )
    try:
        offset = 0
        page_map = []

        poller = form_recognizer_client.begin_analyze_document("prebuilt-layout", document=file)
        form_recognizer_results = poller.result()

        for page_num, page in enumerate(form_recognizer_results.pages):
            tables_on_page = [
                table
                for table in (form_recognizer_results.tables or [])
                if table.bounding_regions and table.bounding_regions[0].page_number == page_num + 1
            ]

            # mark all positions of the table spans in the page
            page_offset = page.spans[0].offset
            page_length = page.spans[0].length
            table_chars = [-1] * page_length
            for table_id, table in enumerate(tables_on_page):
                for span in table.spans:
                    # replace all table spans with "table_id" in table_chars array
                    for i in range(span.length):
                        idx = span.offset - page_offset + i
                        if idx >= 0 and idx < page_length:
                            table_chars[idx] = table_id

            # build page text by replacing characters in table spans with table html
            page_text = ""
            added_tables = set()
            for idx, table_id in enumerate(table_chars):
                if table_id == -1:
                    page_text += form_recognizer_results.content[page_offset + idx]
                elif table_id not in added_tables:
                    page_text += table_to_html(tables_on_page[table_id])
                    added_tables.add(table_id)

            page_text += " "
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)

        logger.info("Done extracting document text")

        return page_map
    except Exception as e:
        logger.exception(f"Error extracting text from file: {e}")
        raise e


def split_text(page_map, filename):
    logger.info(f"Splitting '{filename}' into sections")

    def find_page(offset):
        num_pages = len(page_map)
        for i in range(num_pages - 1):
            if offset >= page_map[i][1] and offset < page_map[i + 1][1]:
                return i
        return num_pages - 1

    all_text = "".join(p[2] for p in page_map)
    length = len(all_text)
    start = 0
    end = length
    while start + SECTION_OVERLAP < length:
        last_word = -1
        end = start + MAX_SECTION_LENGTH

        if end > length:
            end = length
        else:
            # Try to find the end of the sentence
            while (
                end < length
                and (end - start - MAX_SECTION_LENGTH) < SENTENCE_SEARCH_LIMIT
                and all_text[end] not in SENTENCE_ENDINGS
            ):
                if all_text[end] in WORDS_BREAKS:
                    last_word = end
                end += 1
            if end < length and all_text[end] not in SENTENCE_ENDINGS and last_word > 0:
                end = last_word  # Fall back to at least keeping a whole word
        if end < length:
            end += 1

        # Try to find the start of the sentence or at least a whole word boundary
        last_word = -1
        while (
            start > 0
            and start > end - MAX_SECTION_LENGTH - 2 * SENTENCE_SEARCH_LIMIT
            and all_text[start] not in SENTENCE_ENDINGS
        ):
            if all_text[start] in WORDS_BREAKS:
                last_word = start
            start -= 1
        if all_text[start] not in SENTENCE_ENDINGS and last_word > 0:
            start = last_word
        if start > 0:
            start += 1

        section_text = all_text[start:end]
        yield (section_text, find_page(start))

        last_table_start = section_text.rfind("<table")
        if last_table_start > 2 * SENTENCE_SEARCH_LIMIT and last_table_start > section_text.rfind("</table"):
            # If the section ends with an unclosed table, we need to start the next section with the table.
            # If table starts inside SENTENCE_SEARCH_LIMIT, we ignore it, as that will cause an infinite loop for tables longer than MAX_SECTION_LENGTH
            # If last table starts inside SECTION_OVERLAP, keep overlapping
            logger.info(
                f"Section ends with unclosed table, starting next section with the table at page {find_page(start)} offset {start} table start {last_table_start}"
            )
            start = min(end - SECTION_OVERLAP, start + last_table_start)
        else:
            start = end - SECTION_OVERLAP

    if start + SECTION_OVERLAP < end:
        yield (all_text[start:end], find_page(start))


def split_text_string(text):
    length = len(text)
    start = 0
    end = length
    while start + SECTION_OVERLAP < length:
        last_word = -1
        end = start + MAX_SECTION_LENGTH

        if end > length:
            end = length
        else:
            while (
                end < length
                and (end - start - MAX_SECTION_LENGTH) < SENTENCE_SEARCH_LIMIT
                and text[end] not in SENTENCE_ENDINGS
            ):
                if text[end] in WORDS_BREAKS:
                    last_word = end
                end += 1
            if end < length and text[end] not in SENTENCE_ENDINGS and last_word > 0:
                end = last_word
        if end < length:
            end += 1

        last_word = -1
        while (
            start > 0
            and start > end - MAX_SECTION_LENGTH - 2 * SENTENCE_SEARCH_LIMIT
            and text[start] not in SENTENCE_ENDINGS
        ):
            if text[start] in WORDS_BREAKS:
                last_word = start
            start -= 1
        if text[start] not in SENTENCE_ENDINGS and last_word > 0:
            start = last_word
        if start > 0:
            start += 1

        section_text = text[start:end]
        yield section_text

        last_table_start = section_text.rfind("<table")
        if last_table_start > 2 * SENTENCE_SEARCH_LIMIT and last_table_start > section_text.rfind("</table"):
            start = min(end - SECTION_OVERLAP, start + last_table_start)
        else:
            start = end - SECTION_OVERLAP

    if start + SECTION_OVERLAP < end:
        yield text[start:end]


def filename_to_id(filename):
    filename_ascii = re.sub("[^0-9a-zA-Z_-]", "_", filename)
    filename_hash = base64.b16encode(filename.encode("utf-8")).decode("ascii")
    return f"file-{filename_ascii}-{filename_hash}"


def create_sections(filename, page_map):
    logger.info("Begin creating sections")

    file_id = filename_to_id(filename)
    for i, (content, pagenum) in enumerate(split_text(page_map, filename)):
        section = {
            "id": f"{file_id}-page-{i}",
            "content": content,
            "category": "",
            "sourcepage": blob_name_from_file_page(filename, pagenum),
            "sourcefile": filename,
        }

        section["embedding"] = compute_embedding(content)

        yield section

    logger.info("Done creating sections")


def create_sections_string(url, string):
    logger.info("Begin creating sections")

    pretty_url = get_title_from_url(url)
    pretty_url_ascii = re.sub("[^0-9a-zA-Z_-]", "_", pretty_url)
    pretty_url_hash = base64.b16encode(pretty_url.encode("utf-8")).decode("ascii")
    pretty_url_id = f"web-{pretty_url_ascii}-{pretty_url_hash}"

    for i, content in enumerate(split_text_string(string)):
        section = {
            "id": f"{pretty_url_id}-section-{i}",
            "content": content,
            "category": "",
            "sourcepage": url,
            "sourcefile": pretty_url,
        }

        section["embedding"] = compute_embedding(content)

        yield section

    logger.info("Done creating sections")


def before_retry_sleep(retry_state):
    logger.info("Rate limited on the OpenAI embeddings API, sleeping before retrying...")


@retry(
    retry=retry_if_exception_type(openai.error.RateLimitError),
    wait=wait_random_exponential(min=15, max=60),
    stop=stop_after_attempt(15),
    before_sleep=before_retry_sleep,
)
def compute_embedding(text):
    try:
        embedding_args = {"deployment_id": os.environ["AZURE_OPENAI_EMB_DEPLOYMENT"]}
        return openai.Embedding.create(
            **embedding_args, model=os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-ada-002"), input=text
        )["data"][0]["embedding"]
    except Exception as e:
        logger.exception(f"Error computing embedding for text: {e}")
        raise e


@retry(
    retry=retry_if_exception_type(openai.error.RateLimitError),
    wait=wait_random_exponential(min=15, max=60),
    stop=stop_after_attempt(15),
    before_sleep=before_retry_sleep,
)
def compute_embedding_in_batch(texts):
    try:
        embedding_args = {"deployment_id": os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT")}
        emb_response = openai.Embedding.create(
            **embedding_args, model=os.getenv("AZURE_OPENAI_EMB_MODEL_NAME"), input=texts
        )
        return [data.embedding for data in emb_response.data]
    except Exception as e:
        logger.exception(f"Error computing embedding for text: {e}")
        raise e


def update_embeddings_in_batch(sections):
    logger.info("Begin updating batch embeddings")

    batch_queue: list = []
    copy_s = []
    batch_response = {}
    token_count = 0
    for s in sections:
        token_count += calculate_tokens_emb_aoai(s["content"])
        if (
            token_count <= SUPPORTED_BATCH_AOAI_MODEL[os.getenv("AZURE_OPENAI_EMB_MODEL_NAME")]["token_limit"]
            and len(batch_queue)
            < SUPPORTED_BATCH_AOAI_MODEL[os.getenv("AZURE_OPENAI_EMB_MODEL_NAME")]["max_batch_size"]
        ):
            batch_queue.append(s)
            copy_s.append(s)
        else:
            emb_responses = compute_embedding_in_batch([item["content"] for item in batch_queue])
            logger.info(f"Batch Completed. Batch size  {len(batch_queue)} Token count {token_count}")
            for emb, item in zip(emb_responses, batch_queue):
                batch_response[item["id"]] = emb
            batch_queue = []
            batch_queue.append(s)
            token_count = calculate_tokens_emb_aoai(s["content"])

    if batch_queue:
        emb_responses = compute_embedding_in_batch([item["content"] for item in batch_queue])
        logger.info(f"Batch Completed. Batch size  {len(batch_queue)} Token count {token_count}")
        for emb, item in zip(emb_responses, batch_queue):
            batch_response[item["id"]] = emb

    for s in copy_s:
        s["embedding"] = batch_response[s["id"]]
        yield s

    logger.info("Done updating batch embeddings")


def index_sections(sections, search_client):
    try:
        logger.info("Begin indexing sections")

        i = 0
        batch = []
        for s in sections:
            batch.append(s)
            i += 1
            if i % 1000 == 0:
                results = search_client.upload_documents(documents=batch)
                succeeded = sum([1 for r in results if r.succeeded])
                logger.info(f"Indexed {len(results)} sections, {succeeded} succeeded")
                batch = []

        if len(batch) > 0:
            results = search_client.upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            logger.info(f"Indexed {len(results)} sections, {succeeded} succeeded")

        logger.info("Done indexing sections")
    except Exception as e:
        logger.exception(f"Error indexing sections: {e}")


def scrape_url(url):
    try:
        logger.info("Begin scraping content from url")

        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        # Wait for the page to be fully loaded
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        page_source = driver.page_source
        driver.quit()

        # Parse the HTML content of the response
        soup = BeautifulSoup(page_source, "html.parser")

        for tag in soup(
            ["header", "footer", "a", "button", "img", "script", "style", "noscript", "form", "input", "svg"]
        ):
            tag.decompose()

        for tag in soup.select("[class*=breadcrumbs], [class*=tags], [id*=chat], [class*=related]"):
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

        return text

        logger.info("Done scraping content from url")
    except Exception as ex:
        logger.exception("Error in scrape_url: {}".format(ex))
        raise ex


def remove_from_index(filename, search_client):
    try:
        logger.info("Begin removing sections from from index")

        while True:
            filter = f"sourcepage eq '{filename}'"
            search_results = search_client.search(search_text="", filter=filter, select=["id"])

            docs = []
            for doc in search_results:
                docs.append(doc)

            if len(docs) == 0:
                break

            search_client.delete_documents(documents=docs)
            # It can take a few seconds for search results to reflect changes, so wait a bit
            time.sleep(2)

        logger.info("Done removing sections from index")
    except Exception as e:
        logger.exception(f"Error removing sections from index: {e}")


def process_web(id, search_client):
    try:
        logger.info("Begin processing document")

        db = get_db()

        doc = db.documents.find_one({"id": id})

        if doc is None:
            logger.info("Document not found")
            return

        doc = Document(**doc)

        sections = []
        hasChanges = False

        for index, url in enumerate(doc.urls):
            text = scrape_url(url.url)

            hashed_text = hash_text_md5(text)

            # check if content has changed
            if url.hash == hashed_text:
                db.documents.update_one({"id": id}, {"$set": {"urls.{}.hash".format(index): hashed_text}})
                continue

            hasChanges = True

            remove_from_index(url.url, search_client)

            new_sections = create_sections_string(
                url.url,
                text,
            )

            sections.extend(new_sections)

        if hasChanges:
            sections = update_embeddings_in_batch(sections)

            index_sections(sections, search_client)

        else:
            logger.info("Document has not changed")
            return

        doc.status = Status.done.value
        db.documents.update_one({"id": id}, {"$set": doc.model_dump()})

        logger.info("Done processing document")

    except Exception as e:
        logger.exception("Failed to process document: {}".format(e))


def process_file(id, file_data, search_client, blob_container_client):
    try:
        logger.info("Begin processing document")
        db = get_db()

        doc = db.documents.find_one({"id": id})
        doc = Document(**doc)

        if doc.file is not None and doc.file_pages is not None:
            for page in doc.file_pages:
                remove_from_index(page, search_client)

        if doc.file_pages:
            blob_container_client.delete_blobs(*doc.file_pages)

        filename = file_data["filename"]

        # update document
        doc.file = filename
        doc.file_pages = file_data["file_pages"]
        doc.logs.append(Log(user=doc.owner, change="update_file", message="File updated"))

        page_map = get_document_text(file_data["pdf"])

        sections = list(
            create_sections(
                filename,
                page_map,
            )
        )

        sections = update_embeddings_in_batch(sections)

        index_sections(sections, search_client)

        db.documents.update_one({"id": id}, {"$set": doc.model_dump()})

        logger.info("Done processing document")

    except Exception as e:
        logger.exception("Failed to process document: {}".format(e))
