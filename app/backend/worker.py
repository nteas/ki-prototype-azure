import datetime
import openai
import os
import logging

from core.types import Frequency, Log
from core.db import get_db
from core.utilities import (
    hash_text_md5,
    scrape_url,
    get_filename_from_url,
    create_sections_string,
    update_embeddings_in_batch,
    index_sections,
    remove_from_index,
)
from core.logger import logger
from azure.search.documents.aio import SearchClient
from azure.identity.aio import DefaultAzureCredential


async def worker():
    azure_credential = DefaultAzureCredential(logging_level=logging.ERROR)
    search_client = SearchClient(
        endpoint=f"https://{os.environ['AZURE_SEARCH_SERVICE']}.search.windows.net",
        index_name=os.environ["AZURE_SEARCH_INDEX"],
        credential=azure_credential,
    )

    try:
        AZURE_OPENAI_SERVICE = os.environ["AZURE_OPENAI_SERVICE"]
        openai_token = await azure_credential.get_token("https://cognitiveservices.azure.com/.default")
        openai.api_key = openai_token.token
        openai.api_type = "azure_ad"
        openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
        openai.api_version = "2023-07-01-preview"

        db = get_db()

        documents = []

        daily_docs = db.documents.find(
            {
                "type": "web",
                "frequency": Frequency.daily.value,
                "deleted": {"$ne": True},
            }
        )

        if daily_docs is None:
            print("No daily documents found")
        else:
            daily_docs = list(daily_docs)
            documents.extend(daily_docs)

        # check if today is monday
        if datetime.datetime.today().weekday() == 0:
            weekly_docs = db.documents.find(
                {
                    "type": "web",
                    "frequency": Frequency.weekly.value,
                    "deleted": {"$ne": True},
                }
            )

            if weekly_docs is None:
                print("No weekly documents found")
            else:
                weekly_docs = list(weekly_docs)
                documents.extend(weekly_docs)

        # check if today is the first of the month
        if datetime.datetime.today().day == 1:
            monthly_docs = db.documents.find(
                {
                    "type": "web",
                    "frequency": Frequency.monthly.value,
                    "deleted": {"$ne": True},
                }
            )

            if monthly_docs is None:
                print("No monthly documents found")
            else:
                monthly_docs = list(monthly_docs)
                documents.extend(monthly_docs)

        if len(documents) == 0:
            print("No documents found")
            raise Exception("No documents found")

        # make sure documents contain unique documents
        documents = list({v["id"]: v for v in documents}.values())

        print(f"Found {len(documents)} documents")

        for document in documents:
            logger.info("Getting content from url")

            url = document["url"]

            if url is None:
                continue

            text = await scrape_url(url, search_client)

            hashed_text = hash_text_md5(text)

            if document["hash"] == hashed_text:
                continue

            await remove_from_index(document["file"], search_client)

            pages = list(
                create_sections_string(
                    url,
                    text,
                )
            )

            sections = update_embeddings_in_batch(pages)

            filename = get_filename_from_url(url)
            await index_sections(filename, sections, search_client)

            user = "worker"
            change = "scraped"
            message = "Data lastet inn og oppdatert"
            log = Log(user=user, change=change, message=message)

            db.documents.update_one(
                {"id": document["id"]},
                {
                    "$set": {"hash": hashed_text},
                    "$push": {"logs": log.model_dump()},
                },
            )

            logger.info("Got content from url")

    except Exception as e:
        print(e)
    finally:
        await azure_credential.close()
