"""Raceclass Model module."""

from pydantic import BaseModel, Field


class RaceclassesConfig(BaseModel):
    """Model with details about a raceclass configuration."""

    naming_rules: dict
    gender_order: list[str] = Field(default_factory=list)
    ageclass_order: list[str] = Field(default_factory=list)
    grouping_feature: str = "same_age"
    unranked_ageclasses: list[str] = Field(default_factory=list)
