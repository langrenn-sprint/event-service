"""Event data class module."""

from dataclasses import dataclass, field
from datetime import date, time

from dataclasses_json import DataClassJsonMixin


@dataclass
class Event(DataClassJsonMixin):
    """Data class with details about a event."""

    name: str
    date_of_event: date | None = field(default=None)
    time_of_event: time | None = field(default=None)
    timezone: str | None = field(default="Europe/Oslo")
    competition_format: str | None = field(default=None)
    organiser: str | None = field(default=None)
    webpage: str | None = field(default=None)
    information: str | None = field(default=None)
    id: str | None = field(default=None)
