import datetime
import openai
import os

from core.types import Log
from core.db import get_db
from core.utilities import scrape_store_index
from core.context import get_azure_credential, logger, get_blob_container_client


async def worker():
    azure_credential = get_azure_credential()
    blob_container_client = await get_blob_container_client()

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
                "frequency": "daily",
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
                    "frequency": "weekly",
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
                    "frequency": "monthly",
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

            filename = document["file"]

            file_pages = await scrape_store_index(filename, url, blob_container_client)

            user = "worker"
            change = "scraped"
            message = "Data lastet inn og oppdatert"
            log = Log(user=user, change=change, message=message)

            db.documents.update_one(
                {"id": document["id"]},
                {
                    "$set": {
                        "file_pages": file_pages,
                    },
                    "$push": {"logs": log.model_dump()},
                },
            )

            logger.info("Got content from url")

        print("Tick! The time is: %s" % datetime.datetime.now())
    except Exception as e:
        print(e)
    finally:
        await blob_container_client.close()
        await azure_credential.close()