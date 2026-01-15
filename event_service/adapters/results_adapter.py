"""Module for raceclass results adapter."""

from typing import Any

from .adapter import Adapter


class ResultsAdapter(Adapter):
    """Class representing an adapter for results."""

    database: Any

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database

    @classmethod
    async def get_all_results(cls: Any, event_id: str) -> list:  # pragma: no cover
        """Get all results function."""
        cursor = cls.database.raceclass_results_collection.find(
            {"event_id": event_id}
        ).sort([("id", 1)])
        return [result async for result in cursor]

    @classmethod
    async def create_result(cls: Any, result: dict) -> str:  # pragma: no cover
        """Create result function."""
        return await cls.database.raceclass_results_collection.insert_one(result)

    @classmethod
    async def get_result_by_id(cls: Any, result_id: str) -> dict:  # pragma: no cover
        """Get result function."""
        return await cls.database.raceclass_results_collection.find_one(
            {"id": result_id}
        )

    @classmethod
    async def get_result_by_raceclass(
        cls: Any, event_id: str, raceclass: str
    ) -> dict:  # pragma: no cover
        """Get results by raceclass function."""
        return await cls.database.raceclass_results_collection.find_one(
            {"$and": [{"event_id": event_id}, {"raceclass": raceclass}]}
        )

    @classmethod
    async def delete_result(cls: Any, result_id: str) -> str | None:  # pragma: no cover
        """Delete result function."""
        return await cls.database.raceclass_results_collection.delete_one(
            {"id": result_id}
        )
