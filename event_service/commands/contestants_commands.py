"""Module for contestants service."""
from random import shuffle
from typing import Any, List

from event_service.services import (
    ContestantsService,
    EventNotFoundException,
    EventsService,
    IllegalValueException,
    RaceclassesService,
)


class NoRaceclassInEventException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class NoValueForOrderInRaceclassExcpetion(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class NoValueForGroupInRaceclassExcpetion(Exception):
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
            EventNotFoundException: event not found
            IllegalValueException: an illegal value is specified for the contestant
            NoRaceclassInEventException: there are no raceclasses in event
            NoValueForGroupInRaceclassExcpetion: raceclass does not have value for group
            NoValueForOrderInRaceclassExcpetion: raceclass does not have value for order
        """
        # Check if event exists:
        try:
            await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundException as e:
            raise e from e

        # Get the raceclasses:
        raceclasses = await RaceclassesService.get_all_raceclasses(db, event_id)
        if len(raceclasses) == 0:
            raise NoRaceclassInEventException(
                f"Event {event_id} has no raceclasses. Not able to assign bibs."
            ) from None

        # Check if all raceclasses has value for group:
        for raceclass in raceclasses:
            if not raceclass.group:
                raise NoValueForGroupInRaceclassExcpetion(
                    f"Raceclass {raceclass.name} does not have value for group."
                )
        # Check if all raceclasses has value for order:
        for raceclass in raceclasses:
            if not raceclass.order:
                raise NoValueForOrderInRaceclassExcpetion(
                    f"Raceclass {raceclass.name} does not have value for order."
                )
        # Get all contestants in event:
        contestants = await ContestantsService.get_all_contestants(db, event_id)

        # Sort list of contestants in random order:
        shuffle(contestants)

        # Create temporary list, lookup correct raceclasses, and convert to dict:
        _list: List[dict] = list()
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
                raise IllegalValueException(
                    f"Ageclass {c_dict['ageclass']!r} not found in raceclasses."
                ) from e

        # Sort on racelass_group and racelass_order:
        _list_sorted_on_raceclass = sorted(
            _list, key=lambda k: (k["raceclass_group"], k["raceclass_order"])
        )
        # For every contestant, assign unique bib
        bib_no = 0
        for d in _list_sorted_on_raceclass:
            bib_no += 1
            d["bib"] = bib_no

        # finally update contestant record:
        for _c in contestants:
            c_with_bib = next(
                item for item in _list_sorted_on_raceclass if item["id"] == _c.id
            )
            _c.bib = c_with_bib["bib"]
            assert _c.id is not None
            await ContestantsService.update_contestant(db, event_id, _c.id, _c)
