"""Raceclass data class module."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
    seeding: bool = False
    distance: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)


@dataclass
class RaceclassResult(DataClassJsonMixin):
    """Data class with details about final result for a (sprint) raceclass."""

    event_id: str
    raceclass: str
    timing_point: str
    no_of_contestants: int
    ranking_sequence: List[Dict]  # list of references to bib
    status: int  # int with reference to RaceResultStatus
    id: Optional[str] = field(default=None)
