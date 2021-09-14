"""Package for all services."""
from .ageclasses_service import (
    AgeclassCreateException,
    AgeclassesService,
    AgeclassNotFoundException,
    AgeclassNotUniqueNameException,
    AgeclassUpdateException,
)
from .contestants_service import ContestantNotFoundException, ContestantsService
from .events_service import EventNotFoundException, EventsService
from .exceptions import IllegalValueException
