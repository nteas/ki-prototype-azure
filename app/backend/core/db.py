import os
import logging
import pymongo


def get_db():
    mongodb_client: None
    AZURE_MONGODB = os.getenv("AZURE_MONGODB")
    try:
        mongodb_client = pymongo.MongoClient(AZURE_MONGODB)
        logging.info("Connected to mongo.")
        yield mongodb_client["ki-prototype"]
    except pymongo.errors.ConnectionFailure:
        logging.error("Failed to connect to MongoDB at %s", AZURE_MONGODB)
        mongodb_client = None
        raise
    finally:
        logging.info("Closing mongo connection.")
        mongodb_client.close()
        mongodb_client = None
