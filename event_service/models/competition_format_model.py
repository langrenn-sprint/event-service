"""Competition format data class module."""

from abc import ABC
from dataclasses import dataclass, field
from datetime import time

from dataclasses_json import DataClassJsonMixin
from marshmallow.fields import Constant


@dataclass
class CompetitionFormat(DataClassJsonMixin, ABC):
    """Abstract data class with details about a competition format."""

    def __post_init__(self) -> None:  # pragma: no cover
        """Prevent instantiate abstract class."""
        if self.__class__ == CompetitionFormat:
            msg = "Cannot instantiate abstract class."
            raise TypeError(msg)

    name: str
    start_procedure: str
    starting_order: str
    max_no_of_contestants_in_raceclass: int
    max_no_of_contestants_in_race: int


@dataclass
class IntervalStartFormat(CompetitionFormat, DataClassJsonMixin):
    """Data class with details about a interval start format."""

    time_between_groups: time
    intervals: time
    datatype: str = field(
        metadata=dict(marshmallow_field=Constant("interval_start")),  # noqa:C408
        default="interval_start",
    )
    id: str | None = field(default=None)


@dataclass
class RaceSetting(DataClassJsonMixin):
    """Data class with details about the settings of a race."""

    max_no_of_contestants: int
    no_of_heats: dict[str, int]
    rules: dict[str, dict[str, int | str]]


@dataclass
class IndividualSprintFormat(CompetitionFormat, DataClassJsonMixin):
    """Data class with details about a individual sprint format."""

    time_between_groups: time
    time_between_rounds: time
    time_between_heats: time
    rounds_ranked_classes: list[str]
    rounds_non_ranked_classes: list[str]
    race_config: dict[str, RaceSetting]
    datatype: str = field(
        metadata=dict(marshmallow_field=Constant("individual_sprint")),  # noqa:C408
        default="individual_sprint",
    )
    id: str | None = field(default=None)
