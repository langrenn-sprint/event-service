"""Contract test cases for competition-formats."""
from copy import deepcopy
import logging
import os
from typing import Any, AsyncGenerator

from aiohttp import ClientSession, hdrs
import pytest
from pytest_mock import MockFixture

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture
@pytest.mark.asyncio
async def clear_db(http_service: Any, token: MockFixture) -> AsyncGenerator:
    """Delete all Competition_formats before we start."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        competition_formats = await response.json()
        for competition_format in competition_formats:
            competition_format_id = competition_format["id"]
            async with session.delete(
                f"{url}/{competition_format_id}", headers=headers
            ) as response:
                pass
    await session.close()
    yield


@pytest.fixture
async def competition_format() -> dict:
    """An competition_format object for testing."""
    return {
        "name": "Interval start",
        "starting_order": "Draw",
        "start_procedure": "Interval start",
        "intervals": "00:00:30",
    }


@pytest.fixture
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


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_competition_format(
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
    competition_format: dict,
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/competition-formats"
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
    assert "/competition-formats/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_competition_formats(
    http_service: Any, token: MockFixture
) -> None:
    """Should return OK and a list of competition_formats as json."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        competition_formats = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(competition_formats) is list
    assert len(competition_formats) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_competition_format_by_id(
    http_service: Any, token: MockFixture, competition_format: dict
) -> None:
    """Should return OK and an competition_format as json."""
    url = f"{http_service}/competition-formats"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            competition_formats = await response.json()
        id = competition_formats[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url, headers=headers) as response:
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(competition_format) is dict
    assert body["id"] == id
    assert body["name"] == competition_format["name"]
    assert body["starting_order"] == competition_format["starting_order"]
    assert body["start_procedure"] == competition_format["start_procedure"]
    assert body["intervals"] == competition_format["intervals"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_competition_format_by_name(
    http_service: Any, token: MockFixture, competition_format: dict
) -> None:
    """Should return OK and an competition_format as json."""
    url = f"{http_service}/competition-formats"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            competition_formats = await response.json()
        name = competition_formats[0]["name"]
        url = f"{url}?name={name}"
        async with session.get(url, headers=headers) as response:
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(body) is list
    assert body[0]["id"]
    assert body[0]["name"] == competition_format["name"]
    assert body[0]["starting_order"] == competition_format["starting_order"]
    assert body[0]["start_procedure"] == competition_format["start_procedure"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_competition_format(
    http_service: Any, token: MockFixture, competition_format: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            competition_formats = await response.json()
        id = competition_formats[0]["id"]
        url = f"{url}/{id}"

        request_body = deepcopy(competition_format)
        new_name = "Interval start updated"
        request_body["id"] = id
        request_body["name"] = new_name

        async with session.put(url, headers=headers, json=request_body) as response:
            assert response.status == 204

        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            updated_competition_format = await response.json()
            assert updated_competition_format["name"] == new_name


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_competition_format(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            competition_formats = await response.json()
        id = competition_formats[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204

        async with session.get(url, headers=headers) as response:
            assert response.status == 404
