"""Module for contestants service."""

from random import shuffle
from typing import Any

from event_service.services import (
    ContestantsService,
    EventNotFoundError,
    EventsService,
    IllegalValueError,
    RaceclassesService,
)


class NoRaceclassInEventError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class NoValueForOrderInRaceclassError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class NoValueForGroupInRaceclassError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantsCommands:
    """Class representing a commands on contestants."""

    @classmethod
    async def assign_bibs(cls: Any, db: Any, event_id: str) -> None:  # noqa: C901
        """Assign bibs function.

        This function will
        - sort list of contestants in random order, and
        - sort the resulting list on the raceclass of the contestant
        - assign bibs in ascending order.

        Arguments:
            db: the database to use
            event_id: the id of the event

        Raises:
            EventNotFoundError: event not found
            IllegalValueError: an illegal value is specified for the contestant
            NoRaceclassInEventError: there are no raceclasses in event
            NoValueForGroupInRaceclassError: raceclass does not have value for group
            NoValueForOrderInRaceclassError: raceclass does not have value for order
        """
        # Check if event exists:
        try:
            await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundError as e:
            raise e from e

        # Get the raceclasses:
        raceclasses = await RaceclassesService.get_all_raceclasses(db, event_id)
        if len(raceclasses) == 0:
            msg = f"Event {event_id} has no raceclasses. Not able to assign bibs."
            raise NoRaceclassInEventError(msg) from None

        # Check if all raceclasses has value for group:
        for raceclass in raceclasses:
            if not raceclass.group:
                msg = f"Raceclass {raceclass.name} does not have value for group."
                raise NoValueForGroupInRaceclassError(msg)
        # Check if all raceclasses has value for order:
        for raceclass in raceclasses:
            if not raceclass.order:
                msg = f"Raceclass {raceclass.name} does not have value for order."
                raise NoValueForOrderInRaceclassError(msg)
        # Get all contestants in event:
        contestants = await ContestantsService.get_all_contestants(db, event_id)

        # Sort list of contestants in random order:
        shuffle(contestants)

        # Create temporary list, lookup correct raceclasses, and convert to dict:
        _list: list[dict] = []
        for c in contestants:
            c_dict = c.to_dict()
            try:
                c_dict["raceclass_group"] = next(
                    item
                    for item in raceclasses
                    if c_dict["ageclass"] in item.ageclasses
                ).group
                c_dict["raceclass_order"] = next(
                    item
                    for item in raceclasses
                    if c_dict["ageclass"] in item.ageclasses
                ).order
                _list.append(c_dict)
            except StopIteration as e:
                msg = f"Ageclass {c_dict['ageclass']!r} not found in raceclasses."
                raise IllegalValueError(msg) from e

        # Sort on racelass_group and racelass_order:
        _list_sorted_on_raceclass = sorted(
            _list, key=lambda k: (k["raceclass_group"], k["raceclass_order"])
        )
        # For every contestant, assign unique bib
        bib_no = 0
        for d in _list_sorted_on_raceclass:
            bib_no += 1  # noqa: SIM113
            d["bib"] = bib_no

        # finally update contestant record:
        for _c in contestants:
            c_with_bib = next(
                item for item in _list_sorted_on_raceclass if item["id"] == _c.id
            )
            _c.bib = c_with_bib["bib"]
            if _c.bib is None:  # pragma: no cover
                msg = f"Bib number not assigned for contestant with id {_c.id}"
                raise ValueError(msg)
            await ContestantsService.update_contestant(db, event_id, _c.id, _c) # type: ignore [reportArgumentType]
