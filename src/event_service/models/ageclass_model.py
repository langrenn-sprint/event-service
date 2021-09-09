"""Ageclass data class module."""
from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Ageclass(DataClassJsonMixin):
    """Data class with details about an ageclass."""

    name: str
    order: int
    raceclass: str
    event_id: str
    distance: str
    id: Optional[str] = field(default=None)
