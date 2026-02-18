"""Contract test cases for results."""

import logging
import os
from collections.abc import AsyncGenerator
from http import HTTPStatus
from typing import Any

import motor.motor_asyncio
import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture

from app.utils import db_utils

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "27017"))
DB_NAME = os.getenv("DB_NAME", "events_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
async def token(http_service: Any) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {"Content-Type": "application/json"}
    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)
        body = response.json()

    if response.status_code != HTTPStatus.OK:
        logger.error(
            f"Got unexpected status {response.status_code} from {http_service}."
        )
    return body["token"]


@pytest.fixture(scope="module", autouse=True)
async def clear_db() -> AsyncGenerator:
    """Delete all events before we start."""
    mongo = motor.motor_asyncio.AsyncIOMotorClient(
        host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASSWORD
    )
    try:
        await db_utils.drop_db_and_recreate_indexes(mongo, DB_NAME)
    except Exception as error:
        logger.exception(f"Failed to drop database {DB_NAME}")
        raise error from error

    yield

    try:
        await db_utils.drop_db(mongo, DB_NAME)
    except Exception as error:
        logger.exception(f"Failed to drop database {DB_NAME}")
        raise error from error


@pytest.fixture(scope="module")
async def event_id(
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
) -> str | None:
    """Create an event object for testing."""
    url = f"{http_service}/events"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = {
        "name": "Oslo Skagen sprint",
        "date_of_event": "2021-08-31",
        "time_of_event": "12:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)
        status = response.status_code

    if status == HTTPStatus.CREATED:
        # return the event_id, which is the last item of the path
        return response.headers["Location"].split("/")[-1]
    logger.error(f"Got unsuccesful status when creating event: {status}.")
    return None


@pytest.fixture(scope="module")
async def new_result(event_id: str) -> dict:
    """Create a result object for testing."""
    return {
        "event_id": event_id,
        "raceclass_name": "G12",
        "timing_point": "Finish",
        "no_of_contestants": 3,
        "ranking_sequence": [
            {"rank": 1, "bib": 19},
            {"rank": 2, "bib": 23},
            {"rank": 3, "bib": 11},
        ],
        "status": 1,
    }


@pytest.mark.contract
async def test_create_result(
    http_service: Any, token: MockFixture, event_id: str, new_result: dict
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/events/{event_id}/results"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = new_result
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)

        assert response.status_code == HTTPStatus.CREATED, response.json()
        assert f"/events/{event_id}/results/" in response.headers["Location"]


@pytest.mark.contract
async def test_get_all_results(http_service: Any, event_id: str) -> None:
    """Should return OK and a list of results as json."""
    url = f"{http_service}/events/{event_id}/results"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        results = response.json()
        assert "application/json" in response.headers["Content-Type"]
        assert type(results) is list
        assert len(results) == 1


@pytest.mark.contract
async def test_get_result_by_raceclass_name(http_service: Any, event_id: str) -> None:
    """Should return OK and result of one raceclass as json."""
    name_parameter = "G12"
    url = f"{http_service}/events/{event_id}/results/{name_parameter}"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        result = response.json()
        assert "application/json" in response.headers["Content-Type"]
        assert type(result) is dict
        assert result["raceclass_name"] == name_parameter


@pytest.mark.contract
async def test_delete_result(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    name_parameter = "G12"
    url = f"{http_service}/events/{event_id}/results/{name_parameter}"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT
