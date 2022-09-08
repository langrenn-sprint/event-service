"""Contract test cases for results."""
import asyncio
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
async def new_result(event_id: str) -> dict:
    """Create a result object for testing."""
    return {
        "event_id": event_id,
        "raceclass": "G12",
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
@pytest.mark.asyncio
async def test_create_result(
    http_service: Any, token: MockFixture, event_id: str, new_result: dict
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/events/{event_id}/results"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = new_result
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert f"/events/{event_id}/results/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_results(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of results as json."""
    url = f"{http_service}/events/{event_id}/results"

    session = ClientSession()
    async with session.get(url) as response:
        results = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(results) is list
    assert len(results) == 1


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_result_by_raceclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and result of one raceclass as json."""
    name_parameter = "G12"
    url = f"{http_service}/events/{event_id}/results/{name_parameter}"

    session = ClientSession()
    async with session.get(url) as response:
        result = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(result) is dict
    assert result["raceclass"] == name_parameter


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_result(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    name_parameter = "G12"
    url = f"{http_service}/events/{event_id}/results/{name_parameter}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204
