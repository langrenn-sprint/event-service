"""Module for events service."""

import logging
from typing import Any
from uuid import UUID

from app.adapters import EventsAdapter, ResultsAdapter
from app.models import Result
from app.services import EventNotFoundError


class ResultNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ResultsService:
    """Class representing a service for results."""

    logger = logging.getLogger("event_service.services.results_service")

    @classmethod
    async def create_result(cls: Any, event_id: UUID, result: Result) -> UUID | None:
        """Create result function.

        Args:
            db (Any): the db
            event_id: the event
            result (Result): a result instanse to be created

        Returns:
            Optional[str]: The id of the created result. None otherwise.

        Raises:
            IllegalValueError: input object has illegal values
            EventNotFoundError: event does not exist
        """
        # First we have to check if the event exist:
        event = await EventsAdapter.get_event_by_id(event_id)
        if not event:
            msg = f"Event with id {event_id} not found"
            raise EventNotFoundError(msg) from None
        res = await ResultsAdapter.create_result(result)
        cls.logger.debug(f"inserted result with id: {result.id}")
        if res:
            return result.id
        return None

    @classmethod
    async def delete_result(
        cls: Any, event_id: UUID, raceclass_name: str
    ) -> str | None:
        """Get result function."""
        # get old document
        result = await ResultsAdapter.get_result_by_raceclass_name(
            event_id, raceclass_name
        )
        # delete the document if found:
        if not result:
            msg = f"Result not found for event/raceclass {event_id}/{raceclass_name}"
            raise ResultNotFoundError(msg) from None

        return await ResultsAdapter.delete_result(result.id)
