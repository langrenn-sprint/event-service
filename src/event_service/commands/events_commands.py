"""Module for contestants service."""
from typing import Any

from event_service.models import Ageclass
from event_service.services import (
    AgeclassCreateException,
    AgeclassesService,
    AgeclassNotUniqueNameException,
    AgeclassUpdateException,
    ContestantsService,
    EventNotFoundException,
    EventsService,
)


class EventsCommands:
    """Class representing a commands on events."""

    @classmethod
    async def generate_ageclasses(cls: Any, db: Any, event_id: str) -> None:
        """Create ageclasses function."""
        # Check if event exists:
        try:
            await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundException as e:
            raise e from e
        # Get all contestants in event:
        contestants = await ContestantsService.get_all_contestants(db, event_id)
        # For every contestant, create corresponding ageclass and update counter:
        for _c in contestants:
            # Check if ageclass exist:
            ageclasses = await AgeclassesService.get_ageclass_by_name(
                db, event_id, _c.ageclass
            )
            ageclass_exist = True
            if len(ageclasses) == 0:
                ageclass_exist = False
            elif len(ageclasses) > 1:
                raise AgeclassNotUniqueNameException(
                    f"Ageclass name {_c.ageclass} not unique."
                ) from None
            else:
                ageclass = ageclasses[0]
            # Update counter if found:
            if ageclass_exist and ageclass.id:
                ageclass.no_of_contestants += 1
                result = await AgeclassesService.update_ageclass(
                    db, event_id, ageclass.id, ageclass
                )
                if not result:
                    raise AgeclassUpdateException(
                        f"Create of raceclass with id {ageclass.id} failed."
                    ) from None
            # Otherwise: create
            else:
                new_ageclass = Ageclass(
                    event_id=event_id,
                    name=_c.ageclass,
                    raceclass=_create_raceclass_name(_c.ageclass),
                    distance=_c.distance,
                    no_of_contestants=1,
                )
                result = await AgeclassesService.create_ageclass(
                    db, event_id, new_ageclass
                )
                if not result:
                    raise AgeclassCreateException(
                        f"Create of raceclass with name {_c.ageclass} failed."
                    ) from None


# helpers
def _create_raceclass_name(ageclass_name: str) -> str:
    raceclass = ageclass_name.replace(" ", "")
    raceclass = raceclass.replace("Menn", "M")
    raceclass = raceclass.replace("Kvinner", "K")
    raceclass = raceclass.replace("junior", "J")
    raceclass = raceclass.replace("Junior", "J")
    raceclass = raceclass.replace("Felles", "F")
    raceclass = raceclass.replace("år", "")
    return raceclass
