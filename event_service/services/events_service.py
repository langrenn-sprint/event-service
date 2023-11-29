"""Module for events service."""
from datetime import date, time
import logging
from typing import Any, List, Optional
import uuid
import zoneinfo

from event_service.adapters import (
    CompetitionFormatsAdapter,
    CompetitionFormatsAdapterException,
    EventsAdapter,
)
from event_service.models import Event
from .exceptions import (
    CompetitionFormatNotFoundException,
    IllegalValueException,
    InvalidDateFormatException,
    InvalidTimezoneException,
)


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class EventNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class EventsService:
    """Class representing a service for events."""

    @classmethod
    async def get_all_events(cls: Any, db: Any) -> List[Event]:
        """Get all events function."""
        events: List[Event] = []
        _events = await EventsAdapter.get_all_events(db)
        for e in _events:
            events.append(Event.from_dict(e))
        _s = sorted(
            events,
            key=lambda k: (
                k.date_of_event is not None,
                k.date_of_event,
                k.time_of_event is not None,
                k.time_of_event,
            ),
            reverse=True,
        )
        return _s

    @classmethod
    async def create_event(cls: Any, db: Any, event: Event) -> Optional[str]:
        """Create event function.

        Args:
            db (Any): the db
            event (Event): a event instanse to be created

        Returns:
            Optional[str]: The id of the created event. None otherwise.

        Raises:
            IllegalValueException: input object has illegal values
        """
        if event.id:
            # Validate for duplicates
            existing_event = await EventsAdapter.get_event_by_id(db, str(event.id))
            if existing_event:
                raise IllegalValueException(f"Event id {event.id} exists.") from None
            id = event.id
        else:
            # create id
            id = create_id()
            event.id = id        # Validate new event:
        await validate_event(db, event)
        # insert new event
        new_event = event.to_dict()
        result = await EventsAdapter.create_event(db, new_event)
        logging.debug(f"inserted event with id: {id}")
        if result:
            return id
        return None

    @classmethod
    async def get_event_by_id(cls: Any, db: Any, id: str) -> Event:
        """Get event function."""
        event = await EventsAdapter.get_event_by_id(db, id)
        # return the document if found:
        if event:
            return Event.from_dict(event)
        raise EventNotFoundException(f"Event with id {id} not found") from None

    @classmethod
    async def update_event(cls: Any, db: Any, id: str, event: Event) -> Optional[str]:
        """Get event function."""
        # validate:
        await validate_event(db, event)
        # get old document
        old_event = await EventsAdapter.get_event_by_id(db, id)
        # update the event if found:
        if old_event:
            if event.id != old_event["id"]:
                raise IllegalValueException("Cannot change id for event.") from None
            new_event = event.to_dict()
            result = await EventsAdapter.update_event(db, id, new_event)
            return result
        raise EventNotFoundException(f"Event with id {id} not found.") from None

    @classmethod
    async def delete_event(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get event function."""
        # get old document
        event = await EventsAdapter.get_event_by_id(db, id)
        # delete the document if found:
        if event:
            result = await EventsAdapter.delete_event(db, id)
            return result
        raise EventNotFoundException(f"Event with id {id} not found") from None


#   Validation:
async def validate_event(db: Any, event: Event) -> None:  # noqa: C901
    """Validate the event."""
    # Validate date_of_event if set:
    if event.date_of_event:
        try:
            date.fromisoformat(event.date_of_event)  # type: ignore
        except ValueError as e:
            raise InvalidDateFormatException(
                'Time "{time_str}" has invalid format.'
            ) from e

    # Validate time_of_event if set:
    if event.time_of_event:
        try:
            time.fromisoformat(event.time_of_event)  # type: ignore
        except ValueError as e:
            raise InvalidDateFormatException(
                'Time "{time_str}" has invalid format.'
            ) from e

    # Validate timezone:
    if event.timezone:
        if event.timezone not in zoneinfo.available_timezones():
            raise InvalidTimezoneException(
                f"Invalid timezone: {event.timezone}."
            ) from None

    # Validate competition_format:
    if event.competition_format:
        try:
            competition_formats = (
                await CompetitionFormatsAdapter.get_competition_formats_by_name(
                    db, event.competition_format
                )
            )
        except CompetitionFormatsAdapterException as e:
            raise CompetitionFormatNotFoundException(
                f'Competition format "{event.competition_format!r}" not found.'
            ) from e

        if len(competition_formats) == 1:
            pass
        elif len(competition_formats) == 0:
            raise CompetitionFormatNotFoundException(
                f'Competition_format "{event.competition_format!r}" for event not found.'
            ) from None
        else:
            raise CompetitionFormatNotFoundException(
                f'Competition_format "{event.competition_format!r}" for event is ambigous.'
            ) from None
