"""Raceclass Model module."""

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Result(BaseModel):
    """Model with details about final result for a (sprint) raceclass."""

    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    raceclass_name: str
    timing_point: str
    no_of_contestants: int
    ranking_sequence: list[dict]  # list of references to bib
    status: int  # int with reference to RaceResultStatus
