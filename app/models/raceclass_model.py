"""Raceclass Model module."""

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Raceclass(BaseModel):
    """Model with details about an raceclass."""

    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: UUID = Field(default_factory=uuid4)
    name: str
    ageclasses: list[str]
    gender: str
    event_id: UUID
    group: int = 0
    order: int = 0
    ranking: bool = True
    seeding: bool = False
    distance: str | None = Field(default=None)
    no_of_contestants: int | None = 0
