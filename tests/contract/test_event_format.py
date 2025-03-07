"""Contract test cases for event specific format."""

import logging
import os
from collections.abc import AsyncGenerator
from copy import deepcopy
from typing import Any

import motor.motor_asyncio
import pytest
from aiohttp import ClientSession, hdrs
from pytest_mock import MockFixture

from event_service.utils import db_utils

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 27017))
DB_NAME = os.getenv("DB_NAME", "events_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


@pytest.fixture(scope="module")
async def token(http_service: Any) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {hdrs.CONTENT_TYPE: "application/json"}
    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        body = await response.json()
    await session.close()
    if response.status != 200:
        logging.error(f"Got unexpected status {response.status} from {http_service}.")
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
        logging.exception(f"Failed to drop database {DB_NAME}: {error}")
        raise error

    yield

    try:
        await db_utils.drop_db(mongo, DB_NAME)
    except Exception as error:
        logging.exception(f"Failed to drop database {DB_NAME}: {error}")
        raise error


@pytest.fixture(scope="module")
async def event_id(
    http_service: Any, token: MockFixture, clear_db: AsyncGenerator
) -> str | None:
    """Create an event object for testing."""
    url = f"{http_service}/events"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {
        "name": "Oslo Skagen sprint",
        "date": "2021-08-31",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()
    if status == 201:
        # return the event_id, which is the last item of the path
        return response.headers[hdrs.LOCATION].split("/")[-1]
    logging.error(f"Got unsuccesful status when creating event: {status}.")
    return None


@pytest.fixture(scope="module")
async def competition_format(event_id: str) -> dict:
    """Create a competition format object for testing."""
    return {
        "name": "Interval Start",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
        "max_no_of_contestants_in_raceclass": 9999,
        "max_no_of_contestants_in_race": 9999,
        "datatype": "interval_start",
    }


@pytest.mark.contract
async def test_create_event_specific_format(
    http_service: Any, token: MockFixture, event_id: str, competition_format: dict
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/events/{event_id}/format"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = competition_format
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert f"/events/{event_id}/format" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
async def test_get_event_specific_format(
    http_service: Any, token: MockFixture, event_id: str, competition_format: dict
) -> None:
    """Should return OK and a event specific format as json."""
    url = f"{http_service}/events/{event_id}/format"

    session = ClientSession()
    async with session.get(url) as response:
        body = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(body) is dict
    assert body["name"] == competition_format["name"]
    assert body["starting_order"] == competition_format["starting_order"]
    assert body["start_procedure"] == competition_format["start_procedure"]
    assert body["time_between_groups"] == competition_format["time_between_groups"]
    assert body["intervals"] == competition_format["intervals"]
    assert (
        body["max_no_of_contestants_in_raceclass"]
        == competition_format["max_no_of_contestants_in_raceclass"]
    )
    assert (
        body["max_no_of_contestants_in_race"]
        == competition_format["max_no_of_contestants_in_race"]
    )
    assert body["datatype"] == competition_format["datatype"]


@pytest.mark.contract
async def test_update_competition_format(
    http_service: Any, token: MockFixture, event_id: str, competition_format: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/events/{event_id}/format"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = deepcopy(competition_format)
    request_body["name"] = "format name updated"
    async with ClientSession() as session:
        async with session.put(url, headers=headers, json=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
async def test_delete_competition_format(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return No Content."""
    url = f"{http_service}/events/{event_id}/format"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204
