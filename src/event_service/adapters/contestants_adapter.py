"""Module for contestant adapter."""
import logging
from typing import Any, List, Optional

from .adapter import Adapter


class ContestantsAdapter(Adapter):
    """Class representing an adapter for contestants."""

    @classmethod
    async def get_all_contestants(cls: Any, db: Any) -> List:  # pragma: no cover
        """Get all contestants function."""
        contestants: List = []
        cursor = db.contestants_collection.find()
        for contestant in await cursor.to_list(length=100):
            contestants.append(contestant)
            logging.debug(contestant)
        return contestants

    @classmethod
    async def create_contestant(
        cls: Any, db: Any, contestant: dict
    ) -> str:  # pragma: no cover
        """Create contestant function."""
        result = await db.contestants_collection.insert_one(contestant)
        return result

    @classmethod
    async def get_contestant_by_id(
        cls: Any, db: Any, id: str
    ) -> dict:  # pragma: no cover
        """Get contestant function."""
        result = await db.contestants_collection.find_one({"id": id})
        return result

    @classmethod
    async def get_contestant_by_name(
        cls: Any, db: Any, contestantname: str
    ) -> dict:  # pragma: no cover
        """Get contestant function."""
        result = await db.contestants_collection.find_one(
            {"contestantname": contestantname}
        )
        return result

    @classmethod
    async def update_contestant(
        cls: Any, db: Any, id: str, contestant: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get contestant function."""
        result = await db.contestants_collection.replace_one({"id": id}, contestant)
        return result

    @classmethod
    async def delete_contestant(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get contestant function."""
        result = await db.contestants_collection.delete_one({"id": id})
        return result
