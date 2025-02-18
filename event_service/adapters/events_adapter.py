"""Module for event adapter."""

from typing import Any

from .adapter import Adapter


class EventsAdapter(Adapter):
    """Class representing an adapter for events."""

    @classmethod
    async def get_all_events(cls: Any, db: Any) -> list:  # pragma: no cover
        """Get all events function."""
        events: list = []
        cursor = db.events_collection.find().sort([("id", 1)])
        for event in await cursor.to_list(None):
            events.append(event)  # noqa: PERF402
        return events

    @classmethod
    async def create_event(cls: Any, db: Any, event: dict) -> str:  # pragma: no cover
        """Create event function."""
        return await db.events_collection.insert_one(event)

    @classmethod
    async def get_event_by_id(
        cls: Any, db: Any, event_id: str
    ) -> dict:  # pragma: no cover
        """Get event function."""
        return await db.events_collection.find_one({"id": event_id})

    @classmethod
    async def get_event_by_name(
        cls: Any, db: Any, event_name: str
    ) -> dict:  # pragma: no cover
        """Get event function."""
        return await db.events_collection.find_one({"eventname": event_name})

    @classmethod
    async def update_event(
        cls: Any, db: Any, event_id: str, event: dict
    ) -> str | None:  # pragma: no cover
        """Get event function."""
        return await db.events_collection.replace_one({"id": event_id}, event)

    @classmethod
    async def delete_event(
        cls: Any, db: Any, event_id: str
    ) -> str | None:  # pragma: no cover
        """Get event function."""
        return await db.events_collection.delete_one({"id": event_id})
