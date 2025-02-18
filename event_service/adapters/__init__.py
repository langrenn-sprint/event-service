"""Package for all adapters."""

from .competition_formats_adapter import (
    CompetitionFormatsAdapter,
    CompetitionFormatsAdapterError,
)
from .contestants_adapter import ContestantsAdapter
from .event_format_adapter import EventFormatAdapter
from .events_adapter import EventsAdapter
from .raceclasses_adapter import RaceclassesAdapter
from .results_adapter import ResultsAdapter
from .users_adapter import UsersAdapter

__all__ = [
    "CompetitionFormatsAdapter",
    "CompetitionFormatsAdapterError",
    "ContestantsAdapter",
    "EventFormatAdapter",
    "EventsAdapter",
    "RaceclassesAdapter",
    "ResultsAdapter",
    "UsersAdapter",
]
