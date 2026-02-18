"""Resource module for events resources."""

import logging
import os
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.authorization import Role, RoleChecker
from app.commands import EventsCommands
from app.services import (
    EventNotFoundError,
    RaceclassCreateError,
    RaceclassNotUniqueNameError,
    RaceclassUpdateError,
)

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["events"])


@router.post(
    "/events/{event_id}/generate-raceclasses",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def generate_raceclasses_on_event(event_id: UUID) -> Response:
    """Generate raceclasses on a given event."""
    # Execute command:
    try:
        await EventsCommands.generate_raceclasses(event_id)
    except EventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except (
        RaceclassCreateError,
        RaceclassNotUniqueNameError,
        RaceclassUpdateError,
    ) as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e
    headers = {"Location": f"{BASE_URL}/events/{event_id}/raceclasses"}
    return Response(status_code=HTTPStatus.CREATED, headers=headers)
