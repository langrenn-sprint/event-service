"""Raceclass data class module."""
from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Raceclass(DataClassJsonMixin):
    """Data class with details about an raceclass."""

    name: str
    ageclass_name: str
    event_id: str
    no_of_contestants: int = 0
    distance: Optional[str] = field(default=None)
    order: Optional[int] = field(default=None)
    id: Optional[str] = field(default=None)
