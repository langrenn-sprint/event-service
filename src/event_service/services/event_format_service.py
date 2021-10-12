"""Module for event_format service."""
import logging
from typing import Any, Optional
import uuid

from event_service.adapters import EventFormatAdapter
from event_service.models import (
    CompetitionFormat,
    IndividualSprintFormat,
    IntervalStartFormat,
)
from .events_service import EventNotFoundException, EventsService


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class EventFormatNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class EventFormatService:
    """Class representing a service for event_format."""

    @classmethod
    async def create_event_format(
        cls: Any, db: Any, event_id: str, event_format: CompetitionFormat
    ) -> Optional[str]:
        """Create event_format function.

        Args:
            db (Any): the db
            event_id (str): identifier of the event the event_format takes part in
            event_format (CompetitionFormat): a event_format instanse to be created

        Returns:
            Optional[str]: The id of the created event_format. None otherwise.

        Raises:
            EventNotFoundException: event does not exist
        """
        # First we have to check if the event exist:
        try:
            _ = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundException as e:
            raise e from e
        # insert new event_format
        new_event_format = event_format.to_dict()
        result = await EventFormatAdapter.create_event_format(
            db, event_id, new_event_format
        )
        logging.debug(
            f"inserted event_format for event_id/name: {event_id}/{event_format.name}"
        )
        if result:
            return event_format.name
        return None

    @classmethod
    async def get_event_format(
        cls: Any,
        db: Any,
        event_id: str,
    ) -> CompetitionFormat:
        """Get event_format function."""
        event_format = await EventFormatAdapter.get_event_format(db, event_id)
        # return the document if found:
        if event_format:
            if event_format["datatype"] == "interval_start":
                return IntervalStartFormat.from_dict(event_format)
            elif event_format["datatype"] == "individual_sprint":
                return IndividualSprintFormat.from_dict(event_format)
        raise EventFormatNotFoundException(
            f"EventFormat with for event id {event_id} not found"
        ) from None

    @classmethod
    async def update_event_format(
        cls: Any,
        db: Any,
        event_id: str,
        event_format: CompetitionFormat,
    ) -> Optional[str]:
        """Get event_format function."""
        # get old document
        old_event_format = await EventFormatAdapter.get_event_format(db, event_id)
        # update the event_format if found:
        if old_event_format:
            new_event_format = event_format.to_dict()
            result = await EventFormatAdapter.update_event_format(
                db, event_id, new_event_format
            )
            return result
        raise EventFormatNotFoundException(
            f"EventFormat for event with id {event_id} not found."
        ) from None

    @classmethod
    async def delete_event_format(cls: Any, db: Any, event_id: str) -> Optional[str]:
        """Get event_format function."""
        # get old document
        event_format = await EventFormatAdapter.get_event_format(db, event_id)
        # delete the document if found:
        if event_format:
            result = await EventFormatAdapter.delete_event_format(db, event_id)
            return result
        raise EventFormatNotFoundException(
            f"EventFormat for event id {event_id} not found"
        ) from None
