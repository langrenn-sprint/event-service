"""Event data class module."""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Event(DataClassJsonMixin):
    """Data class with details about a event."""

    name: str
    date_of_event: Optional[date] = field(default=None)
    competition_format: Optional[str] = field(default=None)
    organiser: Optional[str] = field(default=None)
    webpage: Optional[str] = field(default=None)
    information: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)
