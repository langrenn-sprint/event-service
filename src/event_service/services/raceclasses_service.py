"""Module for raceclasses service."""
import logging
from typing import Any, List, Optional
import uuid

from event_service.adapters import RaceclassesAdapter
from event_service.models import Raceclass
from .events_service import EventNotFoundException, EventsService
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class RaceclassNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceclassCreateException(Exception):
    """Class representing custom exception for create method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceclassUpdateException(Exception):
    """Class representing custom exception for update method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceclassNotUniqueNameException(Exception):
    """Class representing custom exception for find method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceclassesService:
    """Class representing a service for raceclasses."""

    @classmethod
    async def get_all_raceclasses(cls: Any, db: Any, event_id: str) -> List[Raceclass]:
        """Get all raceclasses function."""
        raceclasses: List[Raceclass] = []
        _raceclasses = await RaceclassesAdapter.get_all_raceclasses(db, event_id)
        for a in _raceclasses:
            raceclasses.append(Raceclass.from_dict(a))
        _s = sorted(
            raceclasses,
            key=lambda k: (
                k.order is not None,
                k.group,
                k.order,
                k.name,
            ),
            reverse=False,
        )
        return _s

    @classmethod
    async def create_raceclass(
        cls: Any, db: Any, event_id: str, raceclass: Raceclass
    ) -> Optional[str]:
        """Create raceclass function.

        Args:
            db (Any): the db
            event_id (str): identifier of the event the raceclass takes part in
            raceclass (Raceclass): a raceclass instanse to be created

        Returns:
            Optional[str]: The id of the created raceclass. None otherwise.

        Raises:
            EventNotFoundException: event does not exist
            IllegalValueException: input object has illegal values
        """
        # First we have to check if the event exist:
        try:
            _ = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundException as e:
            raise e from e
        # Validation:
        if raceclass.id:
            raise IllegalValueException(
                "Cannot create raceclass with input id."
            ) from None
        # create id
        raceclass_id = create_id()
        raceclass.id = raceclass_id
        # insert new raceclass
        new_raceclass = raceclass.to_dict()
        result = await RaceclassesAdapter.create_raceclass(db, event_id, new_raceclass)
        logging.debug(
            f"inserted raceclass with event_id/raceclass_id: {event_id}/{raceclass_id}"
        )
        if result:
            return raceclass_id
        return None

    @classmethod
    async def delete_all_raceclasses(cls: Any, db: Any, event_id: str) -> None:
        """Get all raceclasses function."""
        await RaceclassesAdapter.delete_all_raceclasses(db, event_id)

    @classmethod
    async def get_raceclass_by_id(
        cls: Any, db: Any, event_id: str, raceclass_id: str
    ) -> Raceclass:
        """Get raceclass function."""
        raceclass = await RaceclassesAdapter.get_raceclass_by_id(
            db, event_id, raceclass_id
        )
        # return the document if found:
        if raceclass:
            return Raceclass.from_dict(raceclass)
        raise RaceclassNotFoundException(
            f"Raceclass with id {raceclass_id} not found"
        ) from None

    @classmethod
    async def get_raceclass_by_name(
        cls: Any, db: Any, event_id: str, name: str
    ) -> List[Raceclass]:
        """Get raceclass by name function."""
        raceclasses: List[Raceclass] = []
        _raceclasses = await RaceclassesAdapter.get_raceclass_by_name(
            db, event_id, name
        )
        for a in _raceclasses:
            raceclasses.append(Raceclass.from_dict(a))
        return raceclasses

    @classmethod
    async def get_raceclass_by_ageclass_name(
        cls: Any, db: Any, event_id: str, ageclass_name: str
    ) -> List[Raceclass]:
        """Get raceclass by ageclass_name function."""
        raceclasses: List[Raceclass] = []
        _raceclasses = await RaceclassesAdapter.get_raceclass_by_ageclass_name(
            db, event_id, ageclass_name
        )
        for a in _raceclasses:
            raceclasses.append(Raceclass.from_dict(a))
        return raceclasses

    @classmethod
    async def update_raceclass(
        cls: Any, db: Any, event_id: str, raceclass_id: str, raceclass: Raceclass
    ) -> Optional[str]:
        """Get raceclass function."""
        # get old document
        old_raceclass = await RaceclassesAdapter.get_raceclass_by_id(
            db, event_id, raceclass_id
        )
        # update the raceclass if found:
        if old_raceclass:
            if raceclass.id != old_raceclass["id"]:
                raise IllegalValueException("Cannot change id for raceclass.") from None
            new_raceclass = raceclass.to_dict()
            result = await RaceclassesAdapter.update_raceclass(
                db, event_id, raceclass_id, new_raceclass
            )
            return result
        raise RaceclassNotFoundException(
            f"Raceclass with id {raceclass_id} not found."
        ) from None

    @classmethod
    async def delete_raceclass(
        cls: Any, db: Any, event_id: str, raceclass_id: str
    ) -> Optional[str]:
        """Get raceclass function."""
        # get old document
        raceclass = await RaceclassesAdapter.get_raceclass_by_id(
            db, event_id, raceclass_id
        )
        # delete the document if found:
        if raceclass:
            result = await RaceclassesAdapter.delete_raceclass(
                db, event_id, raceclass_id
            )
            return result
        raise RaceclassNotFoundException(
            f"Raceclass with id {raceclass_id} not found"
        ) from None

    # -- helper methods
