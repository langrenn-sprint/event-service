"""Module for event adapter."""
import logging
from typing import Any, List, Optional

from .adapter import Adapter


class EventsAdapter(Adapter):
    """Class representing an adapter for events."""

    @classmethod
    async def get_all_events(cls: Any, db: Any) -> List:  # pragma: no cover
        """Get all events function."""
        events: List = []
        cursor = db.events_collection.find()
        for event in await cursor.to_list(None):
            events.append(event)
            logging.debug(event)
        return events

    @classmethod
    async def create_event(cls: Any, db: Any, event: dict) -> str:  # pragma: no cover
        """Create event function."""
        result = await db.events_collection.insert_one(event)
        return result

    @classmethod
    async def get_event_by_id(cls: Any, db: Any, id: str) -> dict:  # pragma: no cover
        """Get event function."""
        result = await db.events_collection.find_one({"id": id})
        return result

    @classmethod
    async def get_event_by_name(
        cls: Any, db: Any, eventname: str
    ) -> dict:  # pragma: no cover
        """Get event function."""
        result = await db.events_collection.find_one({"eventname": eventname})
        return result

    @classmethod
    async def update_event(
        cls: Any, db: Any, id: str, event: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get event function."""
        result = await db.events_collection.replace_one({"id": id}, event)
        return result

    @classmethod
    async def delete_event(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get event function."""
        result = await db.events_collection.delete_one({"id": id})
        return result
