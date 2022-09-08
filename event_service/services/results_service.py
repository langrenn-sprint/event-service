"""Module for events service."""
import logging
from typing import Any, List, Optional
import uuid

from event_service.adapters import ResultsAdapter
from event_service.models import RaceclassResult
from .events_service import EventNotFoundException, EventsService
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class ResultNotFoundException(Exception):
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
    ) -> List[RaceclassResult]:
        """Get all results function."""
        results: List[RaceclassResult] = []
        _results = await ResultsAdapter.get_all_results(db, event_id)
        for e in _results:
            results.append(RaceclassResult.from_dict(e))
        return results

    @classmethod
    async def create_result(
        cls: Any, db: Any, event_id: str, result: RaceclassResult
    ) -> Optional[str]:
        """Create result function.

        Args:
            db (Any): the db
            event_id: the event
            result (RaceclassResult): a result instanse to be created

        Returns:
            Optional[str]: The id of the created result. None otherwise.

        Raises:
            IllegalValueException: input object has illegal values
            EventNotFoundException: event does not exist
        """
        # First we have to check if the event exist:
        try:
            _ = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundException as e:
            raise e from e
        # Validation:
        if result.id:
            raise IllegalValueException("Cannot create result with input id.") from None
        # create id
        id = create_id()
        result.id = id
        # insert new result
        new_result = result.to_dict()
        res = await ResultsAdapter.create_result(db, new_result)
        logging.debug(f"inserted result with id: {id}")
        if res:
            return id
        return None

    @classmethod
    async def get_result_by_raceclass(
        cls: Any, db: Any, event_id: str, raceclass: str
    ) -> RaceclassResult:
        """Get result function."""
        result = await ResultsAdapter.get_result_by_raceclass(db, event_id, raceclass)
        # return the document if found:
        if result:
            return RaceclassResult.from_dict(result)
        raise ResultNotFoundException(
            f"Result not found for event/raceclass {event_id}/{raceclass}"
        ) from None

    @classmethod
    async def delete_result(
        cls: Any, db: Any, event_id: str, raceclass: str
    ) -> Optional[str]:
        """Get result function."""
        # get old document
        result = await ResultsAdapter.get_result_by_raceclass(db, event_id, raceclass)
        # delete the document if found:
        if result:
            res = await ResultsAdapter.delete_result(db, result["id"])
            return res
        raise ResultNotFoundException(
            f"Result not found event/raceclass {event_id}/{raceclass}"
        ) from None
