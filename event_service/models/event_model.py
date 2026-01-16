"""Event data class module."""

from dataclasses import dataclass, field
from datetime import date, time

from dataclasses_json import DataClassJsonMixin, config
from marshmallow.fields import Date, Time


@dataclass
class Event(DataClassJsonMixin):
    """Data class with details about a event."""

    name: str
    date_of_event: date | None = field(
        default=None,
        metadata=config(
            exclude=lambda f: f is None,
            encoder=date.isoformat,
            decoder=date.fromisoformat,
            mm_field=Date(format="iso"),
        ),
    )
    time_of_event: time | None = field(
        default=None,
        metadata=config(
            exclude=lambda f: f is None,
            encoder=time.isoformat,
            decoder=time.fromisoformat,
            mm_field=Time(format="iso"),
        ),
    )
    timezone: str | None = field(default="Europe/Oslo")
    competition_format: str | None = field(default=None)
    organiser: str | None = field(default=None)
    webpage: str | None = field(default=None)
    information: str | None = field(default=None)
    id: str | None = field(default=None)
