"""Contestant data class module."""
from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Contestant(DataClassJsonMixin):
    """Data class with details about a contestant."""

    first_name: str
    last_name: str
    birth_date: str
    club: str
    event_id: str
    minidrett_id: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)
