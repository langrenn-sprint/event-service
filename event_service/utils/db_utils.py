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
