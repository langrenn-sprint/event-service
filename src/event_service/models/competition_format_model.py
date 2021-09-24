"""Competition format data class module."""
from dataclasses import dataclass, field
from datetime import time
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class CompetitionFormat(DataClassJsonMixin):
    """Data class with details about a competition format."""

    name: str
    start_procedure: str
    starting_order: Optional[str] = field(default=None)
    intervals: Optional[time] = field(default=None)
    id: Optional[str] = field(default=None)
