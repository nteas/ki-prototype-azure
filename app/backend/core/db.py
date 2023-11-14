import os
import logging
from pymongo import MongoClient

db_client: MongoClient = None


def get_db() -> MongoClient:
    return db_client["ki-prototype"]


def connect_and_init_db():
    AZURE_MONGODB = os.getenv("AZURE_MONGODB")

    global db_client
    try:
        db_client = MongoClient(AZURE_MONGODB, serverSelectionTimeoutMS=5000)
        logging.info("Connected to mongo.")

        if "documents" not in db_client["ki-prototype"].list_collection_names():
            db_client["ki-prototype"].create_collection("documents")
    except Exception as e:
        logging.exception(f"Could not connect to mongo: {e}")
        raise


def close_db_connect():
    global db_client
    if db_client is None:
        logging.warning("Connection is None, nothing to close.")
        return
    db_client.close()
    db_client = None
    logging.info("Mongo connection closed.")
