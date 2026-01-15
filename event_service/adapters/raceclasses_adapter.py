"""Module for raceclass adapter."""

from typing import Any

from .adapter import Adapter


class RaceclassesAdapter(Adapter):
    """Class representing an adapter for raceclasses."""

    database: Any

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database

    @classmethod
    async def get_all_raceclasses(
        cls: Any, event_id: str
    ) -> list[dict]:  # pragma: no cover
        """Get all raceclasses function."""
        raceclasses: list = []
        cursor = cls.database.raceclasses_collection.find({"event_id": event_id}).sort(
            [("id", 1)]
        )
        for raceclass in await cursor.to_list(None):
            raceclasses.append(raceclass)  # noqa: PERF402
        return raceclasses

    @classmethod
    async def create_raceclass(
        cls: Any, event_id: str, raceclass: dict
    ) -> str:  # pragma: no cover
        """Create raceclass function."""
        _ = event_id
        return await cls.database.raceclasses_collection.insert_one(raceclass)

    @classmethod
    async def get_raceclass_by_id(
        cls: Any, event_id: str, raceclass_id: str
    ) -> dict:  # pragma: no cover
        """Get raceclass by id function."""
        return await cls.database.raceclasses_collection.find_one(
            {"$and": [{"event_id": event_id}, {"id": raceclass_id}]}
        )

    @classmethod
    async def get_raceclass_by_name(
        cls: Any, event_id: str, name: str
    ) -> list[dict]:  # pragma: no cover
        """Get raceclass by name function."""
        raceclasses: list = []
        cursor = cls.database.raceclasses_collection.find(
            {
                "$and": [
                    {"event_id": event_id},
                    {"name": name},
                ]
            }
        ).sort([("name", 1)])
        for raceclass in await cursor.to_list(None):
            raceclasses.append(raceclass)  # noqa: PERF402
        return raceclasses

    @classmethod
    async def update_raceclass(
        cls: Any, event_id: str, raceclass_id: str, raceclass: dict
    ) -> str | None:  # pragma: no cover
        """Update given raceclass function."""
        return await cls.database.raceclasses_collection.replace_one(
            {"$and": [{"event_id": event_id}, {"id": raceclass_id}]}, raceclass
        )

    @classmethod
    async def delete_raceclass(
        cls: Any, event_id: str, raceclass_id: str
    ) -> str | None:  # pragma: no cover
        """Delete given raceclass function."""
        return await cls.database.raceclasses_collection.delete_one(
            {"$and": [{"event_id": event_id}, {"id": raceclass_id}]}
        )

    @classmethod
    async def delete_all_raceclasses(
        cls: Any, event_id: str
    ) -> str | None:  # pragma: no cover
        """Delete all raceclasses function."""
        return await cls.database.raceclasses_collection.delete_many(
            {"event_id": event_id}
        )
