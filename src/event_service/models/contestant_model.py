"""Contestant data class module."""
from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Contestant(DataClassJsonMixin):
    """Data class with details about a contestant."""

    first_name: str
    last_name: str
    birth_date: str
    club: str
    minidrett_id: Optional[str] = field(default=None)
    events: Optional[List] = None
    id: Optional[str] = field(default=None)
