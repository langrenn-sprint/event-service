"""Module for raceclasses service."""

import logging
import uuid
from typing import Any

from event_service.adapters import RaceclassesAdapter
from event_service.models import Raceclass

from .contestants_service import validate_ageclass
from .events_service import EventNotFoundError, EventsService
from .exceptions import IllegalValueError, RaceclassNotFoundError


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class RaceclassCreateError(Exception):
    """Class representing custom exception for create method."""


class RaceclassUpdateError(Exception):
    """Class representing custom exception for update method."""


class RaceclassNotUniqueNameError(Exception):
    """Class representing custom exception for find method."""


class RaceclassesService:
    """Class representing a service for raceclasses."""

    @classmethod
    async def get_all_raceclasses(cls: Any, db: Any, event_id: str) -> list[Raceclass]:
        """Get all raceclasses function."""
        raceclasses: list[Raceclass] = []
        _raceclasses = await RaceclassesAdapter.get_all_raceclasses(db, event_id)
        raceclasses = [Raceclass.from_dict(a) for a in _raceclasses]
        return sorted(
            raceclasses,
            key=lambda k: (
                k.group is not None,
                k.order is not None,
                k.group,
                k.order,
                k.name,
            ),
            reverse=False,
        )

    @classmethod
    async def create_raceclass(
        cls: Any, db: Any, event_id: str, raceclass: Raceclass
    ) -> str | None:
        """Create raceclass function.

        Args:
            db (Any): the db
            event_id (str): identifier of the event the raceclass takes part in
            raceclass (Raceclass): a raceclass instanse to be created

        Returns:
            Optional[str]: The id of the created raceclass. None otherwise.

        Raises:
            EventNotFoundError: event does not exist
            IllegalValueError: input object has illegal values
        """
        # First we have to check if the event exist:
        try:
            _ = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundError as e:
            raise e from e
        # Validation:
        if raceclass.id:
            msg = "Cannot create raceclass with input id."
            raise IllegalValueError(msg) from None
        # Remove spaces from ageclasses:
        raceclass.ageclasses = [ageclass.strip() for ageclass in raceclass.ageclasses]
        # Validate raceclasses:
        try:
            await validate_raceclass(raceclass)
        except IllegalValueError as e:
            raise e from e
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
        if not raceclass:
            msg = f"Raceclass with id {raceclass_id} not found"
            raise RaceclassNotFoundError(msg) from None
        return Raceclass.from_dict(raceclass)

    @classmethod
    async def get_raceclass_by_name(
        cls: Any, db: Any, event_id: str, name: str
    ) -> list[Raceclass]:
        """Get raceclass by name function."""
        _raceclasses = await RaceclassesAdapter.get_raceclass_by_name(
            db, event_id, name
        )
        return [Raceclass.from_dict(raceclass) for raceclass in _raceclasses]

    @classmethod
    async def get_raceclass_by_ageclass_name(
        cls: Any, db: Any, event_id: str, ageclass_name: str
    ) -> list[Raceclass]:
        """Get raceclass by ageclass_name function."""
        _raceclasses = await RaceclassesAdapter.get_all_raceclasses(db, event_id)
        return [
            Raceclass.from_dict(raceclass)
            for raceclass in _raceclasses
            if ageclass_name in raceclass["ageclasses"]
        ]

    @classmethod
    async def update_raceclass(
        cls: Any, db: Any, event_id: str, raceclass_id: str, raceclass: Raceclass
    ) -> str | None:
        """Get raceclass function."""
        # get old document
        old_raceclass = await RaceclassesAdapter.get_raceclass_by_id(
            db, event_id, raceclass_id
        )
        # Check if raceclass if found:
        if not old_raceclass:
            msg = f"Raceclass with id {raceclass_id} not found."
            raise RaceclassNotFoundError(msg) from None
        if raceclass.id != old_raceclass["id"]:
            msg = f"Cannot change id for raceclass from {old_raceclass['id']} to {raceclass.id}."
            raise IllegalValueError(msg) from None
        # Remove spaces from ageclasses:
        raceclass.ageclasses = [ageclass.strip() for ageclass in raceclass.ageclasses]
        # Validate raceclasses:
        try:
            await validate_raceclass(raceclass)
        except IllegalValueError as e:
            raise e from e
        # Everything ok, update:
        new_raceclass = raceclass.to_dict()
        return await RaceclassesAdapter.update_raceclass(
            db, event_id, raceclass_id, new_raceclass
        )

    @classmethod
    async def delete_raceclass(
        cls: Any, db: Any, event_id: str, raceclass_id: str
    ) -> str | None:
        """Get raceclass function."""
        # get old document
        raceclass = await RaceclassesAdapter.get_raceclass_by_id(
            db, event_id, raceclass_id
        )
        # delete the document if found:
        if not raceclass:
            msg = f"Raceclass with id {raceclass_id} not found"
            raise RaceclassNotFoundError(msg) from None

        return await RaceclassesAdapter.delete_raceclass(db, event_id, raceclass_id)

    # -- helper methods


async def validate_raceclass(raceclass: Raceclass) -> None:
    """Validator function for raceclasses."""
    # Check that ageclass is valid:
    if hasattr(raceclass, "ageclasses"):
        for ageclass in raceclass.ageclasses:
            try:
                await validate_ageclass(ageclass)
            except IllegalValueError as e:
                raise e from e
