"""Module for raceclass results adapter."""
from typing import Any, List, Optional

from .adapter import Adapter


class ResultsAdapter(Adapter):
    """Class representing an adapter for results."""

    @classmethod
    async def get_all_results(
        cls: Any, db: Any, event_id: str
    ) -> List:  # pragma: no cover
        """Get all results function."""
        results: List = []
        cursor = db.raceclass_results_collection.find({"event_id": event_id})
        for result in await cursor.to_list(None):
            results.append(result)
        return results

    @classmethod
    async def create_result(cls: Any, db: Any, result: dict) -> str:  # pragma: no cover
        """Create result function."""
        res = await db.raceclass_results_collection.insert_one(result)
        return res

    @classmethod
    async def get_result_by_id(cls: Any, db: Any, id: str) -> dict:  # pragma: no cover
        """Get result function."""
        res = await db.raceclass_results_collection.find_one({"id": id})
        return res

    @classmethod
    async def get_result_by_raceclass(
        cls: Any, db: Any, event_id: str, raceclass: str
    ) -> dict:  # pragma: no cover
        """Get results by raceclass function."""
        result = await db.raceclass_results_collection.find_one(
            {"$and": [{"event_id": event_id}, {"raceclass": raceclass}]}
        )
        return result

    @classmethod
    async def delete_result(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get result function."""
        result = await db.raceclass_results_collection.delete_one({"id": id})
        return result
