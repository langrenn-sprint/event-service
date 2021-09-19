"""Module for contestants service."""
from typing import Any

from event_service.models import Contestant, Raceclass
from event_service.services import (
    ContestantsService,
    EventNotFoundException,
    EventsService,
    RaceclassCreateException,
    RaceclassesService,
    RaceclassNotUniqueNameException,
    RaceclassUpdateException,
)


class EventsCommands:
    """Class representing a commands on events."""

    @classmethod
    async def generate_raceclasses(cls: Any, db: Any, event_id: str) -> None:
        """Create raceclasses function."""
        # Check if event exists:
        try:
            await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundException as e:
            raise e from e
        # Get all contestants in event:
        contestants = await ContestantsService.get_all_contestants(db, event_id)
        # For every contestant, create corresponding raceclass and update counter:
        for _c in contestants:
            # Check if raceclass exist:
            raceclasses = await RaceclassesService.get_raceclass_by_ageclass_name(
                db, event_id, _c.ageclass
            )
            raceclass_exist = True
            if len(raceclasses) == 0:
                raceclass_exist = False
            elif len(raceclasses) > 1:
                raise RaceclassNotUniqueNameException(
                    f"Raceclass name {_c.ageclass} not unique."
                ) from None
            else:
                raceclass = raceclasses[0]
            # Update counter if found:
            if raceclass_exist and raceclass.id:
                raceclass.no_of_contestants += 1
                result = await RaceclassesService.update_raceclass(
                    db, event_id, raceclass.id, raceclass
                )
                if not result:
                    raise RaceclassUpdateException(
                        f"Create of raceclass with id {raceclass.id} failed."
                    ) from None
            # Otherwise: create
            else:
                new_raceclass = Raceclass(
                    event_id=event_id,
                    name=_create_raceclass_name(_c),
                    ageclass_name=_c.ageclass,
                    distance=_c.distance,
                    no_of_contestants=1,
                )
                result = await RaceclassesService.create_raceclass(
                    db, event_id, new_raceclass
                )
                if not result:
                    raise RaceclassCreateException(
                        f"Create of raceclass with name {new_raceclass.name} failed."
                    ) from None


# helpers
def _create_raceclass_name(contestant: Contestant) -> str:
    """Helper function to create name of raceclass."""
    name = contestant.ageclass.replace(" ", "")
    name = name.replace("Menn", "M")
    name = name.replace("Kvinner", "K")
    name = name.replace("junior", "J")
    name = name.replace("Junior", "J")
    name = name.replace("Felles", "F")
    name = name.replace("år", "")
    return name
