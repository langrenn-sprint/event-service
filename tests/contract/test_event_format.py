"""Contract test cases for event specific format."""
import asyncio
from copy import deepcopy
import logging
import os
from typing import Any, Optional

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
async def event_id(http_service: Any, token: MockFixture) -> Optional[str]:
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
    else:
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
        "datatype": "interval_start",
    }


@pytest.mark.contract
@pytest.mark.asyncio
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
@pytest.mark.asyncio
async def test_get_event_specific_format(
    http_service: Any, token: MockFixture, event_id: str, competition_format: dict
) -> None:
    """Should return OK and a event specific format as json."""
    url = f"{http_service}/events/{event_id}/format"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        body = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(body) is dict
    assert body["name"] == competition_format["name"]


@pytest.mark.contract
@pytest.mark.asyncio
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
@pytest.mark.asyncio
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
