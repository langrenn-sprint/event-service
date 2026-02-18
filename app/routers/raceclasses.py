"""Resource module for raceclasses resources."""

import logging
import os
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.authorization import Role, RoleChecker
from app.models import Raceclass
from app.services import (
    EventNotFoundError,
    IllegalValueError,
    RaceclassesService,
    RaceclassNotFoundError,
)

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["raceclasses"])


@router.get("/events/{event_id}/raceclasses")
async def get_all_raceclasses(
    event_id: UUID,
    name: Annotated[
        str | None,
        Query(
            description="The name of the raceclass to filter by. If not provided, all raceclasses will be returned.",
        ),
    ] = None,
    ageclass_name: Annotated[
        str | None,
        Query(
            alias="ageclass-name",
            description="The name of the ageclass to filter by. If not provided, all raceclasses will be returned.",
        ),
    ] = None,
) -> list[Raceclass]:
    """Get all raceclasses."""
    if name:
        raceclasses = await RaceclassesService.get_raceclass_by_name(event_id, name)
    elif ageclass_name:
        raceclasses = await RaceclassesService.get_raceclass_by_ageclass_name(
            event_id, ageclass_name
        )
    else:
        raceclasses = await RaceclassesService.get_all_raceclasses(event_id)

    return raceclasses


@router.post(
    "/events/{event_id}/raceclasses",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def create_raceclass(event_id: UUID, raceclass: Raceclass) -> Response:
    """Create raceclass function."""
    logger.debug(f"Got create request for raceclass {raceclass}.")

    try:
        raceclass_id = await RaceclassesService.create_raceclass(event_id, raceclass)
    except EventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    if raceclass_id:
        logger.debug(f"inserted document with id {raceclass_id}")
        headers = {
            "Location": f"{BASE_URL}/events/{event_id}/raceclasses/{raceclass_id}"
        }

        return Response(status_code=HTTPStatus.CREATED, headers=headers)
    raise HTTPException(
        status_code=HTTPStatus.BAD_REQUEST
    ) from None  # pragma: no cover


@router.delete(
    "/events/{event_id}/raceclasses",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def delete_all_raceclasses(event_id: UUID) -> Response:
    """Delete all raceclasses function."""
    await RaceclassesService.delete_all_raceclasses(event_id)

    return Response(status_code=204)


@router.get("/events/{event_id}/raceclasses/{raceclass_id}")
async def get_raceclass_by_id(event_id: UUID, raceclass_id: UUID) -> Raceclass:
    """Get raceclass by id function."""
    logger.debug(f"Got get request for raceclass {raceclass_id}")

    try:
        raceclass = await RaceclassesService.get_raceclass_by_id(event_id, raceclass_id)
    except RaceclassNotFoundError:
        msg = f"Raceclass with id {raceclass_id} not found."
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=msg) from None
    return raceclass


@router.put(
    "/events/{event_id}/raceclasses/{raceclass_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def put(event_id: UUID, raceclass_id: UUID, raceclass: Raceclass) -> Response:
    """Update raceclass function."""
    logger.debug(f"Got request-body {raceclass} for {raceclass_id}.")

    try:
        await RaceclassesService.update_raceclass(event_id, raceclass_id, raceclass)
    except IllegalValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except RaceclassNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/events/{event_id}/raceclasses/{raceclass_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def delete_raceclass_by_id(event_id: UUID, raceclass_id: UUID) -> Response:
    """Delete raceclass by id function."""
    logger.debug(f"Got delete request for raceclass {raceclass_id}")

    try:
        await RaceclassesService.delete_raceclass(event_id, raceclass_id)
    except RaceclassNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)
