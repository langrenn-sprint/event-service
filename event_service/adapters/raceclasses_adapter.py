"""Module for raceclass adapter."""
from typing import Any, List, Optional

from .adapter import Adapter


class RaceclassesAdapter(Adapter):
    """Class representing an adapter for raceclasses."""

    @classmethod
    async def get_all_raceclasses(
        cls: Any, db: Any, event_id: str
    ) -> List[dict]:  # pragma: no cover
        """Get all raceclasses function."""
        raceclasses: List = []
        cursor = db.raceclasses_collection.find({"event_id": event_id})
        for raceclass in await cursor.to_list(None):
            raceclasses.append(raceclass)
        return raceclasses

    @classmethod
    async def create_raceclass(
        cls: Any, db: Any, event_id: str, raceclass: dict
    ) -> str:  # pragma: no cover
        """Create raceclass function."""
        result = await db.raceclasses_collection.insert_one(raceclass)
        return result

    @classmethod
    async def get_raceclass_by_id(
        cls: Any, db: Any, event_id: str, raceclass_id: str
    ) -> dict:  # pragma: no cover
        """Get raceclass by id function."""
        result = await db.raceclasses_collection.find_one(
            {"$and": [{"event_id": event_id}, {"id": raceclass_id}]}
        )
        return result

    @classmethod
    async def get_raceclass_by_name(
        cls: Any, db: Any, event_id: str, name: str
    ) -> List[dict]:  # pragma: no cover
        """Get raceclass by name function."""
        raceclasses: List = []
        cursor = db.raceclasses_collection.find(
            {
                "$and": [
                    {"event_id": event_id},
                    {"name": name},
                ]
            }
        )
        for raceclass in await cursor.to_list(None):
            raceclasses.append(raceclass)
        return raceclasses

    @classmethod
    async def update_raceclass(
        cls: Any, db: Any, event_id: str, raceclass_id: str, raceclass: dict
    ) -> Optional[str]:  # pragma: no cover
        """Update given raceclass function."""
        result = await db.raceclasses_collection.replace_one(
            {"$and": [{"event_id": event_id}, {"id": raceclass_id}]}, raceclass
        )
        return result

    @classmethod
    async def delete_raceclass(
        cls: Any, db: Any, event_id: str, raceclass_id: str
    ) -> Optional[str]:  # pragma: no cover
        """Delete given raceclass function."""
        result = await db.raceclasses_collection.delete_one(
            {"$and": [{"event_id": event_id}, {"id": raceclass_id}]}
        )
        return result

    @classmethod
    async def delete_all_raceclasses(
        cls: Any, db: Any, event_id: str
    ) -> Optional[str]:  # pragma: no cover
        """Delete all raceclasses function."""
        result = await db.raceclasses_collection.delete_many({"event_id": event_id})
        return result
