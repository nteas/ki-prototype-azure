import os
import logging
from pymongo import MongoClient
import pymongo


async def get_db() -> MongoClient:
    AZURE_MONGODB = os.getenv("AZURE_MONGODB")

    global db_client
    try:
        db_client = MongoClient(AZURE_MONGODB, serverSelectionTimeoutMS=5000)
        logging.info("Connected to mongo.")

        if "documents" not in db_client["ki-prototype"].list_collection_names():
            db_client["ki-prototype"].create_collection("documents")

        db_client["ki-prototype"]["documents"].create_index([("$**", pymongo.ASCENDING)])

        yield db_client["ki-prototype"]
    except Exception as e:
        logging.exception(f"Could not connect to mongo: {e}")
        raise
    finally:
        await db_client.close()
        logging.info("Mongo connection closed.")
