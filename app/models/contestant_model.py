"""Contestant model module."""

from datetime import date, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer


class Contestant(BaseModel):
    """Model with details about a contestant."""

    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    birth_date: date

    @field_serializer("birth_date")
    def serialize_birth_date(self, dt: date) -> str:
        """Serialize birth date to ISO format."""
        return dt.isoformat()

    gender: str
    ageclass: str
    region: str
    club: str
    event_id: UUID
    email: EmailStr | None = Field(default=None)

    @field_serializer("email")
    def serialize_email(self, email: EmailStr | None) -> str | None:
        """Serialize email to string."""
        return str(email) if email else None

    registration_date_time: datetime

    @field_serializer("registration_date_time")
    def serialize_registration_date_time(self, dt: datetime) -> str:
        """Serialize registration date and time to ISO format."""
        return dt.isoformat()

    team: str | None = Field(default=None)
    minidrett_id: str | None = Field(default=None)
    bib: int | None = Field(default=None)
    distance: str | None = Field(default=None)
    seeding_points: int | None = Field(default=None)
