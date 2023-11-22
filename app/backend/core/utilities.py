import base64
import html
import logging
import os
import re
import time
from typing import Any, Optional
import openai
import tiktoken
from azure.ai.formrecognizer import DocumentAnalysisClient
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from core.context import get_search_client

adls_gen2_creds = None
storage_creds = None

MAX_SECTION_LENGTH = 1000
SENTENCE_SEARCH_LIMIT = 100
SECTION_OVERLAP = 100

open_ai_token_cache: dict[str, Any] = {}
CACHE_KEY_TOKEN_CRED = "openai_token_cred"
CACHE_KEY_CREATED_TIME = "created_time"
CACHE_KEY_TOKEN_TYPE = "token_type"

# Embedding batch support section
SUPPORTED_BATCH_AOAI_MODEL = {"text-embedding-ada-002": {"token_limit": 8100, "max_batch_size": 16}}


def calculate_tokens_emb_aoai(input: str):
    encoding = tiktoken.encoding_for_model(os.getenv("AZURE_OPENAI_EMB_MODEL_NAME"))
    return len(encoding.encode(input))


def blob_name_from_file_page(filename, page=0):
    return os.path.splitext(filename)[0] + f"-{page}" + ".pdf"


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


def get_document_text(file, formrecognizer_creds):
    AZURE_FORMRECOGNIZER_SERVICE = os.getenv("AZURE_FORMRECOGNIZER_SERVICE")
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

        return page_map
    except Exception as e:
        print(f"Error extracting text from file: {e}")
        raise e
    finally:
        print("Done extracting text")


def split_text(page_map, filename):
    SENTENCE_ENDINGS = [".", "!", "?"]
    WORDS_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]
    print(f"Splitting '{filename}' into sections")

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
            print(
                f"Section ends with unclosed table, starting next section with the table at page {find_page(start)} offset {start} table start {last_table_start}"
            )
            start = min(end - SECTION_OVERLAP, start + last_table_start)
        else:
            start = end - SECTION_OVERLAP

    if start + SECTION_OVERLAP < end:
        yield (all_text[start:end], find_page(start))


def filename_to_id(filename):
    filename_ascii = re.sub("[^0-9a-zA-Z_-]", "_", filename)
    filename_hash = base64.b16encode(filename.encode("utf-8")).decode("ascii")
    return f"file-{filename_ascii}-{filename_hash}"


def create_sections(
    filename, page_map, embedding_deployment: Optional[str] = None, embedding_model: Optional[str] = None
):
    file_id = filename_to_id(filename)
    for i, (content, pagenum) in enumerate(split_text(page_map, filename)):
        section = {
            "id": f"{file_id}-page-{i}",
            "content": content,
            "category": "",
            "sourcepage": blob_name_from_file_page(filename, pagenum),
            "sourcefile": filename,
        }

        section["embedding"] = compute_embedding(content, embedding_deployment, embedding_model)

        yield section


def before_retry_sleep():
    print("Rate limited on the OpenAI embeddings API, sleeping before retrying...")


@retry(
    retry=retry_if_exception_type(openai.error.RateLimitError),
    wait=wait_random_exponential(min=15, max=60),
    stop=stop_after_attempt(15),
    before_sleep=before_retry_sleep,
)
def compute_embedding(text, embedding_deployment, embedding_model):
    try:
        refresh_openai_token()
        embedding_args = {"deployment_id": embedding_deployment}
        return openai.Embedding.create(**embedding_args, model=embedding_model, input=text)["data"][0]["embedding"]
    except Exception as e:
        print(f"Error computing embedding for text: {e}")
        raise e


@retry(
    retry=retry_if_exception_type(openai.error.RateLimitError),
    wait=wait_random_exponential(min=15, max=60),
    stop=stop_after_attempt(15),
    before_sleep=before_retry_sleep,
)
def compute_embedding_in_batch(texts):
    try:
        refresh_openai_token()
        embedding_args = {"deployment_id": os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT")}
        emb_response = openai.Embedding.create(
            **embedding_args, model=os.getenv("AZURE_OPENAI_EMB_MODEL_NAME"), input=texts
        )
        return [data.embedding for data in emb_response.data]
    except Exception as e:
        print(f"Error computing embedding for text: {e}")
        raise e


def update_embeddings_in_batch(sections):
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
            print(f"Batch Completed. Batch size  {len(batch_queue)} Token count {token_count}")
            for emb, item in zip(emb_responses, batch_queue):
                batch_response[item["id"]] = emb
            batch_queue = []
            batch_queue.append(s)
            token_count = calculate_tokens_emb_aoai(s["content"])

    if batch_queue:
        emb_responses = compute_embedding_in_batch([item["content"] for item in batch_queue])
        print(f"Batch Completed. Batch size  {len(batch_queue)} Token count {token_count}")
        for emb, item in zip(emb_responses, batch_queue):
            batch_response[item["id"]] = emb

    for s in copy_s:
        s["embedding"] = batch_response[s["id"]]
        yield s


async def index_sections(
    filename,
    sections,
    search_creds,
    acls=None,
):
    search_client = await get_search_client()

    try:
        AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

        print(f"Indexing sections from '{filename}' into search index '{AZURE_SEARCH_INDEX}'")

        if not search_creds:
            raise Exception("Search credentials not provided")

        i = 0
        batch = []
        for s in sections:
            if acls:
                s.update(acls)
            batch.append(s)
            i += 1
            if i % 1000 == 0:
                results = await search_client.upload_documents(documents=batch)
                succeeded = sum([1 for r in results if r.succeeded])
                print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
                batch = []

        if len(batch) > 0:
            results = await search_client.upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
    finally:
        await search_client.close()
        print("Done indexing sections")


async def remove_from_index(filename, search_creds):
    if not search_creds:
        raise Exception("Search credentials not provided")

    search_client = await get_search_client()

    try:
        logging.info(f"Removing sections from '{filename or '<all>'}' from search index")

        while True:
            filter = f"sourcefile eq '{filename}'"
            search_results = await search_client.search(search_text="", filter=filter, select=["id"])

            docs = []
            async for doc in search_results:
                docs.append(doc)

            if len(docs) == 0:
                break

            await search_client.delete_documents(documents=docs)
            print("Removed  sections from index")
            # It can take a few seconds for search results to reflect changes, so wait a bit
            time.sleep(2)
    except Exception as e:
        print(f"Error removing sections from index: {e}")
    finally:
        await search_client.close()
        print("Done removing sections from index")


def refresh_openai_token():
    """
    Refresh OpenAI token every 5 minutes
    """
    if (
        CACHE_KEY_TOKEN_TYPE in open_ai_token_cache
        and open_ai_token_cache[CACHE_KEY_TOKEN_TYPE] == "azure_ad"
        and open_ai_token_cache[CACHE_KEY_CREATED_TIME] + 300 < time.time()
    ):
        token_cred = open_ai_token_cache[CACHE_KEY_TOKEN_CRED]
        openai.api_key = token_cred.get_token("https://cognitiveservices.azure.com/.default").token
        open_ai_token_cache[CACHE_KEY_CREATED_TIME] = time.time()
