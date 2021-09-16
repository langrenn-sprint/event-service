"""Module for ageclasses service."""
import logging
from typing import Any, List, Optional
import uuid

from event_service.adapters import AgeclassesAdapter
from event_service.models import Ageclass
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class AgeclassNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class AgeclassCreateException(Exception):
    """Class representing custom exception for create method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class AgeclassUpdateException(Exception):
    """Class representing custom exception for update method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class AgeclassNotUniqueNameException(Exception):
    """Class representing custom exception for find method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class AgeclassesService:
    """Class representing a service for ageclasses."""

    @classmethod
    async def get_all_ageclasses(cls: Any, db: Any, event_id: str) -> List[Ageclass]:
        """Get all ageclasses function."""
        ageclasses: List[Ageclass] = []
        _ageclasses = await AgeclassesAdapter.get_all_ageclasses(db, event_id)
        for a in _ageclasses:
            ageclasses.append(Ageclass.from_dict(a))
        return ageclasses

    @classmethod
    async def create_ageclass(
        cls: Any, db: Any, event_id: str, ageclass: Ageclass
    ) -> Optional[str]:
        """Create ageclass function.

        Args:
            db (Any): the db
            event_id (str): identifier of the event the ageclass takes part in
            ageclass (Ageclass): a ageclass instanse to be created

        Returns:
            Optional[str]: The id of the created ageclass. None otherwise.

        Raises:
            IllegalValueException: input object has illegal values
        """
        # Validation:
        if ageclass.id:
            raise IllegalValueException(
                "Cannot create ageclass with input id."
            ) from None
        # create id
        ageclass_id = create_id()
        ageclass.id = ageclass_id
        # insert new ageclass
        new_ageclass = ageclass.to_dict()
        result = await AgeclassesAdapter.create_ageclass(db, event_id, new_ageclass)
        logging.debug(
            f"inserted ageclass with event_id/ageclass_id: {event_id}/{ageclass_id}"
        )
        if result:
            return ageclass_id
        return None

    @classmethod
    async def delete_all_ageclasses(cls: Any, db: Any, event_id: str) -> None:
        """Get all ageclasses function."""
        await AgeclassesAdapter.delete_all_ageclasses(db, event_id)

    @classmethod
    async def get_ageclass_by_id(
        cls: Any, db: Any, event_id: str, ageclass_id: str
    ) -> Ageclass:
        """Get ageclass function."""
        ageclass = await AgeclassesAdapter.get_ageclass_by_id(db, event_id, ageclass_id)
        # return the document if found:
        if ageclass:
            return Ageclass.from_dict(ageclass)
        raise AgeclassNotFoundException(
            f"Ageclass with id {ageclass_id} not found"
        ) from None

    @classmethod
    async def get_ageclass_by_name(
        cls: Any, db: Any, event_id: str, name: str
    ) -> List[Ageclass]:
        """Get ageclass by name function."""
        ageclasses: List[Ageclass] = []
        _ageclasses = await AgeclassesAdapter.get_ageclass_by_name(db, event_id, name)
        for a in _ageclasses:
            ageclasses.append(Ageclass.from_dict(a))
        return ageclasses

    @classmethod
    async def update_ageclass(
        cls: Any, db: Any, event_id: str, ageclass_id: str, ageclass: Ageclass
    ) -> Optional[str]:
        """Get ageclass function."""
        # get old document
        old_ageclass = await AgeclassesAdapter.get_ageclass_by_id(
            db, event_id, ageclass_id
        )
        # update the ageclass if found:
        if old_ageclass:
            if ageclass.id != old_ageclass["id"]:
                raise IllegalValueException("Cannot change id for ageclass.") from None
            new_ageclass = ageclass.to_dict()
            result = await AgeclassesAdapter.update_ageclass(
                db, event_id, ageclass_id, new_ageclass
            )
            return result
        raise AgeclassNotFoundException(
            f"Ageclass with id {ageclass_id} not found."
        ) from None

    @classmethod
    async def delete_ageclass(
        cls: Any, db: Any, event_id: str, ageclass_id: str
    ) -> Optional[str]:
        """Get ageclass function."""
        # get old document
        ageclass = await AgeclassesAdapter.get_ageclass_by_id(db, event_id, ageclass_id)
        # delete the document if found:
        if ageclass:
            result = await AgeclassesAdapter.delete_ageclass(db, event_id, ageclass_id)
            return result
        raise AgeclassNotFoundException(
            f"Ageclass with id {ageclass_id} not found"
        ) from None

    # -- helper methods
