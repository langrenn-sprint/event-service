"""Raceclass data class module."""

import asyncio
from dataclasses import dataclass, field

import nest_asyncio
from dataclasses_json import DataClassJsonMixin

from event_service.adapters import ContestantsAdapter

nest_asyncio.apply()  # Patch the current event loop


@dataclass
class Raceclass(DataClassJsonMixin):
    """Data class with details about an raceclass."""

    name: str
    ageclasses: list[str]
    gender: str
    event_id: str
    group: int = 0
    order: int = 0
    ranking: bool = True
    seeding: bool = False
    distance: str | None = field(default=None)
    id: str | None = field(default=None)
    no_of_contestants: int = field(init=False)  # Not in constructor

    def __post_init__(self) -> None:
        """Number of contestants in raceclass.

        This number is calculated based on number of contestants
        in each of the ageclasses of the raceclass

        """
        _no_of_contestants = 0
        # Get all contestants in race:
        contestants = asyncio.run(ContestantsAdapter.get_all_contestants(self.event_id))

        # Count all contestants where ageclass is in ageclasses:
        for contestant in contestants:
            if contestant["ageclass"] in self.ageclasses:
                _no_of_contestants += 1
        self.no_of_contestants = _no_of_contestants


@dataclass
class RaceclassResult(DataClassJsonMixin):
    """Data class with details about final result for a (sprint) raceclass."""

    event_id: str
    raceclass: str
    timing_point: str
    no_of_contestants: int
    ranking_sequence: list[dict]  # list of references to bib
    status: int  # int with reference to RaceResultStatus
    id: str | None = field(default=None)
