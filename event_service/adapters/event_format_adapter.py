"""Module for event_format adapter."""

from typing import Any

from .adapter import Adapter


class EventFormatAdapter(Adapter):
    """Class representing an adapter for event_format."""

    database: Any

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database

    @classmethod
    async def create_event_format(
        cls: Any, event_id: str, event_format: dict
    ) -> str:  # pragma: no cover
        """Create event_format function."""
        _ = event_id
        return await cls.database.event_format_collection.insert_one(event_format)

    @classmethod
    async def get_event_format(cls: Any, event_id: str) -> dict:  # pragma: no cover
        """Get event_format function."""
        _ = event_id
        return await cls.database.event_format_collection.find_one()

    @classmethod
    async def update_event_format(
        cls: Any, event_id: str, event_format: dict
    ) -> str | None:  # pragma: no cover
        """Update given event_format function."""
        _ = event_id
        return await cls.database.event_format_collection.replace_one({}, event_format)

    @classmethod
    async def delete_event_format(
        cls: Any, event_id: str
    ) -> str | None:  # pragma: no cover
        """Delete given event_format function."""
        _ = event_id
        return await cls.database.event_format_collection.delete_one({})
