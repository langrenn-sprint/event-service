"""Module for competition_formats service."""
from datetime import time
import logging
from typing import Any, List, Optional, Union
import uuid

from event_service.adapters import CompetitionFormatsAdapter
from event_service.models import (
    CompetitionFormat,
    IndividualSprintFormat,
    IntervalStartFormat,
)
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


class CompetitionFormatAllreadyExistException(Exception):
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
            if e["datatype"] == "interval_start":
                competition_formats.append(IntervalStartFormat.from_dict(e))
            elif e["datatype"] == "individual_sprint":
                competition_formats.append(IndividualSprintFormat.from_dict(e))
        _s = sorted(
            competition_formats,
            key=lambda k: (k.name,),
            reverse=False,
        )
        return _s

    @classmethod
    async def create_competition_format(
        cls: Any,
        db: Any,
        competition_format: Union[IndividualSprintFormat, IntervalStartFormat],
    ) -> Optional[str]:
        """Create competition_format function.

        Args:
            db (Any): the db
            competition_format (CompetitionFormat): a competition_format instanse to be created

        Returns:
            Optional[str]: The id of the created competition_format. None otherwise.

        Raises:
            CompetitionFormatAllreadyExistException: A format with the same name allready exist
            IllegalValueException: input object has illegal values
        """
        # Validation:
        if competition_format.id:
            raise IllegalValueException(
                "Cannot create competition_format with input id."
            ) from None
        # Check if it exists:
        _competition_formats = (
            await CompetitionFormatsAdapter.get_competition_formats_by_name(
                db, competition_format.name
            )
        )
        if _competition_formats:
            raise CompetitionFormatAllreadyExistException(
                f"Competition-format with name {competition_format.name} allready exist."
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
            if competition_format["datatype"] == "interval_start":
                return IntervalStartFormat.from_dict(competition_format)
            elif competition_format["datatype"] == "individual_sprint":
                return IndividualSprintFormat.from_dict(competition_format)
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
            if e["datatype"] == "interval_start":
                competition_formats.append(IntervalStartFormat.from_dict(e))
            elif e["datatype"] == "individual_sprint":
                competition_formats.append(IndividualSprintFormat.from_dict(e))
        return competition_formats

    @classmethod
    async def update_competition_format(
        cls: Any,
        db: Any,
        id: str,
        competition_format: Union[IndividualSprintFormat, IntervalStartFormat],
    ) -> Optional[str]:
        """Get competition_format function."""
        # Validate:
        await validate_competition_format(competition_format)
        # get old document
        old_competition_format = (
            await CompetitionFormatsAdapter.get_competition_format_by_id(db, id)
        )
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
async def validate_competition_format(  # noqa: C901
    competition_format: Union[IndividualSprintFormat, IntervalStartFormat],
) -> None:
    """Validate the competition-format."""
    # Validate time_between_groups if set:
    if hasattr(competition_format, "time_between_groups"):
        try:
            time.fromisoformat(competition_format.time_between_groups)  # type: ignore
        except ValueError as e:
            raise InvalidDateFormatException(
                f'time_between_groups "{competition_format.time_between_groups}" has invalid time format.'  # noqa: B950
            ) from e
    # Validate intervals if set:
    if type(competition_format) is IntervalStartFormat and hasattr(
        competition_format, "intervals"
    ):
        try:
            time.fromisoformat(competition_format.intervals)  # type: ignore
        except ValueError as e:
            raise InvalidDateFormatException(
                f'intervals "{competition_format.intervals}" has invalid time format.'
            ) from e
    if type(competition_format) is IndividualSprintFormat:
        # Validate time_between_rounds if set:
        if hasattr(competition_format, "time_between_rounds"):
            try:
                time.fromisoformat(competition_format.time_between_rounds)  # type: ignore
            except ValueError as e:
                raise InvalidDateFormatException(
                    f'intervals "{competition_format.time_between_rounds}" has invalid time format.'  # noqa: B950
                ) from e
        # Validate time_between_rounds if set:
        if hasattr(competition_format, "time_between_heats"):
            try:
                time.fromisoformat(competition_format.time_between_heats)  # type: ignore
            except ValueError as e:
                raise InvalidDateFormatException(
                    f'intervals "{competition_format.time_between_heats}" has invalid time format.'  # noqa: B950
                ) from e
