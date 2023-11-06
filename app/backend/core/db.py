import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

db_client: AsyncIOMotorClient = None


async def get_db() -> AsyncIOMotorClient:
    return db_client["ki-prototype"]


async def connect_and_init_db():
    AZURE_MONGODB = os.getenv("AZURE_MONGODB")

    global db_client
    try:
        db_client = AsyncIOMotorClient(AZURE_MONGODB)
        logging.info("Connected to mongo.")
    except Exception as e:
        logging.exception(f"Could not connect to mongo: {e}")
        raise


async def close_db_connect():
    global db_client
    if db_client is None:
        logging.warning("Connection is None, nothing to close.")
        return
    db_client.close()
    db_client = None
    logging.info("Mongo connection closed.")
