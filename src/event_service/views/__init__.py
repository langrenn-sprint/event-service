"""Package for all views."""
from .ageclasses import AgeclassesView, AgeclassView
from .contestants import ContestantsView, ContestantView
from .contestants_commands import ContestantsAssignBibsView
from .events import EventsView, EventView
from .events_commands import EventGenerateAgeclassesView
from .liveness import Ping, Ready
