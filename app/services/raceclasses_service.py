"""Module for raceclasses service."""

import logging
from typing import Any
from uuid import UUID

from app.adapters import ContestantsAdapter, EventsAdapter, RaceclassesAdapter
from app.models import Raceclass
from app.services import (
    EventNotFoundError,
    IllegalValueError,
    RaceclassNotFoundError,
)


class RaceclassCreateError(Exception):
    """Class representing custom exception for create method."""


class RaceclassUpdateError(Exception):
    """Class representing custom exception for update method."""


class RaceclassNotUniqueNameError(Exception):
    """Class representing custom exception for find method."""


class RaceclassesService:
    """Class representing a service for raceclasses."""

    logger = logging.getLogger("event_service.services.raceclasses_service")

    @classmethod
    async def get_all_raceclasses(cls: Any, event_id: UUID) -> list[Raceclass]:
        """Get all raceclasses function."""
        raceclasses: list[Raceclass] = []
        raceclasses = await RaceclassesAdapter.get_all_raceclasses(event_id)
        for raceclass in raceclasses:
            raceclass.no_of_contestants = await get_no_of_contestants_in_raceclass(
                event_id, raceclass.ageclasses
            )
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
        cls: Any, event_id: UUID, raceclass: Raceclass
    ) -> UUID | None:
        """Create raceclass function.

        Args:
            db (Any): the db
            event_id (str): identifier of the event the raceclass takes part in
            raceclass (Raceclass): a raceclass instanse to be created

        Returns:
            Optional[str]: The id of the created raceclass. None otherwise.

        Raises:
            EventNotFoundError: event does not exist
        """
        # First we have to check if the event exist:
        event = await EventsAdapter.get_event_by_id(event_id)
        if not event:
            msg = f"Event with id {event_id} not found."
            raise EventNotFoundError(msg) from None
        # Remove spaces from ageclasses:
        raceclass.ageclasses = [ageclass.strip() for ageclass in raceclass.ageclasses]
        # insert new raceclass
        result = await RaceclassesAdapter.create_raceclass(event_id, raceclass)
        cls.logger.debug(
            f"inserted raceclass with event_id/raceclass_id: {event_id}/{raceclass.id}"
        )
        if result:
            return raceclass.id
        return None

    @classmethod
    async def delete_all_raceclasses(cls: Any, event_id: UUID) -> None:
        """Get all raceclasses function."""
        await RaceclassesAdapter.delete_all_raceclasses(event_id)

    @classmethod
    async def get_raceclass_by_id(
        cls: Any, event_id: UUID, raceclass_id: UUID
    ) -> Raceclass:
        """Get raceclass by id function."""
        raceclass = await RaceclassesAdapter.get_raceclass_by_id(event_id, raceclass_id)
        if raceclass:
            raceclass.no_of_contestants = await get_no_of_contestants_in_raceclass(
                event_id, raceclass.ageclasses
            )
            return raceclass
        msg = f"Raceclass with id {raceclass_id} not found."
        raise RaceclassNotFoundError(msg) from None

    @classmethod
    async def get_raceclass_by_name(
        cls: Any, event_id: UUID, raceclass_name: str
    ) -> list[Raceclass]:
        """Get raceclass by name function."""
        raceclasses = await RaceclassesAdapter.get_raceclass_by_name(
            event_id, raceclass_name
        )
        for raceclass in raceclasses:
            raceclass.no_of_contestants = await get_no_of_contestants_in_raceclass(
                event_id, raceclass.ageclasses
            )
        return raceclasses

    @classmethod
    async def get_raceclass_by_ageclass_name(
        cls: Any, event_id: UUID, ageclass_name: str
    ) -> list[Raceclass]:
        """Get raceclass by ageclass_name function."""
        _raceclasses = await RaceclassesAdapter.get_raceclass_by_ageclass_name(
            event_id, ageclass_name
        )
        for raceclass in _raceclasses:
            raceclass.no_of_contestants = await get_no_of_contestants_in_raceclass(
                event_id, raceclass.ageclasses
            )
        return [
            raceclass
            for raceclass in _raceclasses
            if ageclass_name in raceclass.ageclasses
        ]

    @classmethod
    async def update_raceclass(
        cls: Any, event_id: UUID, raceclass_id: UUID, raceclass: Raceclass
    ) -> str | None:
        """Get raceclass function."""
        # get old document
        old_raceclass = await RaceclassesAdapter.get_raceclass_by_id(
            event_id, raceclass_id
        )
        # Check if raceclass if found:
        if not old_raceclass:
            msg = f"Raceclass with id {raceclass_id} not found."
            raise RaceclassNotFoundError(msg) from None
        if raceclass.id != old_raceclass.id:
            msg = f"Cannot change id for raceclass from {old_raceclass.id} to {raceclass.id}."
            raise IllegalValueError(msg) from None
        # Remove spaces from ageclasses:
        raceclass.ageclasses = [ageclass.strip() for ageclass in raceclass.ageclasses]
        # Everything ok, update:
        return await RaceclassesAdapter.update_raceclass(
            event_id, raceclass_id, raceclass
        )

    @classmethod
    async def delete_raceclass(
        cls: Any, event_id: UUID, raceclass_id: UUID
    ) -> str | None:
        """Get raceclass function."""
        # get old document
        raceclass = await RaceclassesAdapter.get_raceclass_by_id(event_id, raceclass_id)
        # delete the document if found:
        if not raceclass:
            msg = f"Raceclass with id {raceclass_id} not found"
            raise RaceclassNotFoundError(msg) from None

        return await RaceclassesAdapter.delete_raceclass(event_id, raceclass_id)

    # -- helper methods


async def get_no_of_contestants_in_raceclass(
    event_id: UUID, ageclasses: list[str]
) -> int:
    """Get number of contestants in a raceclass."""
    return len(
        await ContestantsAdapter.get_contestants_by_ageclasses(event_id, ageclasses)
    )
