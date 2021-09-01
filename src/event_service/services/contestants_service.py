"""Module for contestants service."""
import logging
from typing import Any, List, Optional
import uuid

from event_service.adapters import ContestantsAdapter
from event_service.models import Contestant
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class ContestantNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantsService:
    """Class representing a service for contestants."""

    @classmethod
    async def get_all_contestants(cls: Any, db: Any) -> List[Contestant]:
        """Get all contestants function."""
        contestants = await ContestantsAdapter.get_all_contestants(db)
        return contestants

    @classmethod
    async def create_contestant(
        cls: Any, db: Any, contestant: Contestant
    ) -> Optional[str]:
        """Create contestant function.

        Args:
            db (Any): the db
            contestant (Contestant): a contestant instanse to be created

        Returns:
            Optional[str]: The id of the created contestant. None otherwise.

        Raises:
            IllegalValueException: input object has illegal values
        """
        # Validation:
        if contestant.id:
            raise IllegalValueException("Cannot create contestant with input id.")
        # create id
        id = create_id()
        contestant.id = id
        # insert new contestant
        new_contestant = contestant.to_dict()
        result = await ContestantsAdapter.create_contestant(db, new_contestant)
        logging.debug(f"inserted contestant with id: {id}")
        if result:
            return id
        return None

    @classmethod
    async def get_contestant_by_id(cls: Any, db: Any, id: str) -> Contestant:
        """Get contestant function."""
        contestant = await ContestantsAdapter.get_contestant_by_id(db, id)
        # return the document if found:
        if contestant:
            return Contestant.from_dict(contestant)
        raise ContestantNotFoundException(f"Contestant with id {id} not found")

    @classmethod
    async def update_contestant(
        cls: Any, db: Any, id: str, contestant: Contestant
    ) -> Optional[str]:
        """Get contestant function."""
        # get old document
        old_contestant = await ContestantsAdapter.get_contestant_by_id(db, id)
        # update the contestant if found:
        if old_contestant:
            if contestant.id != old_contestant["id"]:
                raise IllegalValueException("Cannot change id for contestant.")
            new_contestant = contestant.to_dict()
            result = await ContestantsAdapter.update_contestant(db, id, new_contestant)
            return result
        raise ContestantNotFoundException(f"Contestant with id {id} not found.")

    @classmethod
    async def delete_contestant(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get contestant function."""
        # get old document
        contestant = await ContestantsAdapter.get_contestant_by_id(db, id)
        # delete the document if found:
        if contestant:
            result = await ContestantsAdapter.delete_contestant(db, id)
            return result
        raise ContestantNotFoundException(f"Contestant with id {id} not found")
