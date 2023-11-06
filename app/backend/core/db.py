import os
import logging
from pymongo import MongoClient


def get_db() -> MongoClient:
    db_client: MongoClient = None
    AZURE_MONGODB = os.getenv("AZURE_MONGODB")
    try:
        logging.info("Connected to mongo.")
        db_client = MongoClient(AZURE_MONGODB)
        yield db_client["ki-prototype"]
    except Exception as e:
        logging.exception(f"Could not connect to mongo: {e}")
        raise
    finally:
        logging.info("Closing mongo connection.")
        db_client.close()
        db_client = None
