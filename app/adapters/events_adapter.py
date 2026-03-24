"""Module for event adapter."""

import logging
from typing import Any
from uuid import UUID

from app.models import Event


class EventsAdapter:
    """Class representing an adapter for events."""

    database: Any
    logger = logging.Logger

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database
        cls.logger = logging.getLogger("uvicorn.error")

    @classmethod
    async def get_all_events(cls: Any) -> list[Event]:  # pragma: no cover
        """Get all events function."""
        cursor = cls.database.events_collection.find().sort([("id", 1)])
        return [Event.model_validate(event) for event in await cursor.to_list(None)]

    @classmethod
    async def create_event(cls: Any, event: Event) -> str:  # pragma: no cover
        """Create event function."""
        return await cls.database.events_collection.insert_one(event.model_dump())

    @classmethod
    async def get_event_by_id(
        cls: Any, event_id: UUID
    ) -> Event | None:  # pragma: no cover
        """Get event by id function."""
        result = await cls.database.events_collection.find_one({"id": event_id})
        if result:
            return Event.model_validate(result)
        return None

    @classmethod
    async def update_event(
        cls: Any, event_id: UUID, event: Event
    ) -> str | None:  # pragma: no cover
        """Replace event function."""
        return await cls.database.events_collection.replace_one(
            {"id": event_id}, event.model_dump()
        )

    @classmethod
    async def delete_event(cls: Any, event_id: UUID) -> str | None:  # pragma: no cover
        """Delete event function."""
        return await cls.database.events_collection.delete_one({"id": event_id})
