"""Module for contestants service."""
from io import StringIO
import logging
from typing import Any, Dict, List, Optional
import uuid

import numpy as np
import pandas as pd

from event_service.adapters import ContestantsAdapter, RaceclassesAdapter
from event_service.models import Contestant
from .events_service import EventNotFoundException, EventsService
from .exceptions import IllegalValueException, RaceclassNotFoundException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class ContestantNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantAllreadyExistException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantsService:
    """Class representing a service for contestants."""

    @classmethod
    async def get_all_contestants(cls: Any, db: Any, event_id: str) -> List[Contestant]:
        """Get all contestants function."""
        contestants = []
        _contestants = await ContestantsAdapter.get_all_contestants(db, event_id)
        for c in _contestants:
            contestants.append(Contestant.from_dict(c))
        _s = sorted(
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
        return _s

    @classmethod
    async def get_contestants_by_raceclass(
        cls: Any, db: Any, event_id: str, raceclass: str
    ) -> List[Contestant]:
        """Get all contestants function filter by raceclass."""
        contestants = []
        # Need to get the raceclass, to get the corresponding ageclasses:
        raceclasses = await RaceclassesAdapter.get_raceclass_by_name(
            db, event_id, raceclass
        )
        if raceclasses == []:
            raise RaceclassNotFoundException(f'Raceclass "{raceclass}" not found.')
        # FIXME: this has to change when ageclass_anme on raceclass becomes a list
        ageclasses = [raceclass["ageclass_name"] for raceclass in raceclasses]
        # Then filter contestants on ageclasses:
        _contestants = await ContestantsAdapter.get_all_contestants(db, event_id)
        for _c in _contestants:
            if _c["ageclass"] in ageclasses:
                contestants.append(Contestant.from_dict(_c))
        _s = sorted(
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
        return _s

    @classmethod
    async def get_contestants_by_ageclass(
        cls: Any, db: Any, event_id: str, ageclass: str
    ) -> List[Contestant]:
        """Get all contestants function filter by ageclass."""
        contestants = []
        _contestants = await ContestantsAdapter.get_all_contestants(db, event_id)
        for _c in _contestants:
            if _c["ageclass"] == ageclass:
                contestants.append(Contestant.from_dict(_c))
        _s = sorted(
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
        return _s

    @classmethod
    async def get_contestant_by_bib(
        cls: Any, db: Any, event_id: str, bib: int
    ) -> List[Contestant]:
        """Get all contestants by bib function."""
        contestants = []
        _contestant = await ContestantsAdapter.get_contestant_by_bib(db, event_id, bib)
        if _contestant:
            contestants.append(Contestant.from_dict(_contestant))
        return contestants

    @classmethod
    async def create_contestant(
        cls: Any, db: Any, event_id: str, contestant: Contestant
    ) -> Optional[str]:
        """Create contestant function.

        Args:
            db (Any): the db
            event_id (str): identifier of the event the contestant takes part in
            contestant (Contestant): a contestant instanse to be created

        Returns:
            Optional[str]: The id of the created contestant. None otherwise.

        Raises:
            EventNotFoundException: event does not exist
            ContestantAllreadyExistException: contestant allready exists
            IllegalValueException: input object has illegal values
        """
        # Validation:
        # First we have to check if the event exist:
        try:
            _ = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundException as e:
            raise e from e
        # Check if contestant exist:
        _contestant = await _contestant_exist(db, event_id, contestant)
        if _contestant:
            raise ContestantAllreadyExistException(
                f"Contestant with {contestant.to_dict()} allready exist in event {event_id}. "
            )
        if contestant.id:
            raise IllegalValueException(
                "Cannot create contestant with input id."
            ) from None
        # create id
        contestant_id = create_id()
        contestant.id = contestant_id
        # insert new contestant
        new_contestant = contestant.to_dict()
        result = await ContestantsAdapter.create_contestant(
            db, event_id, new_contestant
        )
        logging.debug(
            f"inserted contestant with event_id/contestant_id: {event_id}/{contestant_id}"
        )
        if result:
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
            EventNotFoundException: event does not exist
        """
        # First we have to check if the event exist:
        try:
            _ = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundException as e:
            raise e from e
        # Parse str as csv:
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
        ]
        df = pd.read_csv(
            StringIO(contestants),
            sep=";",
            encoding="utf-8",
            dtype=str,
            skiprows=2,
            header=0,
            usecols=cols,
        )

        df.columns = [
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
        ]

        # Need to replace nans with None:
        df = df.replace({np.nan: None})

        contestants = df.to_dict("records")
        # For every record, create contestant:
        # TODO: consider parallellizing this
        # create id
        result: Dict[str, int] = {"total": 0, "created": 0, "updated": 0, "failures": 0}
        for _c in contestants:
            result["total"] += 1
            _c["event_id"] = event_id  # type: ignore
            contestant_id = create_id()
            _c["id"] = contestant_id  # type: ignore
            contestant = Contestant.from_dict(_c)
            # insert new contestant
            # Check if contestant exist. If so, update:
            _contestant = await _contestant_exist(db, event_id, contestant)
            if _contestant:
                updated_contestant = contestant.to_dict()
                _result = await ContestantsAdapter.update_contestant(
                    db, event_id, _contestant["id"], updated_contestant
                )
                logging.debug(
                    f"updated event_id/contestant_id: {event_id}/{contestant_id}"
                )
                if _result:
                    result["updated"] += 1
                else:
                    result["failures"] += 1
            else:
                new_contestant = contestant.to_dict()
                _result = await ContestantsAdapter.create_contestant(
                    db, event_id, new_contestant
                )
                logging.debug(
                    f"inserted event_id/contestant_id: {event_id}/{contestant_id}"
                )
                if _result:
                    result["created"] += 1
                else:
                    result["failures"] += 1

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
        if contestant:
            return Contestant.from_dict(contestant)
        raise ContestantNotFoundException(
            f"Contestant with id {contestant_id} not found"
        ) from None

    @classmethod
    async def update_contestant(
        cls: Any, db: Any, event_id: str, contestant_id: str, contestant: Contestant
    ) -> Optional[str]:
        """Get contestant function."""
        # get old document
        old_contestant = await ContestantsAdapter.get_contestant_by_id(
            db, event_id, contestant_id
        )
        # update the contestant if found:
        if old_contestant:
            if contestant.id != old_contestant["id"]:
                raise IllegalValueException(
                    "Cannot change id for contestant."
                ) from None
            new_contestant = contestant.to_dict()
            result = await ContestantsAdapter.update_contestant(
                db, event_id, contestant_id, new_contestant
            )
            return result
        raise ContestantNotFoundException(
            f"Contestant with id {contestant_id} not found."
        ) from None

    @classmethod
    async def delete_contestant(
        cls: Any, db: Any, event_id: str, contestant_id: str
    ) -> Optional[str]:
        """Get contestant function."""
        # get old document
        contestant = await ContestantsAdapter.get_contestant_by_id(
            db, event_id, contestant_id
        )
        # delete the document if found:
        if contestant:
            result = await ContestantsAdapter.delete_contestant(
                db, event_id, contestant_id
            )
            return result
        raise ContestantNotFoundException(
            f"Contestant with id {contestant_id} not found"
        ) from None

    # -- helper methods


async def _contestant_exist(
    db: Any, event_id: str, contestant: Contestant
) -> Optional[dict]:
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