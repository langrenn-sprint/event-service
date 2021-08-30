"""Module for ageclass adapter."""
import logging
from typing import Any, List, Optional
import uuid


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class AgeclassesAdapter:
    """Class representing an adapter for ageclasses."""

    @classmethod
    async def get_all_ageclasses(cls: Any, db: Any) -> List:  # pragma: no cover
        """Get all ageclasses function."""
        ageclasses: List = []
        cursor = db.ageclasses_collection.find()
        for ageclass in await cursor.to_list(length=100):
            ageclasses.append(ageclass)
            logging.debug(ageclass)
        return ageclasses

    @classmethod
    async def create_ageclass(
        cls: Any, db: Any, ageclass: dict
    ) -> Optional[str]:  # pragma: no cover
        """Create ageclass function."""
        # create id
        id = create_id()
        ageclass["id"] = id
        # insert new ageclass
        result = await db.ageclasses_collection.insert_one(ageclass)
        logging.debug(f"inserted ageclass with id: {id}")
        if result:
            return id
        return None  # pragma: no cover

    @classmethod
    async def get_ageclass(
        cls: Any, db: Any, id: str
    ) -> Optional[dict]:  # pragma: no cover
        """Get ageclass function."""
        # insert new
        result = await db.ageclasses_collection.find_one({"id": id})
        # return the document if found:
        if result:
            return result
        return None

    @classmethod
    async def update_ageclass(
        cls: Any, db: Any, id: str, ageclass: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get ageclass function."""
        # get old document
        old_document = await db.ageclasses_collection.find_one({"id": id})
        # update the document if found:
        if old_document:
            _ = await db.ageclasses_collection.replace_one({"id": id}, ageclass)
            return id
        return None

    @classmethod
    async def delete_ageclass(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get ageclass function."""
        # get old document
        document = await db.ageclasses_collection.find_one({"id": id})
        # delete the document if found:
        if document:
            _ = await db.ageclasses_collection.delete_one({"id": id})
            return id
        return None
