"""Contestant data class module."""

from dataclasses import dataclass, field
from datetime import date, datetime

from dataclasses_json import DataClassJsonMixin, config
from marshmallow.fields import DateTime


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
    registration_date_time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=DateTime(format="iso"),
        )
    )
    team: str | None = field(default=None)
    minidrett_id: str | None = field(default=None)
    id: str | None = field(default=None)
    bib: int | None = field(default=None)
    distance: str | None = field(default=None)
    seeding_points: int | None = field(default=None)
