"""Contract test cases for ping."""
import asyncio
from copy import deepcopy
from json import load
import logging
import os
from typing import Any, AsyncGenerator

from aiohttp import ClientSession, hdrs
import pytest
from pytest_mock import MockFixture

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture(scope="module")
def event_loop(request: Any) -> Any:
    """Redefine the event_loop fixture to have the same scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def clear_db(http_service: Any, token: MockFixture) -> AsyncGenerator:
    """Delete all events before we start."""
    url = f"{http_service}/events"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url) as response:
        events = await response.json()
        for event in events:
            event_id = event["id"]
            async with session.delete(f"{url}/{event_id}", headers=headers) as response:
                pass
    await session.close()
    yield


@pytest.fixture(scope="module")
async def event() -> dict:
    """An event object for testing."""
    return {
        "name": "Oslo Skagen sprint",
        "competition_format": "Interval Start",
        "date_of_event": "2021-08-31",
        "time_of_event": "09:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture(scope="module")
@pytest.mark.asyncio
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


@pytest.fixture(scope="module")
async def competition_format_interval_start() -> dict:
    """An competition_format object for testing."""
    with open("tests/files/competition_format.json", "r") as file:
        competition_format = load(file)
    return competition_format


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_event(
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
    event: dict,
    competition_format_interval_start: dict,
) -> None:
    """Should return Created, location header and no body."""
    async with ClientSession() as session:
        headers = {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        # We have to create a competition_format:
        url = f"{http_service}/competition-formats"
        request_body = competition_format_interval_start
        async with session.post(url, headers=headers, json=request_body) as response:
            status = response.status
            assert status == 201

        url = f"{http_service}/events"
        request_body = event

        async with session.post(url, headers=headers, json=request_body) as response:
            status = response.status

        assert status == 201
        assert "/events/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_events(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of events as json."""
    url = f"{http_service}/events"

    session = ClientSession()
    async with session.get(url) as response:
        events = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(events) is list
    assert len(events) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_event_by_id(
    http_service: Any, token: MockFixture, event: dict
) -> None:
    """Should return OK and an event as json."""
    url = f"{http_service}/events"

    async with ClientSession() as session:
        async with session.get(url) as response:
            events = await response.json()
        id = events[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url) as response:
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(event) is dict
    assert body["id"] == id
    assert body["name"] == event["name"]
    assert body["competition_format"] == event["competition_format"]
    assert body["date_of_event"] == event["date_of_event"]
    assert body["time_of_event"] == event["time_of_event"]
    assert body["organiser"] == event["organiser"]
    assert body["webpage"] == event["webpage"]
    assert body["information"] == event["information"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_event(http_service: Any, token: MockFixture, event: dict) -> None:
    """Should return No Content."""
    url = f"{http_service}/events"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            events = await response.json()
        id = events[0]["id"]
        url = f"{url}/{id}"

        request_body = deepcopy(event)
        new_name = "Oslo Skagen sprint updated"
        request_body["id"] = id
        request_body["name"] = new_name

        async with session.put(url, headers=headers, json=request_body) as response:
            assert response.status == 204

        async with session.get(url) as response:
            assert response.status == 200
            updated_event = await response.json()
            assert updated_event["name"] == new_name
            assert updated_event["competition_format"] == event["competition_format"]
            assert updated_event["date_of_event"] == event["date_of_event"]
            assert updated_event["time_of_event"] == event["time_of_event"]
            assert updated_event["organiser"] == event["organiser"]
            assert updated_event["webpage"] == event["webpage"]
            assert updated_event["information"] == event["information"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_event(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/events"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            events = await response.json()
        id = events[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204

        async with session.get(url) as response:
            assert response.status == 404
