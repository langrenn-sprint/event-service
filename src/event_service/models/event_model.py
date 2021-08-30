"""Event data class module."""
from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Event(DataClassJsonMixin):
    """Data class with details about a event."""

    name: str
    id: Optional[str] = field(default=None)
