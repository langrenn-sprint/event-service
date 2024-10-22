"""Module for contestant adapter."""

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
        cursor = db.contestants_collection.find({"event_id": event_id}).sort(
            [("id", 1)]
        )
        for contestant in await cursor.to_list(None):  # we ask for all contestants
            contestants.append(contestant)
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
        """Get contestant by id function."""
        result = await db.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}
        )
        return result

    @classmethod
    async def get_contestant_by_name(
        cls: Any, db: Any, event_id: str, first_name: str, last_name: str
    ) -> dict:  # pragma: no cover
        """Get contestant by name function."""
        result = await db.contestants_collection.find_one(
            {
                "$and": [
                    {"event_id": event_id},
                    {"first_name": first_name},
                    {"last_name": last_name},
                ]
            }
        )
        return result

    @classmethod
    async def get_contestant_by_bib(
        cls: Any, db: Any, event_id: str, bib: int
    ) -> dict:  # pragma: no cover
        """Get contestant by bib function."""
        result = await db.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"bib": bib}]}
        )
        return result

    @classmethod
    async def get_contestant_by_minidrett_id(
        cls: Any, db: Any, event_id: str, minidrett_id: str
    ) -> dict:  # pragma: no cover
        """Get contestant by minidrett_id function."""
        result = await db.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"minidrett_id": minidrett_id}]}
        )
        return result

    @classmethod
    async def update_contestant(
        cls: Any, db: Any, event_id: str, contestant_id: str, contestant: dict
    ) -> Optional[str]:  # pragma: no cover
        """Update given contestant function."""
        result = await db.contestants_collection.replace_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}, contestant
        )
        return result

    @classmethod
    async def delete_contestant(
        cls: Any, db: Any, event_id: str, contestant_id: str
    ) -> Optional[str]:  # pragma: no cover
        """Delete given contestant function."""
        result = await db.contestants_collection.delete_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}
        )
        return result

    @classmethod
    async def delete_all_contestants(
        cls: Any, db: Any, event_id: str
    ) -> Optional[str]:  # pragma: no cover
        """Delete all contestant function."""
        result = await db.contestants_collection.delete_many({"event_id": event_id})
        return result

    @classmethod
    async def search_contestants_in_event_by_name(
        cls: Any, db: Any, event_id: str, name: str
    ) -> List[dict]:  # pragma: no cover
        """Perform text-search after contestants function."""
        list: List[dict] = []
        _result = db.contestants_collection.find(
            {"$and": [{"event_id": event_id}, {"$text": {"$search": f"{name}"}}]}
        ).sort([("bib", 1)])
        for contestant in await _result.to_list(None):  # we ask for all contestants
            list.append(contestant)
        return list
