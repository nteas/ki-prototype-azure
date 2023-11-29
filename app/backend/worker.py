import datetime

from core.db import get_db


def worker():
    try:
        db = get_db()

        documents = db.documents.find(
            {
                "type": "web",
                "deleted": {"$ne": True},
            }
        ).to_list(length=1000)

        if documents is None:
            print("No documents found")
            return

        print(f"Found {len(documents)} documents")

        for document in documents:
            print(document.get("title"))

        print("Tick! The time is: %s" % datetime.datetime.now())
    except Exception as e:
        print(e)
