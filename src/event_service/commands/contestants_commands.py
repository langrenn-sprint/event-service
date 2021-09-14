"""Module for contestants service."""
from typing import Any

from event_service.services import (
    ContestantsService,
    EventNotFoundException,
    EventsService,
)


class ContestantsCommands:
    """Class representing a commands on contestants."""

    @classmethod
    async def assign_bibs(cls: Any, db: Any, event_id: str) -> None:
        """Aggsign bibs function."""
        # Check if event exists:
        try:
            await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundException as e:
            raise e
        # Get all contestants in event:
        contestants = await ContestantsService.get_all_contestants(db, event_id)
        # For every contestant, assign unique bib and update:
        bib_no = 0
        for _c in contestants:
            bib_no += 1
            _c.bib = bib_no
            assert _c.id is not None
            await ContestantsService.update_contestant(db, event_id, _c.id, _c)
