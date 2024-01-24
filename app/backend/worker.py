import datetime

from core.types import Frequency, Log
from core.db import get_db
from core.openai_agent import index_web_document
from core.logger import logger


def worker():
    try:
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
            index_web_document(document["id"], document["urls"])

            user = "worker"
            change = "scraped"
            message = "Data lastet inn og oppdatert"
            log = Log(user=user, change=change, message=message)

            db.documents.update_one(
                {"id": document["id"]},
                {
                    "$push": {"logs": log.model_dump()},
                },
            )

    except Exception as e:
        logger.exception(e)
