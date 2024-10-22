"""Module for event_format adapter."""

from typing import Any, Optional

from .adapter import Adapter


class EventFormatAdapter(Adapter):
    """Class representing an adapter for event_format."""

    @classmethod
    async def create_event_format(
        cls: Any, db: Any, event_id: str, event_format: dict
    ) -> str:  # pragma: no cover
        """Create event_format function."""
        result = await db.event_format_collection.insert_one(event_format)
        return result

    @classmethod
    async def get_event_format(
        cls: Any, db: Any, event_id: str
    ) -> dict:  # pragma: no cover
        """Get event_format function."""
        result = await db.event_format_collection.find_one()
        return result

    @classmethod
    async def update_event_format(
        cls: Any, db: Any, event_id: str, event_format: dict
    ) -> Optional[str]:  # pragma: no cover
        """Update given event_format function."""
        result = await db.event_format_collection.replace_one({}, event_format)
        return result

    @classmethod
    async def delete_event_format(
        cls: Any, db: Any, event_id: str
    ) -> Optional[str]:  # pragma: no cover
        """Delete given event_format function."""
        result = await db.event_format_collection.delete_one({})
        return result
