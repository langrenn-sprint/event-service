"""Module for events service."""
import logging
from typing import Any, List, Optional
import uuid

from event_service.adapters import EventsAdapter
from event_service.models import Event
from .exceptions import IllegalValueException


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
        events = await EventsAdapter.get_all_events(db)
        return events

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
        # Validation:
        if event.id:
            raise IllegalValueException("Cannot create event with input id.")
        # create id
        id = create_id()
        event.id = id
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
        raise EventNotFoundException(f"Event with id {id} not found")

    @classmethod
    async def update_event(cls: Any, db: Any, id: str, event: Event) -> Optional[str]:
        """Get event function."""
        # get old document
        old_event = await EventsAdapter.get_event_by_id(db, id)
        # update the event if found:
        if old_event:
            if event.id != old_event["id"]:
                raise IllegalValueException("Cannot change id for event.")
            new_event = event.to_dict()
            result = await EventsAdapter.update_event(db, id, new_event)
            return result
        raise EventNotFoundException(f"Event with id {id} not found.")

    @classmethod
    async def delete_event(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get event function."""
        # get old document
        event = await EventsAdapter.get_event_by_id(db, id)
        # delete the document if found:
        if event:
            result = await EventsAdapter.delete_event(db, id)
            return result
        raise EventNotFoundException(f"Event with id {id} not found")
