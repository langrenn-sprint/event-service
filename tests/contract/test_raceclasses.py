"""Contract test cases for ping."""

import logging
import os
from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import quote

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
async def raceclass(event_id: str) -> dict:
    """Create a raceclass object for testing."""
    return {
        "name": "G16",
        "ageclasses": ["G 16 år"],
        "event_id": event_id,
        "group": 1,
        "order": 1,
        "no_of_contestants": 0,
        "ranking": True,
        "seeding": False,
        "distance": "5km",
    }


@pytest.mark.contract
async def test_create_raceclass(
    http_service: Any, token: MockFixture, event_id: str, raceclass: dict
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = raceclass
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert f"/events/{event_id}/raceclasses/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
async def test_get_all_raceclasses(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of raceclasses as json."""
    url = f"{http_service}/events/{event_id}/raceclasses"

    session = ClientSession()
    async with session.get(url) as response:
        raceclasses = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceclasses) is list
    assert len(raceclasses) == 1


@pytest.mark.contract
async def test_get_all_raceclasses_by_name(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of raceclasses as json."""
    name_parameter = "G16"
    url = f"{http_service}/events/{event_id}/raceclasses?name={name_parameter}"

    session = ClientSession()
    async with session.get(url) as response:
        raceclasses = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceclasses) is list
    assert len(raceclasses) == 1
    assert raceclasses[0]["name"] == name_parameter


@pytest.mark.contract
async def test_get_all_raceclasses_by_ageclass_name(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of raceclasses as json."""
    ageclass_name = "G 16 år"
    ageclass_name_parameter = quote(ageclass_name)
    url = (
        f"{http_service}/events/{event_id}/raceclasses?ageclass-name"
        f"={ageclass_name_parameter}"
    )

    session = ClientSession()
    async with session.get(url) as response:
        raceclasses = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceclasses) is list
    assert len(raceclasses) == 1
    assert raceclasses[0]["ageclasses"] == [ageclass_name]


@pytest.mark.contract
async def test_get_raceclass_by_id(
    http_service: Any, token: MockFixture, event_id: str, raceclass: dict
) -> None:
    """Should return OK and an raceclass as json."""
    url = f"{http_service}/events/{event_id}/raceclasses"

    async with ClientSession() as session:
        async with session.get(url) as response:
            raceclasses = await response.json()
        id = raceclasses[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url) as response:
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(body) is dict
    assert body["id"]
    assert body["name"] == raceclass["name"]
    assert body["order"] == raceclass["order"]
    assert body["ageclasses"] == raceclass["ageclasses"]
    assert body["distance"] == raceclass["distance"]
    assert body["event_id"] == raceclass["event_id"]


@pytest.mark.contract
async def test_update_raceclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return No Content."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            raceclasses = await response.json()
        assert response.status == 200

        _raceclass = raceclasses[0]
        id = _raceclass["id"]
        _raceclass["name"] = _raceclass["name"] + "/G15"
        _raceclass["ageclasses"].append("G 15 år")

        url = f"{url}/{id}"
        async with session.put(url, headers=headers, json=_raceclass) as response:
            pass
        assert response.status == 204

        async with session.get(url) as response:
            raceclass = await response.json()
        assert response.status == 200
        assert raceclass["name"] == _raceclass["name"]
        assert raceclass["ageclasses"] == _raceclass["ageclasses"]


@pytest.mark.contract
async def test_delete_raceclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return No Content."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            raceclasses = await response.json()
        id = raceclasses[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
async def test_delete_all_raceclasses(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204

        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()
            assert len(raceclasses) == 0
