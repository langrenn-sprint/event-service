"""Module for competition_formats service."""
from datetime import time
import logging
from typing import Any, List, Optional
import uuid

from event_service.adapters import CompetitionFormatsAdapter
from event_service.models import CompetitionFormat
from .exceptions import IllegalValueException, InvalidDateFormatException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class CompetitionFormatNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class CompetitionFormatsService:
    """Class representing a service for competition_formats."""

    @classmethod
    async def get_all_competition_formats(cls: Any, db: Any) -> List[CompetitionFormat]:
        """Get all competition_formats function."""
        competition_formats: List[CompetitionFormat] = []
        _competition_formats = (
            await CompetitionFormatsAdapter.get_all_competition_formats(db)
        )
        for e in _competition_formats:
            competition_formats.append(CompetitionFormat.from_dict(e))
        return competition_formats

    @classmethod
    async def create_competition_format(
        cls: Any, db: Any, competition_format: CompetitionFormat
    ) -> Optional[str]:
        """Create competition_format function.

        Args:
            db (Any): the db
            competition_format (CompetitionFormat): a competition_format instanse to be created

        Returns:
            Optional[str]: The id of the created competition_format. None otherwise.

        Raises:
            IllegalValueException: input object has illegal values
        """
        # Validation:
        if competition_format.id:
            raise IllegalValueException(
                "Cannot create competition_format with input id."
            ) from None
        # create id
        id = create_id()
        competition_format.id = id
        # Validation:
        await validate_competition_format(competition_format)
        # insert new competition_format
        new_competition_format = competition_format.to_dict()
        result = await CompetitionFormatsAdapter.create_competition_format(
            db, new_competition_format
        )
        logging.debug(f"inserted competition_format with id: {id}")
        if result:
            return id
        return None

    @classmethod
    async def get_competition_format_by_id(
        cls: Any, db: Any, id: str
    ) -> CompetitionFormat:
        """Get competition_format function."""
        competition_format = (
            await CompetitionFormatsAdapter.get_competition_format_by_id(db, id)
        )
        # return the document if found:
        if competition_format:
            return CompetitionFormat.from_dict(competition_format)
        raise CompetitionFormatNotFoundException(
            f"CompetitionFormat with id {id} not found"
        ) from None

    @classmethod
    async def get_competition_formats_by_name(
        cls: Any, db: Any, name: str
    ) -> List[CompetitionFormat]:
        """Get competition_format by name function."""
        competition_formats: List[CompetitionFormat] = []
        _competition_formats = (
            await CompetitionFormatsAdapter.get_competition_formats_by_name(db, name)
        )
        for e in _competition_formats:
            competition_formats.append(CompetitionFormat.from_dict(e))
        return competition_formats

    @classmethod
    async def update_competition_format(
        cls: Any, db: Any, id: str, competition_format: CompetitionFormat
    ) -> Optional[str]:
        """Get competition_format function."""
        # get old document
        old_competition_format = (
            await CompetitionFormatsAdapter.get_competition_format_by_id(db, id)
        )
        # Validate:
        await validate_competition_format(competition_format)
        # update the competition_format if found:
        if old_competition_format:
            if competition_format.id != old_competition_format["id"]:
                raise IllegalValueException(
                    "Cannot change id for competition_format."
                ) from None
            new_competition_format = competition_format.to_dict()
            result = await CompetitionFormatsAdapter.update_competition_format(
                db, id, new_competition_format
            )
            return result
        raise CompetitionFormatNotFoundException(
            f"CompetitionFormat with id {id} not found."
        ) from None

    @classmethod
    async def delete_competition_format(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get competition_format function."""
        # get old document
        competition_format = (
            await CompetitionFormatsAdapter.get_competition_format_by_id(db, id)
        )
        # delete the document if found:
        if competition_format:
            result = await CompetitionFormatsAdapter.delete_competition_format(db, id)
            return result
        raise CompetitionFormatNotFoundException(
            f"CompetitionFormat with id {id} not found"
        ) from None

    #   Validation:


async def validate_competition_format(competition_format: CompetitionFormat) -> None:
    """Validate the competition-format."""
    # Validate intervals:
    try:
        time.fromisoformat(competition_format.intervals)  # type: ignore
    except ValueError as e:
        raise InvalidDateFormatException('Time "{time_str}" has invalid format.') from e
