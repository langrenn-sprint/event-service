"""Module for event_format service."""

import logging
import uuid
from typing import Any

from event_service.adapters import EventFormatAdapter
from event_service.models import (
    CompetitionFormat,
    IndividualSprintFormat,
    IntervalStartFormat,
)

from .events_service import (
    EventNotFoundError,
    EventsService,
)


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class EventFormatNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class EventFormatNotSupportedError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)  # pragma: no cover


class EventFormatService:
    """Class representing a service for event_format."""

    logger = logging.getLogger("event_service.services.event_format_service")

    @classmethod
    async def create_event_format(
        cls: Any, event_id: str, event_format: CompetitionFormat
    ) -> str | None:
        """Create event_format function.

        Args:
            db (Any): the db
            event_id (str): identifier of the event the event_format takes part in
            event_format (CompetitionFormat): a event_format instanse to be created

        Returns:
            Optional[str]: The id of the created event_format. None otherwise.

        Raises:
            EventNotFoundError: event does not exist
        """
        # First we have to check if the event exist:
        try:
            _ = await EventsService.get_event_by_id(event_id)
        except EventNotFoundError as e:
            raise e from e
        # insert new event_format
        new_event_format = event_format.to_dict()
        result = await EventFormatAdapter.create_event_format(
            event_id, new_event_format
        )
        cls.logger.debug(
            f"inserted event_format for event_id/name: {event_id}/{event_format.name}"
        )
        if result:
            return event_format.name
        return None

    @classmethod
    async def get_event_format(
        cls: Any,
        event_id: str,
    ) -> CompetitionFormat:
        """Get event_format function."""
        event_format = await EventFormatAdapter.get_event_format(event_id)
        # return the document if found:
        if not event_format:
            msg = f"EventFormat with for event id {event_id} not found"
            raise EventFormatNotFoundError(msg) from None

        if event_format["datatype"] == "interval_start":
            return IntervalStartFormat.from_dict(event_format)
        if event_format["datatype"] == "individual_sprint":
            return IndividualSprintFormat.from_dict(event_format)
        msg = f"Unsupported event format type: {event_format['datatype']}"  # pragma: no cover
        raise EventFormatNotSupportedError(msg)  # pragma: no cover

    @classmethod
    async def update_event_format(
        cls: Any,
        event_id: str,
        event_format: CompetitionFormat,
    ) -> str | None:
        """Get event_format function."""
        # get old document
        old_event_format = await EventFormatAdapter.get_event_format(event_id)
        # update the event_format if found:
        if not old_event_format:
            msg = f"EventFormat for event with id {event_id} not found."
            raise EventFormatNotFoundError(msg) from None
        new_event_format = event_format.to_dict()
        return await EventFormatAdapter.update_event_format(event_id, new_event_format)

    @classmethod
    async def delete_event_format(cls: Any, event_id: str) -> str | None:
        """Get event_format function."""
        # get old document
        event_format = await EventFormatAdapter.get_event_format(event_id)
        # delete the document if found:
        if not event_format:
            msg = f"EventFormat for event id {event_id} not found"
            raise EventFormatNotFoundError(msg) from None

        return await EventFormatAdapter.delete_event_format(event_id)
