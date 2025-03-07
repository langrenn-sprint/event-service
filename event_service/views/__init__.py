"""Package for all views."""

from .contestants import ContestantsView, ContestantView
from .contestants_commands import ContestantsAssignBibsView
from .contestants_search import ContestantsSearchView
from .event_format import EventFormatView
from .events import EventsView, EventView
from .events_commands import EventGenerateRaceclassesView
from .liveness import Ping, Ready
from .raceclasses import RaceclassesView, RaceclassView
from .results import RaceclassResultsView, RaceclassResultView

__all__ = [
    "ContestantView",
    "ContestantsAssignBibsView",
    "ContestantsSearchView",
    "ContestantsView",
    "EventFormatView",
    "EventGenerateRaceclassesView",
    "EventView",
    "EventsView",
    "Ping",
    "RaceclassResultView",
    "RaceclassResultsView",
    "RaceclassView",
    "RaceclassesView",
    "Ready",
]
