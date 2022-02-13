"""Raceclass data class module."""
from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Raceclass(DataClassJsonMixin):
    """Data class with details about an raceclass."""

    name: str
    ageclasses: List[str]
    event_id: str
    group: int = 0
    order: int = 0
    no_of_contestants: int = 0
    ranking: bool = True
    distance: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)
