"""Contract test cases for ping."""

import json
import logging
import os
from collections.abc import AsyncGenerator
from copy import deepcopy
from http import HTTPStatus
from typing import Any

import aiofiles
import motor.motor_asyncio
import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture

from app.utils import db_utils

COMPETITION_FORMAT_HOST_SERVER = os.getenv("COMPETITION_FORMAT_HOST_SERVER")
COMPETITION_FORMAT_HOST_PORT = os.getenv("COMPETITION_FORMAT_HOST_PORT")
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
async def event() -> dict:
    """An event object for testing."""
    return {
        "name": "Oslo Skagen sprint",
        "competition_format": "Interval Start",
        "date_of_event": "2021-08-31",
        "time_of_event": "09:00:00",
        "timezone": "Europe/Oslo",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com/",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture(scope="module")
async def competition_format_interval_start() -> dict:
    """An competition_format object for testing."""
    async with aiofiles.open(
        "tests/files/competition_format_interval_start.json"
    ) as file:
        content = await file.read()
    return json.loads(content)


@pytest.mark.contract
async def test_create_event(
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
    event: dict,
    competition_format_interval_start: dict,
) -> None:
    """Should return Created, location header and no body."""
    async with AsyncClient() as client:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        # We have to create a competition_format:
        url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"
        request_body = competition_format_interval_start
        response = await client.post(url, headers=headers, json=request_body)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
        assert response.status_code == HTTPStatus.CREATED, f"{body}"

        # Now we can create an event:
        url = f"{http_service}/events"
        request_body = event

        response = await client.post(url, headers=headers, json=request_body)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
        assert response.status_code == HTTPStatus.CREATED, f"{body}" if body else ""
        assert "/events/" in response.headers["Location"]


@pytest.mark.contract
async def test_get_all_events(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of events as json."""
    url = f"{http_service}/events"

    async with AsyncClient() as client:
        response = await client.get(url)
        events = response.json()

    assert response.status_code == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
    assert type(events) is list
    assert len(events) > 0


@pytest.mark.contract
async def test_get_event_by_id(
    http_service: Any, token: MockFixture, event: dict
) -> None:
    """Should return OK and an event as json."""
    url = f"{http_service}/events"

    async with AsyncClient() as client:
        response = await client.get(url)
        events = response.json()
        event_id = events[0]["id"]
        url = f"{url}/{event_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        body = response.json()
        assert type(event) is dict
        assert body["id"] == event_id
        assert body["name"] == event["name"]
        assert body["competition_format"] == event["competition_format"]
        assert body["date_of_event"] == event["date_of_event"]
        assert body["time_of_event"] == event["time_of_event"]
        assert body["timezone"] == event["timezone"]
        assert body["organiser"] == event["organiser"]
        assert body["webpage"] == event["webpage"]
        assert body["information"] == event["information"]


@pytest.mark.contract
async def test_update_event(http_service: Any, token: MockFixture, event: dict) -> None:
    """Should return No Content."""
    url = f"{http_service}/events"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        events = response.json()
        event_id = events[0]["id"]
        url = f"{url}/{event_id}"

        request_body = deepcopy(event)
        new_name = "Oslo Skagen sprint updated"
        request_body["id"] = event_id
        request_body["name"] = new_name

        response = await client.put(url, headers=headers, json=request_body)
        assert response.status_code == HTTPStatus.NO_CONTENT

        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        updated_event = response.json()
        assert updated_event["name"] == new_name
        assert updated_event["competition_format"] == event["competition_format"]
        assert updated_event["date_of_event"] == event["date_of_event"]
        assert updated_event["time_of_event"] == event["time_of_event"]
        assert updated_event["organiser"] == event["organiser"]
        assert updated_event["webpage"] == event["webpage"]
        assert updated_event["information"] == event["information"]


@pytest.mark.contract
async def test_delete_event(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/events"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        events = response.json()
        event_id = events[0]["id"]
        url = f"{url}/{event_id}"
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT

        response = await client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND
