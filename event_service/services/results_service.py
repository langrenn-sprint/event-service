"""Module for events service."""

import logging
import uuid
from typing import Any

from event_service.adapters import ResultsAdapter
from event_service.models import RaceclassResult

from .events_service import EventNotFoundError, EventsService
from .exceptions import IllegalValueError


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class ResultNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ResultsService:
    """Class representing a service for results."""

    @classmethod
    async def get_all_results(
        cls: Any, db: Any, event_id: str
    ) -> list[RaceclassResult]:
        """Get all results function."""
        _results = await ResultsAdapter.get_all_results(db, event_id)
        return [RaceclassResult.from_dict(e) for e in _results]

    @classmethod
    async def create_result(
        cls: Any, db: Any, event_id: str, result: RaceclassResult
    ) -> str | None:
        """Create result function.

        Args:
            db (Any): the db
            event_id: the event
            result (RaceclassResult): a result instanse to be created

        Returns:
            Optional[str]: The id of the created result. None otherwise.

        Raises:
            IllegalValueError: input object has illegal values
            EventNotFoundError: event does not exist
        """
        # First we have to check if the event exist:
        try:
            _ = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundError as e:
            raise e from e
        # Validation:
        if result.id:
            msg = f"Cannot create result with input id {result.id}"
            raise IllegalValueError(msg) from None
        # create id
        result_id = create_id()
        result.id = result_id
        # insert new result
        new_result = result.to_dict()
        res = await ResultsAdapter.create_result(db, new_result)
        logging.debug(f"inserted result with id: {result_id}")
        if res:
            return result_id
        return None

    @classmethod
    async def get_result_by_raceclass(
        cls: Any, db: Any, event_id: str, raceclass: str
    ) -> RaceclassResult:
        """Get result function."""
        result = await ResultsAdapter.get_result_by_raceclass(db, event_id, raceclass)
        # return the document if found:
        if not result:
            msg = f"Result not found for event/raceclass {event_id}/{raceclass}"
            raise ResultNotFoundError(msg) from None

        return RaceclassResult.from_dict(result)

    @classmethod
    async def delete_result(
        cls: Any, db: Any, event_id: str, raceclass: str
    ) -> str | None:
        """Get result function."""
        # get old document
        result = await ResultsAdapter.get_result_by_raceclass(db, event_id, raceclass)
        # delete the document if found:
        if not result:
            msg = f"Result not found for event/raceclass {event_id}/{raceclass}"
            raise ResultNotFoundError(msg) from None

        return await ResultsAdapter.delete_result(db, result["id"])
