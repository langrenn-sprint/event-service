"""Module for events service."""

import logging
import uuid
import zoneinfo
from datetime import date, time
from typing import Any

from event_service.adapters import (
    CompetitionFormatsAdapter,
    CompetitionFormatsAdapterError,
    EventsAdapter,
)
from event_service.models import Event

from .exceptions import (
    CompetitionFormatNotFoundError,
    IllegalValueError,
    InvalidDateFormatError,
    InvalidTimezoneError,
)


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class EventNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class EventsService:
    """Class representing a service for events."""

    logger = logging.getLogger("event_service.services.events_service")

    @classmethod
    async def get_all_events(cls: Any, db: Any) -> list[Event]:
        """Get all events function."""
        _events = await EventsAdapter.get_all_events(db)
        events = [Event.from_dict(e) for e in _events]
        return sorted(
            events,
            key=lambda k: (
                k.date_of_event is not None,
                k.date_of_event,
                k.time_of_event is not None,
                k.time_of_event,
            ),
            reverse=True,
        )

    @classmethod
    async def create_event(cls: Any, db: Any, event: Event) -> str | None:
        """Create event function.

        Args:
            db (Any): the db
            event (Event): a event instanse to be created

        Returns:
            Optional[str]: The id of the created event. None otherwise.

        Raises:
            IllegalValueError: input object has illegal values
        """
        if event.id:
            # Validate for duplicates
            existing_event = await EventsAdapter.get_event_by_id(db, str(event.id))
            if existing_event:
                msg = f"Event id {event.id} exists."
                raise IllegalValueError(msg) from None
            event_id = event.id
        else:
            # create id
            event_id = create_id()
            event.id = event_id
        # Validate new event:
        await validate_event(db, event)
        # insert new event
        new_event = event.to_dict()
        result = await EventsAdapter.create_event(db, new_event)
        cls.logger.debug(f"inserted event with id: {event_id}")
        if not result:
            return None
        return event_id

    @classmethod
    async def get_event_by_id(cls: Any, db: Any, event_id: str) -> Event:
        """Get event function."""
        event = await EventsAdapter.get_event_by_id(db, event_id)
        # return the document if found:
        if not event:
            msg = f"Event with id {event_id} not found"
            raise EventNotFoundError(msg) from None
        return Event.from_dict(event)

    @classmethod
    async def update_event(
        cls: Any, db: Any, event_id: str, event: Event
    ) -> str | None:
        """Get event function."""
        # validate:
        await validate_event(db, event)
        # get old document
        old_event = await EventsAdapter.get_event_by_id(db, event_id)
        # update the event if found:
        if not old_event:
            msg = f"Event with id {event_id} not found"
            raise EventNotFoundError(msg) from None
        if event.id != old_event["id"]:
            msg = f"Cannot change id for event with id {event_id}"
            raise IllegalValueError(msg) from None
        new_event = event.to_dict()
        return await EventsAdapter.update_event(db, event_id, new_event)

    @classmethod
    async def delete_event(cls: Any, db: Any, event_id: str) -> str | None:
        """Get event function."""
        # get old document
        event = await EventsAdapter.get_event_by_id(db, event_id)
        # delete the document if found:
        if not event:
            msg = f"Event with id {event_id} not found"
            raise EventNotFoundError(msg) from None
        return await EventsAdapter.delete_event(db, event_id)


#   Validation:
async def validate_event(db: Any, event: Event) -> None:
    """Validate the event."""
    # Validate date_of_event if set:
    if event.date_of_event:
        try:
            date.fromisoformat(event.date_of_event)  # type: ignore [reportArgumentType]
        except ValueError as e:
            msg = f'Date "{event.date_of_event}" has invalid format.'
            raise InvalidDateFormatError(msg) from e

    # Validate time_of_event if set:
    if event.time_of_event:
        try:
            time.fromisoformat(event.time_of_event)  # type: ignore [reportArgumentType]
        except ValueError as e:
            msg = f'Time "{event.time_of_event}" has invalid format.'
            raise InvalidDateFormatError(msg) from e

    # Validate timezone:
    if event.timezone and event.timezone not in zoneinfo.available_timezones():
        msg = f"Invalid timezone: {event.timezone}."
        raise InvalidTimezoneError(msg) from None

    # Validate competition_format:
    if event.competition_format:
        try:
            competition_formats = (
                await CompetitionFormatsAdapter.get_competition_formats_by_name(
                    db, event.competition_format
                )
            )
        except CompetitionFormatsAdapterError as e:
            msg = f'Competition format "{event.competition_format!r}" not found.'
            raise CompetitionFormatNotFoundError(msg) from e

        if len(competition_formats) == 1:
            pass
        elif len(competition_formats) == 0:
            msg = f'Competition_format "{event.competition_format!r}" for event not found.'
            raise CompetitionFormatNotFoundError(msg) from None
        else:
            msg = f'Competition_format "{event.competition_format!r}" for event is ambigous.'
            raise CompetitionFormatNotFoundError(msg) from None
