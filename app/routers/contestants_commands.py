"""Resource module for events resources."""

import logging
import os
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.authorization import Role, RoleChecker
from app.commands import (
    ContestantsCommands,
    NoRaceclassInEventError,
    NoValueForGroupInRaceclassError,
    NoValueForOrderInRaceclassError,
)
from app.services import (
    EventNotFoundError,
    IllegalValueError,
)

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["contestants"])


@router.post(
    "/events/{event_id}/contestants/assign-bibs",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def assign_bibs(
    event_id: UUID,
    start_bib: Annotated[
        int | None,
        Query(
            alias="start-bib",
            description="The starting bib number for assignment. If not provided, bibs will be assigned starting from 1.",
        ),
    ] = None,
) -> Response:
    """Assigne bibs to contestants."""
    # Execute command:

    try:
        await ContestantsCommands.assign_bibs(event_id, start_bib or None)
    except (EventNotFoundError, NoRaceclassInEventError) as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except (
        NoValueForGroupInRaceclassError,
        NoValueForOrderInRaceclassError,
        IllegalValueError,
    ) as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e

    headers = {"Location": f"{BASE_URL}/events/{event_id}/contestants"}
    return Response(status_code=HTTPStatus.CREATED, headers=headers)
