"""Event Model module."""

from datetime import date, time
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer


class Event(BaseModel):
    """Model with details about a event."""

    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: UUID = Field(default_factory=uuid4)
    name: str
    date_of_event: date

    @field_serializer("date_of_event")
    def serialize_event_date(self, dt: date) -> str:
        """Serialize date of event to ISO format."""
        return dt.isoformat()

    time_of_event: time | None = Field(default=None)

    @field_serializer("time_of_event")
    def serialize_event_time(self, dt: time | None) -> str | None:
        """Serialize time of event to ISO format."""
        return dt.isoformat() if dt else None

    timezone: str | None = Field(default="Europe/Oslo")
    competition_format: str | None = Field(default=None)
    organiser: str | None = Field(default=None)
    webpage: HttpUrl | None = Field(default=None)

    @field_serializer("webpage")
    def serialize_webpage(self, webpage: HttpUrl | None) -> str | None:
        """Serialize webpage url to string."""
        return str(webpage) if webpage else None

    information: str | None = Field(default=None)
