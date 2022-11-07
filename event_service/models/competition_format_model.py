"""Competition format data class module."""
from abc import ABC
from dataclasses import dataclass, field
from datetime import time
from typing import Dict, List, Optional, Union

from dataclasses_json import DataClassJsonMixin
from marshmallow.fields import Constant


@dataclass
class CompetitionFormat(DataClassJsonMixin, ABC):  # noqa: B024
    """Abstract data class with details about a competition format."""

    def __post_init__(self) -> None:  # pragma: no cover
        """Prevent instantiate abstract class."""
        if self.__class__ == CompetitionFormat:
            raise TypeError("Cannot instantiate abstract class.")

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
        metadata=dict(marshmallow_field=Constant("interval_start")),
        default="interval_start",
    )
    id: Optional[str] = field(default=None)


@dataclass
class RaceSetting(DataClassJsonMixin):
    """Data class with details about the settings of a race."""

    max_no_of_contestants: int
    no_of_heats: Dict[str, int]
    rules: Dict[str, Dict[str, Union[int, str]]]


@dataclass
class IndividualSprintFormat(CompetitionFormat, DataClassJsonMixin):
    """Data class with details about a individual sprint format."""

    time_between_groups: time
    time_between_rounds: time
    time_between_heats: time
    rounds_ranked_classes: List[str]
    rounds_non_ranked_classes: List[str]
    race_config: Dict[str, RaceSetting]
    datatype: str = field(
        metadata=dict(marshmallow_field=Constant("individual_sprint")),
        default="individual_sprint",
    )
    id: Optional[str] = field(default=None)
