"""Contestant data class module."""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from dataclasses_json import config, DataClassJsonMixin
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
    team: Optional[str] = field(default=None)
    minidrett_id: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)
    bib: Optional[int] = field(default=None)
    distance: Optional[str] = field(default=None)
    seeding_points: Optional[int] = field(default=None)
