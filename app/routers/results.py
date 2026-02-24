"""Resource module for raceclass results resources."""

import logging
import os
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.adapters import ResultsAdapter
from app.authorization import Role, RoleChecker
from app.models import Result
from app.services import EventNotFoundError, ResultNotFoundError, ResultsService

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["results"])


@router.get("/events/{event_id}/results")
async def get_all_results(event_id: UUID) -> list[Result]:
    """Get route function."""
    logger.debug(f"Got get request for event results {event_id}")

    return await ResultsAdapter.get_all_results(event_id)


@router.post(
    "/events/{event_id}/results",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def create_race_result(event_id: UUID, result: Result) -> Response:
    """Create race result function."""
    logger.debug(f"Got create request for result {result}.")

    try:
        result_id = await ResultsService.create_result(event_id, result)
    except EventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    if result_id:
        logger.debug(f"inserted document with result_id {result_id}")
        headers = {"Location": f"{BASE_URL}/events/{event_id}/results/{result_id}"}

        return Response(status_code=HTTPStatus.CREATED, headers=headers)
    raise HTTPException(status_code=HTTPStatus.BAD_REQUEST) from None


@router.get("/events/{event_id}/results/{raceclass_name}")
async def get_result_by_raceclass_name(event_id: UUID, raceclass_name: str) -> Result:
    """Get result by raceclass name function."""
    logger.debug(f"Got get request for event/raceclass {event_id}/{raceclass_name}")

    result = await ResultsAdapter.get_result_by_raceclass_name(event_id, raceclass_name)
    if result:
        return result
    raise HTTPException(status_code=HTTPStatus.NOT_FOUND) from None


@router.delete(
    "/events/{event_id}/results/{raceclass_name}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def delete(event_id: UUID, raceclass_name: str) -> Response:
    """Delete route function."""
    logger.debug(f"Got delete request for result {raceclass_name}")

    try:
        await ResultsService.delete_result(event_id, raceclass_name)
    except ResultNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=204)
