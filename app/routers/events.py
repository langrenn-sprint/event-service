"""Resource module for events resources."""

import logging
import os
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.adapters import EventsAdapter
from app.authorization import Role, RoleChecker
from app.models import Event
from app.services import (
    CompetitionFormatNotFoundError,
    EventNotFoundError,
    EventsService,
    IllegalValueError,
    InvalidTimezoneError,
)

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


router = APIRouter(tags=["events"])

logger = logging.getLogger("uvicorn.error")


@router.get("/events")
async def get_all_events() -> list[Event]:
    """Get all events."""
    events = await EventsAdapter.get_all_events()
    return sorted(
        events,
        key=lambda k: (
            k.date_of_event is not None,
            k.date_of_event,
            k.time_of_event is not None,
            k.time_of_event,
        ),
        reverse=True,
    )


@router.post(
    "/events",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def create_event(event: Event) -> Response:
    """Create an event."""
    try:
        event_id = await EventsService.create_event(event)
    except (IllegalValueError, InvalidTimezoneError) as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except CompetitionFormatNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e
    if event_id:
        logger.debug(f"inserted document with event_id {event_id}")
        headers = {"Location": f"{BASE_URL}/events/{event_id}"}

        return Response(status_code=HTTPStatus.CREATED, headers=headers)
    raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from None


@router.get("/events/{event_id}")
async def get_event_by_id(event_id: UUID) -> Event:
    """Get an event by id."""
    event = await EventsAdapter.get_event_by_id(event_id)
    if event:
        return event
    msg = f"Event with id {event_id} not found"
    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=msg) from None


@router.put(
    "/events/{event_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def update_event(event_id: UUID, event: Event) -> Response:
    """Update an event by id."""
    try:
        await EventsService.update_event(event_id, event)
    except IllegalValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except EventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except CompetitionFormatNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/events/{event_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def delete_event(event_id: UUID) -> Response:
    """Delete an event."""
    try:
        await EventsService.delete_event(event_id)
    except EventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)
