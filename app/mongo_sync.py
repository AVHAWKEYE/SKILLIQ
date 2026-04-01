"""MongoDB Atlas sync helpers for mirroring SQL data."""

import json
import logging
import os
from datetime import datetime
from typing import Iterable, Optional

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from sqlalchemy.orm import Session

from . import models

LOGGER = logging.getLogger(__name__)

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://prat:1234@cluster0.mn8unfr.mongodb.net/?appName=Cluster0",
)
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "skilliq")

_mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGODB_URI, server_api=ServerApi("1"))
    return _mongo_client


def get_mongo_db():
    return get_mongo_client()[MONGODB_DB_NAME]


def ping_mongo() -> bool:
    try:
        get_mongo_client().admin.command("ping")
        return True
    except Exception as exc:  # pragma: no cover - connectivity depends on runtime
        LOGGER.warning("Mongo ping failed: %s", exc)
        return False


def _try_parse_json(value):
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if (text.startswith("{") and text.endswith("}")) or (
        text.startswith("[") and text.endswith("]")
    ):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def sqlalchemy_to_doc(instance) -> dict:
    doc = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            doc[column.name] = value
            continue
        doc[column.name] = _try_parse_json(value)
    return doc


def upsert_instance(collection_name: str, instance, key_field: str = "id") -> None:
    doc = sqlalchemy_to_doc(instance)
    key_value = doc.get(key_field)
    if key_value is None:
        return
    get_mongo_db()[collection_name].update_one(
        {key_field: key_value},
        {"$set": doc},
        upsert=True,
    )


def upsert_instances(collection_name: str, instances: Iterable, key_field: str = "id") -> None:
    collection = get_mongo_db()[collection_name]
    for instance in instances:
        doc = sqlalchemy_to_doc(instance)
        key_value = doc.get(key_field)
        if key_value is None:
            continue
        collection.update_one(
            {key_field: key_value},
            {"$set": doc},
            upsert=True,
        )


def delete_instance(collection_name: str, key_value, key_field: str = "id") -> None:
    get_mongo_db()[collection_name].delete_one({key_field: key_value})


def replace_collection(collection_name: str, instances: Iterable, key_field: str = "id") -> int:
    collection = get_mongo_db()[collection_name]
    docs = []
    for instance in instances:
        doc = sqlalchemy_to_doc(instance)
        if doc.get(key_field) is None:
            continue
        docs.append(doc)

    collection.delete_many({})
    if docs:
        collection.insert_many(docs)
    return len(docs)


def full_sync_from_sql(db: Session) -> dict:
    counts = {}
    counts["users"] = replace_collection("users", db.query(models.User).all())
    counts["assessments"] = replace_collection("assessments", db.query(models.Assessment).all())
    counts["tests"] = replace_collection("tests", db.query(models.Test).all())
    counts["test_questions"] = replace_collection("test_questions", db.query(models.TestQuestion).all())
    counts["test_attempts"] = replace_collection("test_attempts", db.query(models.TestAttempt).all())
    counts["learning_resources"] = replace_collection(
        "learning_resources", db.query(models.LearningResource).all()
    )
    counts["ai_insights"] = replace_collection("ai_insights", db.query(models.AIInsight).all())
    counts["performance_metrics"] = replace_collection(
        "performance_metrics", db.query(models.PerformanceMetric).all()
    )
    return counts


def safe_sync(callable_sync, *args, **kwargs):
    try:
        if not ping_mongo():
            return None
        return callable_sync(*args, **kwargs)
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        LOGGER.warning("Mongo sync failed: %s", exc)
        return None
