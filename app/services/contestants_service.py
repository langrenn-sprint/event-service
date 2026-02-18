"""Module for contestants service."""

import logging
import uuid
from datetime import datetime
from io import StringIO
from typing import Any
from uuid import UUID

import numpy as np
import pandas as pd
from pydantic import ValidationError

from app.adapters import ContestantsAdapter, EventsAdapter, RaceclassesAdapter
from app.models import Contestant, Raceclass
from app.services.events_service import EventNotFoundError
from app.services.exceptions import (
    BibAlreadyInUseError,
    IllegalValueError,
    RaceclassNotFoundError,
)


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class ContestantNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantAllreadyExistError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantsService:
    """Class representing a service for contestants."""

    logger = logging.getLogger("event_service.services.contestants_service")

    @classmethod
    async def get_contestants_by_raceclass(
        cls: Any, event_id: UUID, raceclass_name: str
    ) -> list[Contestant]:
        """Get all contestants function filter by raceclass."""
        # Need to get the raceclass, to get the corresponding ageclasses:
        raceclasses = await RaceclassesAdapter.get_raceclass_by_name(
            event_id, raceclass_name
        )
        if len(raceclasses) == 1:
            pass
        else:
            msg = f'Raceclass with "{raceclass_name!r}" not found.'
            raise RaceclassNotFoundError(msg)

        _raceclass: Raceclass = raceclasses[0]
        # Then filter contestants on ageclasses:
        _contestants = await ContestantsAdapter.get_all_contestants(event_id)
        contestants = [
            contestant
            for contestant in _contestants
            if contestant.ageclass in _raceclass.ageclasses
        ]

        # We sort the list on bib, ageclass, last- and first-name:
        return sorted(
            contestants,
            key=lambda k: (
                k.bib is not None,
                k.bib != "",
                k.bib,
                k.ageclass,
                k.last_name,
                k.first_name,
            ),
            reverse=False,
        )

    @classmethod
    async def get_contestants_by_ageclass(
        cls: Any, event_id: UUID, ageclass: str
    ) -> list[Contestant]:
        """Get all contestants function filter by ageclass."""
        _contestants = await ContestantsAdapter.get_all_contestants(event_id)
        contestants = [
            contestant for contestant in _contestants if contestant.ageclass == ageclass
        ]
        return sorted(
            contestants,
            key=lambda k: (
                k.bib is not None,
                k.bib != "",
                k.bib,
                k.ageclass,
                k.last_name,
                k.first_name,
            ),
            reverse=False,
        )

    @classmethod
    async def create_contestant(
        cls: Any, event_id: UUID, contestant: Contestant
    ) -> UUID | None:
        """Create contestant function.

        Args:
            db (Any): the db
            event_id (str): identifier of the event the contestant takes part in
            contestant (Contestant): a contestant instanse to be created

        Returns:
            Optional[str]: The id of the created contestant. None otherwise.

        Raises:
            EventNotFoundError: event does not exist
            ContestantAllreadyExistError: contestant allready exists
        """
        # Validation:
        # First we have to check if the event exist:
        event = await EventsAdapter.get_event_by_id(event_id)
        if not event:
            msg = f"Event with id {event_id} not found."
            raise EventNotFoundError(msg) from None
        # Check if contestant exist:
        _contestant = await _contestant_exist(event_id, contestant)
        if _contestant:
            msg = (
                f"Contestant with {contestant.id} allready exist in event {event_id}. "
            )
            raise ContestantAllreadyExistError(msg)
        # Strip ageclass for whitespace:
        contestant.ageclass = contestant.ageclass.strip()
        # Validate:
        await _validate_contestant(event_id, contestant)

        # insert new contestant
        result = await ContestantsAdapter.create_contestant(event_id, contestant)
        cls.logger.debug(
            f"inserted contestant with event_id/contestant_id: {event_id}/{contestant.id}"
        )
        if result:
            return contestant.id
        return None

    @classmethod
    async def create_contestants(cls: Any, event_id: UUID, contestants: str) -> dict:
        """Create contestants function.

        Args:
            db (Any): the db
            event_id (str): identifier of the event the contestant takes part in
            contestants (str): a csv file as str

        Returns:
            dict: A short report of created, updated or failed attempts.

        Raises:
            EventNotFoundError: event does not exist
            IllegalValueError: input object has illegal values
        """
        # First we have to check if the event exist:

        event = await EventsAdapter.get_event_by_id(event_id)
        if not event:
            msg = f"Event with id {event_id} not found."
            raise EventNotFoundError(msg) from None

        try:
            contestants_frame = await parse_contestants(contestants)
        except IllegalValueError as e:
            raise e from e

        # Need to replace nans with None:
        contestants_frame = contestants_frame.replace({np.nan: None})

        contestants_dict = contestants_frame.to_dict("records")
        # For every record, create contestant:
        # TODO: consider parallellizing this # noqa: FIX002, TD002, TD003
        # create id
        result: dict[str, Any] = {
            "total": 0,
            "created": 0,
            "updated": [],
            "failures": [],
        }
        for _c in contestants_dict:
            result["total"] += 1
            _c["event_id"] = event_id
            # Validate contestant:
            try:
                # datetime to string in isoformat:
                try:
                    if _c["registration_date_time"]:
                        _c["registration_date_time"] = datetime.strptime(  # noqa: DTZ007
                            _c["registration_date_time"],
                            "%d.%m.%Y %H:%M:%S",
                        ).isoformat()
                except ValueError as e:
                    msg = f"Invalid datetime format in '{_c!r}'"
                    raise IllegalValueError(msg) from e
                contestant = Contestant.model_validate(_c)
                # Strip ageclass for whitespace:
                contestant.ageclass = contestant.ageclass.strip()
                # Validate:
                await _validate_contestant(event_id, contestant)

                # insert new contestant
                # Check if contestant exist. If so, update:
                _existing_contestant = await _contestant_exist(event_id, contestant)
                if _existing_contestant:
                    updated_contestant = contestant
                    _result = await ContestantsAdapter.update_contestant(
                        event_id, _existing_contestant.id, updated_contestant
                    )
                    cls.logger.debug(
                        f"updated event_id/contestant_id: {event_id}/{contestant.id}"
                    )
                    if _result:
                        result["updated"].append(
                            f"contestant: {contestant.model_dump()}"
                        )
                    else:
                        result["failures"].append(
                            f"reason: {_result}: {contestant.model_dump()}"
                        )
                else:
                    new_contestant = contestant
                    _result = await ContestantsAdapter.create_contestant(
                        event_id, new_contestant
                    )
                    cls.logger.debug(
                        f"inserted event_id/contestant_id: {event_id}/{contestant.id}"
                    )
                    if _result:
                        result["created"] += 1
                    else:
                        result["failures"].append(
                            f"reason: {_result}: {contestant.model_dump()}"
                        )
            except (IllegalValueError, ValidationError) as e:
                cls.logger.exception(f"Failed to create contestant with {_c}.")
                result["failures"].append(f"reason: {e}: {_c}")
                continue

        return result

    @classmethod
    async def update_contestant(
        cls: Any,
        event_id: UUID,
        contestant_id: UUID,
        contestant: Contestant,
    ) -> str | None:
        """Update contestant function."""
        # get old document
        old_contestant = await ContestantsAdapter.get_contestant_by_id(
            event_id, contestant_id
        )
        # update the contestant if found:
        if not old_contestant:
            msg = f"Contestant with id {contestant_id} not found."
            raise ContestantNotFoundError(msg) from None

        # Strip ageclass for whitespace:
        contestant.ageclass = contestant.ageclass.strip()
        # Validate:
        await _validate_contestant(event_id, contestant)
        if contestant.id != old_contestant.id:
            msg = f"Cannot change id for contestant with id {contestant_id}."
            raise IllegalValueError(msg) from None
        return await ContestantsAdapter.update_contestant(
            event_id, contestant_id, contestant
        )

    @classmethod
    async def delete_contestant(
        cls: Any, event_id: UUID, contestant_id: UUID
    ) -> str | None:
        """Get contestant function."""
        # get old document
        contestant = await ContestantsAdapter.get_contestant_by_id(
            event_id, contestant_id
        )
        # delete the document if found:
        if not contestant:
            msg = f"Contestant with id {contestant_id} not found"
            raise ContestantNotFoundError(msg) from None

        return await ContestantsAdapter.delete_contestant(event_id, contestant_id)


# -- helper methods


async def parse_contestants(contestants: str) -> pd.DataFrame:
    """Parse contestants from csv."""
    # We try to parse the contestants as csv, Sportsadmin format:
    try:
        return await _parse_contestants_sportsadmin(contestants)
    except IllegalValueError:
        # Try a iSonen format:
        try:
            return await _parse_contestants_i_sonen(contestants)
        except IllegalValueError as e:
            raise e from e


async def _parse_contestants_sportsadmin(contestants: str) -> pd.DataFrame:
    """Parse contestants from csv, Sportsadmin format."""
    try:
        cols = [
            "Klasse",
            "Øvelse",
            "Etternavn",
            "Fornavn",
            "Kjønn",
            "Fødselsdato",
            "Idrettsnr",
            "E-post",
            "Org.tilhørighet",
            "Krets/region",
            "Team",
            "Betalt/påmeldt dato",
        ]
        contestants_df = pd.read_csv(
            StringIO(contestants),
            sep=";",
            encoding="utf-8",
            dtype=str,
            skiprows=2,
            header=0,
            usecols=cols,
        )
        contestants_df.columns = [
            "ageclass",
            "distance",
            "last_name",
            "first_name",
            "gender",
            "birth_date",
            "minidrett_id",
            "email",
            "club",
            "region",
            "team",
            "registration_date_time",
        ]
    except ValueError as e:
        msg = f"Failed to parse contestants. Please check format. Reason: {e}"
        raise IllegalValueError(msg) from e

    return contestants_df


async def _parse_contestants_i_sonen(contestants: str) -> pd.DataFrame:
    """Parse contestants from csv, iSonen format."""
    try:
        cols = [
            "Fornavn",
            "Etternavn",
            "Kjønn",
            "Fødselsdato",
            "Person ID",
            "E-post",
            "Klubb",
            "Krets/region",
            "Team",
            "Påmeldt dato",
            "Påmeldt kl.",
            "Klasse",
            "Øvelse",
        ]
        contestants_df = pd.read_csv(
            StringIO(contestants),
            sep=";",
            encoding="utf-8",
            dtype=str,
            header=0,
            usecols=cols,
        )
        # Need to map column names to dataclass:
        contestants_df.rename(
            columns={
                "Fornavn": "first_name",
                "Etternavn": "last_name",
                "Kjønn": "gender",
                "Fødselsdato": "birth_date",
                "Person ID": "minidrett_id",
                "E-post": "email",
                "Klubb": "club",
                "Krets/region": "region",
                "Team": "team",
                "Påmeldt dato": "registration_date",
                "Påmeldt kl.": "registration_time",
                "Klasse": "ageclass",
                "Øvelse": "distance",
            },
            inplace=True,  # noqa: PD002
        )
        # We need to combine registration_date and registration_time to one column:
        contestants_df["registration_date_time"] = (
            contestants_df["registration_date"]
            + " "
            + contestants_df["registration_time"]
            + ":00"
        )

    except ValueError as e:
        msg = f"Failed to parse contestants. Please check format. Reason: {e}"
        raise IllegalValueError(msg) from e

    return contestants_df


async def _contestant_exist(
    event_id: UUID, contestant: Contestant
) -> Contestant | None:
    """Checks if contestant exist and return id if it does. None otherwise."""
    # if contestant has minidrett_id:
    if contestant.minidrett_id:
        _result = await ContestantsAdapter.get_contestant_by_minidrett_id(
            event_id, contestant.minidrett_id
        )
    else:
        _result = await ContestantsAdapter.get_contestant_by_name(
            event_id, contestant.first_name, contestant.last_name
        )
    if _result:
        return _result
    return None


async def _validate_contestant(event_id: UUID, contestant: Contestant) -> None:
    """Validate contestant."""
    # Check that bib is in use by another contestant:
    if await _bib_in_use_by_another_contestant(event_id, contestant):
        msg = f"Bib {contestant.bib} allready in use by another contestant."
        raise BibAlreadyInUseError(msg)


async def _bib_in_use_by_another_contestant(
    event_id: UUID, contestant: Contestant
) -> bool:
    """Checks if bib is in use by another contestants."""
    # if contestant has minidrett_id:
    if not contestant.bib:
        return False

    _contestant = await ContestantsAdapter.get_contestant_by_bib(
        event_id, contestant.bib
    )
    if not _contestant:
        return False
    return _contestant.id != contestant.id
