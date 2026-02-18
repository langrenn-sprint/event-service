"""Resource module for events resources."""

import logging
import os
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.adapters import ContestantsAdapter
from app.models import Contestant

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["contestants"])


class ContestantSearchQuery(BaseModel):
    """Model for the query to search for contestants."""

    name: str


@router.post("/events/{event_id}/contestants/search")
async def search_for_contestant(
    event_id: UUID, query: ContestantSearchQuery
) -> list[Contestant]:
    """Search for contestant by first name or last name."""
    name = query.name.strip()
    return await ContestantsAdapter.search_contestants_in_event_by_name(event_id, name)
