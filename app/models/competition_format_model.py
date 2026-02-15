"""Competition format model module."""

from abc import ABC
from datetime import timedelta
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompetitionFormat(BaseModel, ABC):
    """Abstract model with details about a competition-format."""

    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: UUID
    name: str
    start_procedure: str
    starting_order: str
    max_no_of_contestants_in_raceclass: int
    max_no_of_contestants_in_race: int
    time_between_groups: timedelta


class IntervalStartFormat(CompetitionFormat):
    """Model with details about a interval start format."""

    datatype: Literal["interval_start"] = "interval_start"

    intervals: timedelta


class RaceConfig(BaseModel):
    """Model with details about the settings of a race."""

    max_no_of_contestants: Annotated[int, Field(gt=0)]
    rounds: list[str]
    no_of_heats: dict[str, dict[str, int]]
    from_to: dict[str, dict[str, dict[str, dict[str, int | str]]]]


class IndividualSprintFormat(CompetitionFormat):
    """Model with details about a individual sprint format."""

    datatype: Literal["individual_sprint"] = "individual_sprint"

    time_between_rounds: timedelta
    time_between_heats: timedelta
    rounds_ranked_classes: list[str]
    rounds_non_ranked_classes: list[str]
    race_config_ranked: list[RaceConfig]
    race_config_non_ranked: list[RaceConfig]


CompetitionFormatUnion = Annotated[
    IntervalStartFormat | IndividualSprintFormat, Field(discriminator="datatype")
]
