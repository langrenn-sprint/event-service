"""Module for ageclass adapter."""
import logging
from typing import Any, List, Optional

from .adapter import Adapter


class AgeclassesAdapter(Adapter):
    """Class representing an adapter for ageclasses."""

    @classmethod
    async def get_all_ageclasses(
        cls: Any, db: Any, event_id: str
    ) -> List:  # pragma: no cover
        """Get all ageclasses function."""
        ageclasses: List = []
        cursor = db.ageclasses_collection.find({"event_id": event_id})
        for ageclass in await cursor.to_list(length=100):
            ageclasses.append(ageclass)
            logging.debug(ageclass)
        return ageclasses

    @classmethod
    async def create_ageclass(
        cls: Any, db: Any, event_id: str, ageclass: dict
    ) -> str:  # pragma: no cover
        """Create ageclass function."""
        result = await db.ageclasses_collection.insert_one(ageclass)
        return result

    @classmethod
    async def get_ageclass_by_id(
        cls: Any, db: Any, event_id: str, ageclass_id: str
    ) -> dict:  # pragma: no cover
        """Get ageclass by id function."""
        result = await db.ageclasses_collection.find_one(
            {"$and": [{"event_id": event_id}, {"id": ageclass_id}]}
        )
        return result

    @classmethod
    async def get_ageclass_by_name(
        cls: Any, db: Any, event_id: str, name: str
    ) -> dict:  # pragma: no cover
        """Get ageclass by name function."""
        result = await db.ageclasses_collection.find_one(
            {
                "$and": [
                    {"event_id": event_id},
                    {"name": name},
                ]
            }
        )
        return result

    @classmethod
    async def update_ageclass(
        cls: Any, db: Any, event_id: str, ageclass_id: str, ageclass: dict
    ) -> Optional[str]:  # pragma: no cover
        """Update given ageclass function."""
        result = await db.ageclasses_collection.replace_one(
            {"$and": [{"event_id": event_id}, {"id": ageclass_id}]}, ageclass
        )
        return result

    @classmethod
    async def delete_ageclass(
        cls: Any, db: Any, event_id: str, ageclass_id: str
    ) -> Optional[str]:  # pragma: no cover
        """Delete given ageclass function."""
        result = await db.ageclasses_collection.delete_one(
            {"$and": [{"event_id": event_id}, {"id": ageclass_id}]}
        )
        return result

    @classmethod
    async def delete_all_ageclasses(
        cls: Any, db: Any, event_id: str
    ) -> Optional[str]:  # pragma: no cover
        """Delete all ageclasses function."""
        result = await db.ageclasses_collection.delete_many({"event_id": event_id})
        return result
