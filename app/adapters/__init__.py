"""Package for all adapters."""

from .competition_formats_adapter import (
    CompetitionFormatsAdapter,
    CompetitionFormatsAdapterError,
)
from .contestants_adapter import ContestantsAdapter
from .events_adapter import EventsAdapter
from .liveness_adapter import LivenessAdapter
from .raceclasses_adapter import RaceclassesAdapter
from .raceclasses_config_adapter import RaceclassesConfigAdapter
from .results_adapter import ResultsAdapter

__all__ = [
    "CompetitionFormatsAdapter",
    "CompetitionFormatsAdapterError",
    "ContestantsAdapter",
    "EventFormatAdapter",
    "EventsAdapter",
    "LivenessAdapter",
    "RaceclassesAdapter",
    "RaceclassesConfigAdapter",
    "ResultsAdapter",
]
