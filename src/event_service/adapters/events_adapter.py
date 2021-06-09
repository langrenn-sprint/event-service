"""Module for event adapter."""
import logging
from typing import Any, List, Optional
import uuid


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class EventsAdapter:
    """Class representing an adapter for events."""

    @classmethod
    async def get_all_events(cls: Any, db: Any) -> List:
        """Get all events function."""
        events: List = []
        cursor = db.events_collection.find()
        for event in await cursor.to_list(length=100):
            events.append(event)
            logging.debug(event)
        return events

    @classmethod
    async def create_event(cls: Any, db: Any, event: dict) -> Optional[str]:
        """Create event function."""
        # create id
        id = create_id()
        event["id"] = id
        # insert new event
        result = await db.events_collection.insert_one(event)
        logging.debug(f"inserted event with id: {id}")
        if result:
            return id
        return None  # pragma: no cover

    @classmethod
    async def get_event(cls: Any, db: Any, id: str) -> Optional[dict]:
        """Get event function."""
        # insert new
        result = await db.events_collection.find_one({"id": id})
        # return the document if found:
        if result:
            return result
        return None

    @classmethod
    async def update_event(cls: Any, db: Any, id: str, event: dict) -> Optional[str]:
        """Get event function."""
        # get old document
        old_document = await db.events_collection.find_one({"id": id})
        # update the document if found:
        if old_document:
            _ = await db.events_collection.replace_one({"id": id}, event)
            return id
        return None

    @classmethod
    async def delete_event(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get event function."""
        # get old document
        document = await db.events_collection.find_one({"id": id})
        # delete the document if found:
        if document:
            _ = await db.events_collection.delete_one({"id": id})
            return id
        return None
