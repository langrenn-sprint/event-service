"""Contestant data class module."""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Contestant(DataClassJsonMixin):
    """Data class with details about a contestant."""

    first_name: str
    last_name: str
    birth_date: date
    gender: str
    ageclass: str
    region: str
    club: str
    event_id: str
    email: str
    team: Optional[str] = field(default=None)
    minidrett_id: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)
    bib: Optional[int] = field(default=None)
    distance: Optional[str] = field(default=None)
