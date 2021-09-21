"""Competition format data class module."""
from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class CompetitionFormat(DataClassJsonMixin):
    """Data class with details about a competition format."""

    name: str
    starting_order: str
    start_procedure: str
    id: Optional[str] = field(default=None)
