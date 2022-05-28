import logging

import dotenv
from pymongo import MongoClient, UpdateOne

config = dotenv.dotenv_values()
logger = logging.getLogger(__name__)


def bulk_update(requests):
    logger.warning(f"Saving {len(requests)} objects")
    return get_collection().bulk_write(requests)


def get_collection():
    return MongoClient(
        host=config["CHALLONGE_DATABASE_URL"]
    )[config["CHALLONGE_DATABASE_NAME"]]["matches"]


def get_many(order_by=None, how=-1, **kwargs):
    result = get_collection().find(kwargs)
    if order_by:
        return result.sort(order_by, how)
    return result


def get_stats(**kwargs):
    if not kwargs:
        raise ValueError("filter kwargs required")
    stats = get_collection().find_one(kwargs)
    if stats:
        stats.pop("_id")
    return stats


def filter_by_ids(ids):
    return list(get_collection().find({"id": {"$in": ids}}, sort=[("id", 1)]))


def set_stats(stats, commit=True, **filter_kwargs):
    if not filter_kwargs:
        raise ValueError("filter kwargs required")

    update_params = {
        "filter": filter_kwargs,
        "update": {"$set": stats},
        "upsert": True,
    }
    if not commit:
        return UpdateOne(**update_params)

    return get_collection().update_one(**update_params)
