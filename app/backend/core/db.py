import os
from pymongo import MongoClient, ASCENDING
from core.logger import logger

db_client: MongoClient = None


def get_db():
    return db_client["ki-prototype"]


def connect_and_init_db():
    AZURE_MONGODB = os.getenv("AZURE_MONGODB")

    global db_client
    try:
        db_client = MongoClient(AZURE_MONGODB, serverSelectionTimeoutMS=5000)
        logger.info("Connected to mongo")

        if "documents" not in db_client["ki-prototype"].list_collection_names():
            db_client["ki-prototype"].create_collection("documents")

        db_client["ki-prototype"]["documents"].create_index([("$**", ASCENDING)])

        return db_client["ki-prototype"]
    except Exception as e:
        logger.exception(f"Could not connect to mongo: {e}")
        raise


def close_db_connect():
    global db_client
    if db_client is None:
        logger.warning("Connection is None, nothing to close.")
        return
    db_client.close()
    db_client = None
    logger.info("Mongo connection closed")
