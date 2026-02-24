"""Module for contestant adapter."""

import logging
from typing import Any
from uuid import UUID

from app.models import Contestant


class ContestantsAdapter:
    """Class representing an adapter for contestants."""

    logger: logging.Logger
    database: Any

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.logger = logging.getLogger("uvicorn.error")
        cls.database = database

    @classmethod
    async def get_all_contestants(
        cls: Any, event_id: UUID
    ) -> list[Contestant]:  # pragma: no cover
        """Get all contestants function."""
        cursor = cls.database.contestants_collection.find({"event_id": event_id}).sort(
            [("id", 1)]
        )
        return [
            Contestant.model_validate(contestant)
            for contestant in await cursor.to_list(None)
        ]

    @classmethod
    async def create_contestant(
        cls: Any, event_id: UUID, contestant: Contestant
    ) -> str:  # pragma: no cover
        """Create contestant function."""
        _ = event_id
        return await cls.database.contestants_collection.insert_one(
            contestant.model_dump()
        )

    @classmethod
    async def get_contestant_by_id(
        cls: Any, event_id: UUID, contestant_id: UUID
    ) -> Contestant | None:  # pragma: no cover
        """Get contestant by id function."""
        result = await cls.database.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}
        )
        if result:
            return Contestant.model_validate(result)
        return None

    @classmethod
    async def get_contestant_by_name(
        cls: Any, event_id: UUID, first_name: str, last_name: str
    ) -> Contestant | None:  # pragma: no cover
        """Get contestant by name function."""
        result = await cls.database.contestants_collection.find_one(
            {
                "$and": [
                    {"event_id": event_id},
                    {"first_name": first_name},
                    {"last_name": last_name},
                ]
            }
        )
        if result:
            return Contestant.model_validate(result)
        return None

    @classmethod
    async def get_contestant_by_bib(
        cls: Any, event_id: UUID, bib: int
    ) -> Contestant | None:  # pragma: no cover
        """Get contestant by bib function."""
        result = await cls.database.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"bib": bib}]}
        )
        if result:
            return Contestant.model_validate(result)
        return None

    @classmethod
    async def get_contestant_by_minidrett_id(
        cls: Any, event_id: UUID, minidrett_id: str
    ) -> Contestant | None:  # pragma: no cover
        """Get contestant by minidrett_id function."""
        result = await cls.database.contestants_collection.find_one(
            {"$and": [{"event_id": event_id}, {"minidrett_id": minidrett_id}]}
        )
        if result:
            return Contestant.model_validate(result)
        return None

    @classmethod
    async def update_contestant(
        cls: Any, event_id: UUID, contestant_id: UUID, contestant: Contestant
    ) -> str | None:  # pragma: no cover
        """Update given contestant function."""
        return await cls.database.contestants_collection.replace_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]},
            contestant.model_dump(),
        )

    @classmethod
    async def delete_contestant(
        cls: Any, event_id: UUID, contestant_id: UUID
    ) -> str | None:  # pragma: no cover
        """Delete given contestant function."""
        return await cls.database.contestants_collection.delete_one(
            {"$and": [{"event_id": event_id}, {"id": contestant_id}]}
        )

    @classmethod
    async def delete_all_contestants(
        cls: Any, event_id: UUID
    ) -> str | None:  # pragma: no cover
        """Delete all contestant function."""
        return await cls.database.contestants_collection.delete_many(
            {"event_id": event_id}
        )

    @classmethod
    async def search_contestants_in_event_by_name(
        cls: Any, event_id: UUID, name: str
    ) -> list[Contestant]:  # pragma: no cover
        """Perform text-search after contestants function."""
        cursor = cls.database.contestants_collection.find(
            {"$and": [{"event_id": event_id}, {"$text": {"$search": f"{name}"}}]}
        ).sort([("bib", 1)])
        return [
            Contestant.model_validate(contestant)
            for contestant in await cursor.to_list(None)
        ]

    @classmethod
    async def get_contestants_by_ageclasses(
        cls: Any, event_id: UUID, ageclasses: list[str]
    ) -> list[Contestant]:  # pragma: no cover
        """Get contestants by ageclass function."""
        cursor = cls.database.contestants_collection.find(
            {"$and": [{"event_id": event_id}, {"ageclass": {"$in": ageclasses}}]}
        )
        return [
            Contestant.model_validate(contestant)
            for contestant in await cursor.to_list(None)
        ]
