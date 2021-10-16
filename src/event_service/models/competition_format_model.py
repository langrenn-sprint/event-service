"""Competition format data class module."""
from abc import ABC
from dataclasses import dataclass, field
from datetime import time
from typing import Optional

from dataclasses_json import DataClassJsonMixin
from marshmallow.fields import Constant


@dataclass
class CompetitionFormat(DataClassJsonMixin, ABC):
    """Abstract data class with details about a competition format."""

    def __post_init__(self) -> None:  # pragma: no cover
        """Prevent instantiate abstract class."""
        if self.__class__ == CompetitionFormat:
            raise TypeError("Cannot instantiate abstract class.")

    name: str
    start_procedure: str
    starting_order: str


@dataclass
class IntervalStartFormat(CompetitionFormat, DataClassJsonMixin):
    """Data class with details about a interval start format."""

    intervals: time
    datatype: str = field(
        metadata=dict(marshmallow_field=Constant("interval_start")),
        default="interval_start",
    )
    id: Optional[str] = field(default=None)


@dataclass
class IndividualSprintFormat(CompetitionFormat, DataClassJsonMixin):
    """Data class with details about a individual sprint format."""

    max_no_of_contestants: int
    time_between_groups: time
    time_between_rounds: time
    time_between_heats: time
    datatype: str = field(
        metadata=dict(marshmallow_field=Constant("individual_sprint")),
        default="individual_sprint",
    )
    id: Optional[str] = field(default=None)
