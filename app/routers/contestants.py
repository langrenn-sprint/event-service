"""Resource module for contestants resources."""

import json
import logging
import os
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app.adapters import ContestantsAdapter
from app.authorization import Role, RoleChecker
from app.models import Contestant
from app.services import (
    BibAlreadyInUseError,
    ContestantAllreadyExistError,
    ContestantNotFoundError,
    ContestantsService,
    EventNotFoundError,
    IllegalValueError,
    RaceclassNotFoundError,
)

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"

router = APIRouter(tags=["contestants"])


logger = logging.getLogger("event_service.views.contestants")


@router.get("/events/{event_id}/contestants")
async def get_all_contestants(
    event_id: UUID,
    raceclass_name: Annotated[
        str | None,
        Query(
            alias="raceclass-name",
            description="The raceclass to filter contestants by.",
        ),
    ] = None,
    ageclass_name: Annotated[
        str | None,
        Query(
            alias="ageclass-name", description="The ageclass to filter contestants by."
        ),
    ] = None,
    bib: Annotated[
        int | None,
        Query(description="The bib to filter contestants by."),
    ] = None,
) -> list[Contestant]:
    """Get all contestants in event."""
    if raceclass_name:
        try:
            contestants = await ContestantsService.get_contestants_by_raceclass(
                event_id, raceclass_name
            )
        except RaceclassNotFoundError as e:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail=str(e)
            ) from e
    elif ageclass_name:
        contestants = await ContestantsService.get_contestants_by_ageclass(
            event_id, ageclass_name
        )
    elif bib:
        contestant = await ContestantsAdapter.get_contestant_by_bib(event_id, bib)
        contestants = [contestant] if contestant else []
    else:
        contestants = await ContestantsAdapter.get_all_contestants(event_id)

    return sorted(
        contestants,
        key=lambda k: (
            k.bib is not None,
            k.bib != "",
            k.bib,
            k.ageclass,
            k.last_name,
            k.first_name,
        ),
        reverse=False,
    )


@router.post(
    "/events/{event_id}/contestants",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def create_contestant(event_id: UUID, contestant: Contestant) -> Response:
    """Create contestant."""
    try:
        contestant_id = await ContestantsService.create_contestant(event_id, contestant)
    except EventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except (BibAlreadyInUseError, ContestantAllreadyExistError) as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e

    if contestant_id:
        logger.debug(f"inserted document with contestant_id {contestant_id}")
        headers = {
            "Location": f"{BASE_URL}/events/{event_id}/contestants/{contestant_id}"
        }
        return Response(status_code=HTTPStatus.CREATED, headers=headers)
    raise HTTPException(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        detail="Failed to create contestant.",
    ) from None


@router.post(
    "/events/{event_id}/contestants/file",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def create_many_contestants(
    event_id: UUID,
    file: UploadFile,
) -> Response:
    """Create contestants by uploading a file."""
    logger.debug(f"part.name {file.filename}.")
    if file.content_type == "text/csv":
        # process csv:
        contestants = (await file.read()).decode()
    else:
        raise HTTPException(
            status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            detail=f"File's content-type {file.content_type} not supported.",
        ) from None
    try:
        result = await ContestantsService.create_contestants(event_id, contestants)
    except EventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except IllegalValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e

    logger.debug(f"result:\n {result}")
    body = json.dumps(result)

    return Response(status_code=200, content=body, media_type="application/json")


@router.get("/events/{event_id}/contestants/{contestant_id}")
async def get_contestant_by_id(event_id: UUID, contestant_id: UUID) -> Contestant:
    """Get a contestant by id."""
    logger.debug(f"Got get request for contestant {contestant_id}")

    contestant = await ContestantsAdapter.get_contestant_by_id(event_id, contestant_id)
    if not contestant:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Contestant with id {contestant_id} not found.",
        )
    return contestant


@router.put(
    "/events/{event_id}/contestants/{contestant_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def update_contestant(
    event_id: UUID, contestant_id: UUID, contestant: Contestant
) -> Response:
    """Update contestant by id."""
    logger.debug(
        f"Got request-body {contestant} for {contestant_id} of type {type(contestant)}."
    )

    try:
        await ContestantsService.update_contestant(event_id, contestant_id, contestant)
    except IllegalValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except ContestantNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except BibAlreadyInUseError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/events/{event_id}/contestants/{contestant_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def delete_contestant(event_id: UUID, contestant_id: UUID) -> Response:
    """Delete a contestant."""
    logger.debug(
        f"Got delete request for contestant {contestant_id} in event {event_id}"
    )

    try:
        await ContestantsService.delete_contestant(event_id, contestant_id)
    except ContestantNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/events/{event_id}/contestants",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def delete_all_contestants(event_id: UUID) -> Response:
    """Delete all contestants."""
    await ContestantsAdapter.delete_all_contestants(event_id)

    return Response(status_code=HTTPStatus.NO_CONTENT)
