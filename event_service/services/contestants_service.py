"""Module for contestants service."""

import logging
import uuid
from datetime import datetime
from io import StringIO
from typing import Any

import numpy as np
import pandas as pd

from event_service.adapters import ContestantsAdapter, RaceclassesAdapter
from event_service.models import Contestant
from event_service.services.raceclasses_service import RaceclassesService
from event_service.utils.validate_ageclass import validate_ageclass

from .events_service import EventNotFoundError, EventsService
from .exceptions import (
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
    async def get_all_contestants(cls: Any, db: Any, event_id: str) -> list[Contestant]:
        """Get all contestants function."""
        _contestants = await ContestantsAdapter.get_all_contestants(db, event_id)
        contestants = [Contestant.from_dict(c) for c in _contestants]
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
    async def get_contestants_by_raceclass(
        cls: Any, db: Any, event_id: str, raceclass: str
    ) -> list[Contestant]:
        """Get all contestants function filter by raceclass."""
        # Need to get the raceclass, to get the corresponding ageclasses:
        raceclasses = await RaceclassesAdapter.get_raceclass_by_name(
            db, event_id, raceclass
        )
        if len(raceclasses) == 1:
            pass
        else:
            msg = f'Raceclass "{raceclass!r}" not found.'
            raise RaceclassNotFoundError(msg)

        _raceclass: dict = raceclasses[0]
        # Then filter contestants on ageclasses:
        _contestants = await ContestantsAdapter.get_all_contestants(db, event_id)
        contestants = [
            Contestant.from_dict(_c)
            for _c in _contestants
            if _c["ageclass"] in _raceclass["ageclasses"]
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
        cls: Any, db: Any, event_id: str, ageclass: str
    ) -> list[Contestant]:
        """Get all contestants function filter by ageclass."""
        _contestants = await ContestantsAdapter.get_all_contestants(db, event_id)
        contestants = [
            Contestant.from_dict(_c)
            for _c in _contestants
            if _c["ageclass"] == ageclass
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
    async def get_contestant_by_bib(
        cls: Any, db: Any, event_id: str, bib: int
    ) -> list[Contestant]:
        """Get all contestants by bib function."""
        contestants = []
        _contestant = await ContestantsAdapter.get_contestant_by_bib(db, event_id, bib)
        if _contestant:
            contestants.append(Contestant.from_dict(_contestant))
        return contestants

    @classmethod
    async def create_contestant(
        cls: Any, db: Any, event_id: str, contestant: Contestant
    ) -> str | None:
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
            IllegalValueError: input object has illegal values
        """
        # Validation:
        # First we have to check if the event exist:
        try:
            _ = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundError as e:
            raise e from e
        # Check if contestant exist:
        _contestant = await _contestant_exist(db, event_id, contestant)
        if _contestant:
            msg = f"Contestant with {contestant.to_dict()} allready exist in event {event_id}. "
            raise ContestantAllreadyExistError(msg)
        if contestant.id:
            msg = f"Contestant with {contestant.to_dict()} allready exist in event {event_id}. "
            raise IllegalValueError(msg) from None
        # Strip ageclass for whitespace:
        contestant.ageclass = contestant.ageclass.strip()
        # Validate:
        await _validate_contestant(db, event_id, contestant)

        # create id
        contestant_id = create_id()
        contestant.id = contestant_id
        # insert new contestant
        new_contestant = contestant.to_dict()
        result = await ContestantsAdapter.create_contestant(
            db, event_id, new_contestant
        )
        cls.logger.debug(
            f"inserted contestant with event_id/contestant_id: {event_id}/{contestant_id}"
        )
        if result:
            # Add contestant to raceclass if it exists:
            raceclasses = await RaceclassesService.get_raceclass_by_ageclass_name(
                db, event_id, contestant.ageclass
            )
            if len(raceclasses) == 1:  # pragma: no cover
                raceclass = raceclasses[0]
                raceclass.no_of_contestants += 1
                update_result = await RaceclassesService.update_raceclass(
                    db,
                    event_id,
                    raceclass.id,  # type: ignore[reportArgumentType]
                    raceclass,
                )
                if not update_result:
                    msg = f"Update of raceclass with id {raceclass.id} failed."
                    raise IllegalValueError(msg) from None
            return contestant_id
        return None

    @classmethod
    async def delete_all_contestants(cls: Any, db: Any, event_id: str) -> None:
        """Get all contestants function."""
        await ContestantsAdapter.delete_all_contestants(db, event_id)

    @classmethod
    async def create_contestants(
        cls: Any, db: Any, event_id: str, contestants: str
    ) -> dict:
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
        try:
            _ = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundError as e:
            raise e from e

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
            _c["event_id"] = event_id  # type: ignore [reportIndexIssue]
            contestant_id = create_id()
            _c["id"] = contestant_id  # type: ignore [reportIndexIssue]
            # Validate contestant:
            try:
                # datetime to string in isoformat:
                try:
                    if _c["registration_date_time"]:  # type: ignore [reportArgumentType]
                        _c["registration_date_time"] = datetime.strptime(  # noqa: DTZ007  # type: ignore [reportArgumentType]
                            _c["registration_date_time"],  # type: ignore [reportArgumentType]
                            "%d.%m.%Y %H:%M:%S",
                        ).isoformat()
                except ValueError as e:
                    msg = f"Invalid datetime format in '{_c!r}'"
                    raise IllegalValueError(msg) from e
                contestant = Contestant.from_dict(_c)
                # Strip ageclass for whitespace:
                contestant.ageclass = contestant.ageclass.strip()
                # Validate:
                await _validate_contestant(db, event_id, contestant)

                # insert new contestant
                # Check if contestant exist. If so, update:
                _existing_contestant = await _contestant_exist(db, event_id, contestant)
                if _existing_contestant:
                    updated_contestant = contestant.to_dict()
                    _result = await ContestantsAdapter.update_contestant(
                        db, event_id, _existing_contestant["id"], updated_contestant
                    )
                    cls.logger.debug(
                        f"updated event_id/contestant_id: {event_id}/{contestant_id}"
                    )
                    if _result:
                        result["updated"].append(f"contestant: {contestant.to_dict()}")
                    else:
                        result["failures"].append(
                            f"reason: {_result}: {contestant.to_dict()}"
                        )
                else:
                    new_contestant = contestant.to_dict()
                    _result = await ContestantsAdapter.create_contestant(
                        db, event_id, new_contestant
                    )
                    cls.logger.debug(
                        f"inserted event_id/contestant_id: {event_id}/{contestant_id}"
                    )
                    if _result:
                        result["created"] += 1
                    else:
                        result["failures"].append(
                            f"reason: {_result}: {contestant.to_dict()}"
                        )
            except IllegalValueError as e:
                cls.logger.exception(f"Failed to create contestant with {_c}.")
                result["failures"].append(f"reason: {e}: {_c}")
                continue

        return result

    @classmethod
    async def get_contestant_by_id(
        cls: Any, db: Any, event_id: str, contestant_id: str
    ) -> Contestant:
        """Get contestant function."""
        contestant = await ContestantsAdapter.get_contestant_by_id(
            db, event_id, contestant_id
        )
        # return the document if found:
        if not contestant:
            msg = f"Contestant with id {contestant_id} not found"
            cls.logger.error(msg)
            raise ContestantNotFoundError(msg) from None

        return Contestant.from_dict(contestant)

    @classmethod
    async def update_contestant(
        cls: Any,
        db: Any,
        event_id: str,
        contestant_id: str,
        contestant: Contestant,
    ) -> str | None:
        """Update contestant function."""
        # get old document
        old_contestant = await ContestantsAdapter.get_contestant_by_id(
            db, event_id, contestant_id
        )
        # update the contestant if found:
        if not old_contestant:
            msg = f"Contestant with id {contestant_id} not found."
            raise ContestantNotFoundError(msg) from None

        # Strip ageclass for whitespace:
        contestant.ageclass = contestant.ageclass.strip()
        # Validate:
        await _validate_contestant(db, event_id, contestant)
        if contestant.id != old_contestant["id"]:
            msg = f"Cannot change id for contestant with id {contestant_id}."
            raise IllegalValueError(msg) from None
        new_contestant = contestant.to_dict()
        # If ageclass has changed, need to update raceclass contestant counters:
        if old_contestant["ageclass"] != new_contestant["ageclass"]:
            # Decrease counter in old raceclass:
            old_raceclasses = await RaceclassesService.get_raceclass_by_ageclass_name(
                db, event_id, old_contestant["ageclass"]
            )
            if len(old_raceclasses) == 1:  # pragma: no cover
                old_raceclass = old_raceclasses[0]
                old_raceclass.no_of_contestants -= 1
                update_result = await RaceclassesService.update_raceclass(
                    db,
                    event_id,
                    old_raceclass.id,  # type: ignore[reportArgumentType]
                    old_raceclass,
                )
                if not update_result:
                    msg = f"Update of raceclass with id {old_raceclass.id} failed."
                    raise IllegalValueError(msg) from None
            # Increase counter in new raceclass:
            new_raceclasses = await RaceclassesService.get_raceclass_by_ageclass_name(
                db, event_id, contestant.ageclass
            )
            if len(new_raceclasses) == 1:  # pragma: no cover
                new_raceclass = new_raceclasses[0]
                new_raceclass.no_of_contestants += 1
                update_result = await RaceclassesService.update_raceclass(
                    db,
                    event_id,
                    new_raceclass.id,  # type: ignore[reportArgumentType]
                    new_raceclass,
                )
                if not update_result:
                    msg = f"Update of raceclass with id {new_raceclass.id} failed."
                    raise IllegalValueError(msg) from None
        return await ContestantsAdapter.update_contestant(
            db, event_id, contestant_id, new_contestant
        )

    @classmethod
    async def delete_contestant(
        cls: Any, db: Any, event_id: str, contestant_id: str
    ) -> str | None:
        """Get contestant function."""
        # get old document
        contestant = await ContestantsAdapter.get_contestant_by_id(
            db, event_id, contestant_id
        )
        # delete the document if found:
        if not contestant:
            msg = f"Contestant with id {contestant_id} not found"
            raise ContestantNotFoundError(msg) from None

        result = await ContestantsAdapter.delete_contestant(db, event_id, contestant_id)
        # Remove contestant from raceclass if it exists:
        raceclasses = await RaceclassesService.get_raceclass_by_ageclass_name(
            db, event_id, contestant["ageclass"]
        )
        if len(raceclasses) == 1:  # pragma: no cover
            raceclass = raceclasses[0]
            raceclass.no_of_contestants -= 1
            update_result = await RaceclassesService.update_raceclass(
                db,
                event_id,
                raceclass.id,  # type: ignore[reportArgumentType]
                raceclass,
            )
            if not update_result:
                msg = f"Update of raceclass with id {raceclass.id} failed."
                raise IllegalValueError(msg) from None
        return result


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
        contestants_df = pd.read_csv(  # noqa: PGH003 # type: ignore
            StringIO(contestants),
            sep=";",
            encoding="utf-8",
            dtype=str,
            skiprows=2,
            header=0,
            usecols=cols,  # noqa: PGH003 # type: ignore
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
        contestants_df = pd.read_csv(  # noqa: PGH003 # type: ignore
            StringIO(contestants),
            sep=";",
            encoding="utf-8",
            dtype=str,
            header=0,
            usecols=cols,  # noqa: PGH003 # type: ignore
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
        contestants_df["registration_date_time"] = (  # type: ignore [reportArgumentType]
            contestants_df["registration_date"]  # type: ignore [reportArgumentType]
            + " "
            + contestants_df["registration_time"]  # type: ignore [reportArgumentType]
            + ":00"
        )

    except ValueError as e:
        msg = f"Failed to parse contestants. Please check format. Reason: {e}"
        raise IllegalValueError(msg) from e

    return contestants_df


async def _contestant_exist(
    db: Any, event_id: str, contestant: Contestant
) -> dict | None:
    """Checks if contestant exist and return id if it does. None otherwise."""
    # if contestant has minidrett_id:
    if contestant.minidrett_id:
        _result = await ContestantsAdapter.get_contestant_by_minidrett_id(
            db, event_id, contestant.minidrett_id
        )
    else:
        _result = await ContestantsAdapter.get_contestant_by_name(
            db, event_id, contestant.first_name, contestant.last_name
        )
    if _result:
        return _result
    return None


async def _validate_contestant(db: Any, event_id: str, contestant: Contestant) -> None:
    """Validate contestant."""
    # Check that ageclass is valid:
    await validate_ageclass(contestant.ageclass)

    # Check that bib is in use by another contestant:
    if await _bib_in_use_by_another_contestant(db, event_id, contestant):
        msg = f"Bib {contestant.bib} allready in use by another contestant."
        raise BibAlreadyInUseError(msg)


async def _bib_in_use_by_another_contestant(
    db: Any, event_id: str, contestant: Contestant
) -> bool:
    """Checks if bib is in use by another contestants."""
    # if contestant has minidrett_id:
    if not contestant.bib:
        return False

    _contestant = await ContestantsAdapter.get_contestant_by_bib(
        db, event_id, contestant.bib
    )

    if not _contestant:
        return False
    return _contestant["id"] != contestant.id
