import os
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection


MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://arquisoft:arquisoft@mongo:27017/promociones?authSource=admin",
)
MONGO_DB = os.getenv("MONGO_DB", "promociones")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "promociones")


client: MongoClient[dict[str, Any]] = MongoClient(MONGO_URI)


def promociones_collection() -> Collection[dict[str, Any]]:
    return client[MONGO_DB][MONGO_COLLECTION]
