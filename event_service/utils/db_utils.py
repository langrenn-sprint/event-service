"""Drop db and recreate indexes."""
from typing import Any


async def drop_db_and_recreate_indexes(mongo: Any, db_name: str) -> None:
    """Drop db and recreate indexes."""
    await drop_db(mongo, db_name)

    db = mongo[f"{db_name}"]
    await create_indexes(db)


async def drop_db(mongo: Any, db_name: str) -> None:
    """Drop db."""
    await mongo.drop_database(f"{db_name}")


async def create_indexes(db: Any) -> None:
    """Create indexes."""
    # contestants_collection:
    await db.contestants_collection.create_index(
        [("event_id", 1), ("first_name", "text"), ("last_name", "text")],
        default_language="norwegian",
    )
    await db.contestants_collection.create_index(
        [("event_id", 1), ("id", 1)], unique=True
    )
    await db.contestants_collection.create_index([("event_id", 1), ("bib", 1)])
    await db.contestants_collection.create_index([("event_id", 1), ("minidrett_id", 1)])

    # events_collection:
    await db.events_collection.create_index([("id", 1)], unique=True)

    # raceclasses_collection:
    await db.raceclasses_collection.create_index(
        [("event_id", 1), ("id", 1)], unique=True
    )
    await db.raceclasses_collection.create_index([("event_id", 1), ("name", 1)])

    # raceclass_results_collection:
    await db.raceclass_results_collection.create_index(
        [("event_id", 1), ("id", 1)], unique=True
    )
    await db.raceclass_results_collection.create_index(
        [("event_id", 1), ("raceclass", 1)]
    )
