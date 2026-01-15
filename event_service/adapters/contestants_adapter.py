"""Module for contestant adapter."""

from typing import Any

from .adapter import Adapter


class ContestantsAdapter(Adapter):
    """Class representing an adapter for contestants."""

    database: Any

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database

    @classmethod
    async def get_all_contestants(cls: Any, event_id: str) -> list:  # pragma: no cover
        """Get all contestants function."""
        contestants: list = []
        cursor = cls.database.contestants_collection.find({"event_id": event_id}).sort(
            [("id", 1)]
        )
        for contestant in await cursor.to_list(None):  # we ask for all contestants
            contestants.append(contestant)  # noqa: PERF402
        return contestants

    @classmethod
    async def create_contestant(
        cls: Any, event_id: str, contestant: dict
    ) -> str:  # pragma: no cover
        """Create contestant function."""
        _ = event_id
        return await cls.database.contestants_collection.insert_one(contestant)

    @classmethod
    async def get_contestant_by_id(
        cls: Any, event_id: str, contestant_id: str
    ) -> dict:  # pragma: no cover
        """Get contestant by id function."""
        return await cls.database.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}
        )

    @classmethod
    async def get_contestant_by_name(
        cls: Any, event_id: str, first_name: str, last_name: str
    ) -> dict:  # pragma: no cover
        """Get contestant by name function."""
        return await cls.database.contestants_collection.find_one(
            {
                "$and": [
                    {"event_id": event_id},
                    {"first_name": first_name},
                    {"last_name": last_name},
                ]
            }
        )

    @classmethod
    async def get_contestant_by_bib(
        cls: Any, event_id: str, bib: int
    ) -> dict:  # pragma: no cover
        """Get contestant by bib function."""
        return await cls.database.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"bib": bib}]}
        )

    @classmethod
    async def get_contestant_by_minidrett_id(
        cls: Any, event_id: str, minidrett_id: str
    ) -> dict:  # pragma: no cover
        """Get contestant by minidrett_id function."""
        return await cls.database.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"minidrett_id": minidrett_id}]}
        )

    @classmethod
    async def update_contestant(
        cls: Any, event_id: str, contestant_id: str, contestant: dict
    ) -> str | None:  # pragma: no cover
        """Update given contestant function."""
        return await cls.database.contestants_collection.replace_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}, contestant
        )

    @classmethod
    async def delete_contestant(
        cls: Any, event_id: str, contestant_id: str
    ) -> str | None:  # pragma: no cover
        """Delete given contestant function."""
        return await cls.database.contestants_collection.delete_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}
        )

    @classmethod
    async def delete_all_contestants(
        cls: Any, event_id: str
    ) -> str | None:  # pragma: no cover
        """Delete all contestant function."""
        return await cls.database.contestants_collection.delete_many(
            {"event_id": event_id}
        )

    @classmethod
    async def search_contestants_in_event_by_name(
        cls: Any, event_id: str, name: str
    ) -> list[dict]:  # pragma: no cover
        """Perform text-search after contestants function."""
        contestants_list: list[dict] = []
        _result = cls.database.contestants_collection.find(
            {"$and": [{"event_id": event_id}, {"$text": {"$search": f"{name}"}}]}
        ).sort([("bib", 1)])
        for contestant in await _result.to_list(None):  # we ask for all contestants
            contestants_list.append(contestant)  # noqa: PERF402
        return contestants_list
