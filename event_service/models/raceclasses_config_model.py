"""Raceclass data class module."""

from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin


@dataclass
class RaceclassesConfig(DataClassJsonMixin):
    """Data class with details about a raceclass configuration."""

    naming_rules: dict
    gender_order: list[str] = field(default_factory=list)
    ageclass_order: list[str] = field(default_factory=list)
    grouping_feature: str = "same_age"
    unranked_ageclasses: list[str] = field(default_factory=list)
