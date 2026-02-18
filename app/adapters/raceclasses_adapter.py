"""Module for raceclass adapter."""

import logging
from typing import Any
from uuid import UUID

from app.models import Raceclass


class RaceclassesAdapter:
    """Class representing an adapter for raceclasses."""

    database: Any
    logger: logging.Logger

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database
        cls.logger = logging.getLogger("uvicorn.error")

    @classmethod
    async def get_all_raceclasses(
        cls: Any, event_id: UUID
    ) -> list[Raceclass]:  # pragma: no cover
        """Get all raceclasses function."""
        cursor = cls.database.raceclasses_collection.find({"event_id": event_id}).sort(
            [("id", 1)]
        )
        return [
            Raceclass.model_validate(raceclass)
            for raceclass in await cursor.to_list(None)
        ]

    @classmethod
    async def create_raceclass(
        cls: Any, event_id: UUID, raceclass: Raceclass
    ) -> str:  # pragma: no cover
        """Create raceclass function."""
        _ = event_id
        return await cls.database.raceclasses_collection.insert_one(
            raceclass.model_dump()
        )

    @classmethod
    async def get_raceclass_by_id(
        cls: Any, event_id: UUID, raceclass_id: UUID
    ) -> Raceclass | None:  # pragma: no cover
        """Get raceclass by id function."""
        result = await cls.database.raceclasses_collection.find_one(
            {"$and": [{"event_id": event_id}, {"id": raceclass_id}]}
        )
        if result is None:
            return None
        return Raceclass.model_validate(result)

    @classmethod
    async def get_raceclass_by_name(
        cls: Any, event_id: UUID, name: str
    ) -> list[Raceclass]:  # pragma: no cover
        """Get raceclass by name function."""
        cursor = cls.database.raceclasses_collection.find(
            {
                "$and": [
                    {"event_id": event_id},
                    {"name": name},
                ]
            }
        ).sort([("name", 1)])
        return [
            Raceclass.model_validate(raceclass)
            for raceclass in await cursor.to_list(None)
        ]

    @classmethod
    async def get_raceclass_by_ageclass_name(
        cls: Any, event_id: UUID, ageclass_name: str
    ) -> list[Raceclass]:  # pragma: no cover
        """Get raceclass by name function."""
        cursor = cls.database.raceclasses_collection.find(
            {
                "$and": [
                    {"event_id": event_id},
                    {"ageclasses": ageclass_name},
                ]
            }
        ).sort([("name", 1)])
        return [
            Raceclass.model_validate(raceclass)
            for raceclass in await cursor.to_list(None)
        ]

    @classmethod
    async def update_raceclass(
        cls: Any, event_id: UUID, raceclass_id: UUID, raceclass: Raceclass
    ) -> str | None:  # pragma: no cover
        """Update given raceclass function."""
        return await cls.database.raceclasses_collection.replace_one(
            {"$and": [{"event_id": event_id}, {"id": raceclass_id}]},
            raceclass.model_dump(),
        )

    @classmethod
    async def delete_raceclass(
        cls: Any, event_id: UUID, raceclass_id: UUID
    ) -> str | None:  # pragma: no cover
        """Delete given raceclass function."""
        return await cls.database.raceclasses_collection.delete_one(
            {"$and": [{"event_id": event_id}, {"id": raceclass_id}]}
        )

    @classmethod
    async def delete_all_raceclasses(
        cls: Any, event_id: UUID
    ) -> str | None:  # pragma: no cover
        """Delete all raceclasses function."""
        return await cls.database.raceclasses_collection.delete_many(
            {"event_id": event_id}
        )
