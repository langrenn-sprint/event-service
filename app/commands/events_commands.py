"""Module for contestants service."""

import logging
from typing import Any
from uuid import UUID

from app.adapters import ContestantsAdapter, EventsAdapter, RaceclassesConfigAdapter
from app.models import Contestant, Raceclass, RaceclassesConfig
from app.services import (
    EventNotFoundError,
    RaceclassCreateError,
    RaceclassesService,
    RaceclassNotUniqueNameError,
    RaceclassUpdateError,
)

logger = logging.getLogger(__name__)


class EventsCommands:
    """Class representing a commands on events."""

    @classmethod
    async def generate_raceclasses(cls: Any, event_id: UUID) -> None:
        """Generate raceclasses function."""
        # Check if event exists:
        event = await EventsAdapter.get_event_by_id(event_id)
        if not event:
            msg = f"Event with id {event_id} not found."
            raise EventNotFoundError(msg) from None

        # Get raceclasses configuration:
        cls.raceclasses_config = (
            await RaceclassesConfigAdapter.get_default_raceclasses_config()
        )

        # Get all contestants in event:
        contestants = await ContestantsAdapter.get_all_contestants(event_id)
        # For every contestant, create corresponding raceclass:
        for contestant in contestants:
            # Check if raceclass exist:
            raceclasses = await RaceclassesService.get_raceclass_by_ageclass_name(
                event_id, contestant.ageclass
            )
            if len(raceclasses) > 1:
                msg = f"Raceclass name {contestant.ageclass} not unique."
                raise RaceclassNotUniqueNameError(msg) from None
            if len(raceclasses) == 0:  # raceclass does not exist
                try:
                    await create_raceclass(event_id, contestant, cls.raceclasses_config)
                except RaceclassCreateError as e:
                    msg = f"Create of raceclass for contestant with id {contestant.id} failed: {e!s}"
                    raise RaceclassCreateError(msg) from e

        # Finally we assign default group and order values and sort:
        raceclasses = await RaceclassesService.get_all_raceclasses(event_id=event_id)

        # Assign default values:
        _raceclasses_with_default_values = _assign_default_values_to_raceclasses(
            raceclasses_config=cls.raceclasses_config, raceclasses=raceclasses
        )
        # Update the raceclasses:
        for raceclass in _raceclasses_with_default_values:
            if raceclass.id:
                result = await RaceclassesService.update_raceclass(
                    event_id, raceclass.id, raceclass
                )
                if not result:  # pragma: no cover
                    msg = f"Update of raceclass with id {raceclass.id} failed."
                    raise RaceclassUpdateError(msg) from None


async def create_raceclass(
    event_id: UUID, contestant: Contestant, raceclasses_config: RaceclassesConfig
) -> None:
    """Create raceclass function."""
    new_raceclass = Raceclass(
        name=assign_name(raceclasses_config, contestant.ageclass),
        gender=contestant.gender,
        ageclasses=[contestant.ageclass],
        event_id=event_id,
        ranking=True,
        seeding=False,
        distance=contestant.distance,
    )
    result = await RaceclassesService.create_raceclass(event_id, new_raceclass)
    if not result:
        msg = f"Create of raceclass with name {new_raceclass.name} failed."
        raise RaceclassCreateError(msg) from None


def assign_name(raceclasses_config: RaceclassesConfig, ageclass: str) -> str:
    """Assign a name to a raceclass based on the ageclass string."""
    raceclass_name = ageclass
    for naming_rule in raceclasses_config.naming_rules:
        raceclass_name = raceclass_name.replace(
            naming_rule, raceclasses_config.naming_rules[naming_rule]
        )
    return raceclass_name


def _assign_default_values_to_raceclasses(
    raceclasses_config: RaceclassesConfig, raceclasses: list[Raceclass]
) -> list[Raceclass]:
    """Helper function to assign default values for raceclasses.

    If anything goes wrong during sorting, the original list is returned.
    We only support grouping by same ageclasses for now.

    Args:
        raceclasses_config: Raceclasses configuration object.
        raceclasses: List of raceclass objects.

    Returns:
        List of raceclass objects with default values.

    """
    raceclasses_sorted: list[Raceclass] = raceclasses.copy()
    try:
        # Sort the raceclasses according to ageclass order and gender order:
        raceclasses_sorted = sorted(
            raceclasses,
            key=lambda raceclass: (
                raceclasses_config.ageclass_order.index(raceclass.ageclasses[0]),
                (raceclasses_config.gender_order.index(raceclass.gender)),
            ),
        )

        # Group by age and assign order in group:
        if raceclasses_config.grouping_feature != "same_age":  # pragma: no cover
            msg = f"Unsupporte grouping feature: {raceclasses_config.grouping_feature}"
            logger.warning(msg)
            return raceclasses_sorted
        current_group = 0
        current_order = 0
        previous_ageclass = None
        for raceclass in raceclasses_sorted:
            # We assume that first part of ageclasse is gender, the rest is age:
            ageclass = raceclass.ageclasses[0].split()[1:]
            if ageclass != previous_ageclass:
                current_group += 1
                current_order = 1
                raceclass.group = current_group
                raceclass.order = 1
                previous_ageclass = ageclass
            else:  # pragma: no cover
                raceclass.group = current_group
                raceclass.order = current_order + 1

        # Assign ranking=False for unranked ageclasses:
        for raceclass in raceclasses_sorted:
            if (
                raceclass.ageclasses[0] in raceclasses_config.unranked_ageclasses
            ):  # pragma: no cover
                raceclass.ranking = False
    except Exception as e:  # noqa: BLE001 # pragma: no cover
        # In case of error, return the raceclasses unsorted:
        msg = f"Error during sorting of raceclasses: {e}"
        logger.warning(msg)

    return raceclasses_sorted
