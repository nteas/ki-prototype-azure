import os
import logging
import pymongo


def get_mongodb_client():
    AZURE_MONGODB = os.getenv("AZURE_MONGODB")
    CONFIG_DB_NAME = "ki-prototype"

    """Set up MongoDB client and make it available to the app."""
    if not AZURE_MONGODB:
        logging.error("Missing AZURE_MONGODB environment variable.")
        return

    try:
        mongodb_client = pymongo.MongoClient(AZURE_MONGODB)
        db = mongodb_client[CONFIG_DB_NAME]
        if CONFIG_DB_NAME not in mongodb_client.list_database_names():
            # Create a database with 400 RU throughput that can be shared across
            # the DB's collections
            db.command({"customAction": "CreateDatabase", "offerThroughput": 400})
            logging.info(f"Created db '{CONFIG_DB_NAME}' with shared throughput.")
        else:
            logging.info(f"Using database: '{CONFIG_DB_NAME}'.")
        return db
    except pymongo.errors.ConnectionFailure:
        logging.error(f"Failed to connect to MongoDB at {AZURE_MONGODB}")
        return None
