"""Module for raceclass results adapter."""

import logging
from typing import Any
from uuid import UUID

from app.models import Result


class ResultsAdapter:
    """Class representing an adapter for results."""

    database: Any
    logger: logging.Logger

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database
        cls.logger = logging.getLogger("uvicorn.error")

    @classmethod
    async def get_all_results(
        cls: Any, event_id: UUID
    ) -> list[Result]:  # pragma: no cover
        """Get all results function."""
        cursor = cls.database.raceclass_results_collection.find(
            {"event_id": event_id}
        ).sort([("id", 1)])
        return [Result.model_validate(result) for result in await cursor.to_list(None)]

    @classmethod
    async def create_result(cls: Any, result: Result) -> str:  # pragma: no cover
        """Create result function."""
        return await cls.database.raceclass_results_collection.insert_one(
            result.model_dump()
        )

    @classmethod
    async def get_result_by_id(
        cls: Any, result_id: UUID
    ) -> Result | None:  # pragma: no cover
        """Get result by id function."""
        result = await cls.database.raceclass_results_collection.find_one(
            {"id": result_id}
        )
        if result is None:
            return None
        return Result.model_validate(result)

    @classmethod
    async def get_result_by_raceclass_name(
        cls: Any, event_id: UUID, raceclass_name: str
    ) -> Result | None:  # pragma: no cover
        """Get results by raceclass function."""
        result = await cls.database.raceclass_results_collection.find_one(
            {"$and": [{"event_id": event_id}, {"raceclass_name": raceclass_name}]}
        )
        if result is None:
            return None
        return Result.model_validate(result)

    @classmethod
    async def delete_result(
        cls: Any, result_id: UUID
    ) -> str | None:  # pragma: no cover
        """Delete result function."""
        return await cls.database.raceclass_results_collection.delete_one(
            {"id": result_id}
        )
