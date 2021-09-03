"""Module for contestant adapter."""
import logging
from typing import Any, List, Optional

from .adapter import Adapter


class ContestantsAdapter(Adapter):
    """Class representing an adapter for contestants."""

    @classmethod
    async def get_all_contestants(
        cls: Any, db: Any, event_id: str
    ) -> List:  # pragma: no cover
        """Get all contestants function."""
        contestants: List = []
        cursor = db.contestants_collection.find({"event_id": event_id})
        for contestant in await cursor.to_list(length=100):
            contestants.append(contestant)
            logging.debug(contestant)
        return contestants

    @classmethod
    async def create_contestant(
        cls: Any, db: Any, event_id: str, contestant: dict
    ) -> str:  # pragma: no cover
        """Create contestant function."""
        result = await db.contestants_collection.insert_one(contestant)
        return result

    @classmethod
    async def get_contestant_by_id(
        cls: Any, db: Any, event_id: str, contestant_id: str
    ) -> dict:  # pragma: no cover
        """Get contestant in given event function."""
        result = await db.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}
        )
        return result

    @classmethod
    async def get_contestant_by_name(
        cls: Any, db: Any, event_id: str, contestantname: str
    ) -> dict:  # pragma: no cover
        """Get contestant function."""
        result = await db.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"contestantname": contestantname}]}
        )
        return result

    @classmethod
    async def update_contestant(
        cls: Any, db: Any, event_id: str, contestant_id: str, contestant: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get contestant function."""
        result = await db.contestants_collection.replace_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}, contestant
        )
        return result

    @classmethod
    async def delete_contestant(
        cls: Any, db: Any, event_id: str, contestant_id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get contestant function."""
        result = await db.contestants_collection.delete_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}
        )
        return result
