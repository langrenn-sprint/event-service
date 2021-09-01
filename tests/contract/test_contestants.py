"""Contract test cases for contestants."""
import copy
import logging
import os
from typing import Any

from aiohttp import ClientSession, hdrs
import pytest
from pytest_mock import MockFixture

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


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


@pytest.fixture
async def contestant() -> dict:
    """Create a contestant object for testing."""
    return {
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": "1970-01-01",
        "club": "Lyn Ski",
    }


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_contestant(
    http_service: Any, token: MockFixture, contestant: dict
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/contestants"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = contestant
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert "/contestants/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_contestants(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of contestants as json."""
    url = f"{http_service}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        contestants = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(contestants) is list
    assert len(contestants) == 1


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_contestant_by_id(
    http_service: Any, token: MockFixture, contestant: dict
) -> None:
    """Should return OK and an contestant as json."""
    url = f"{http_service}/contestants"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            contestants = await response.json()
        id = contestants[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url, headers=headers) as response:
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(body) is dict
    assert body["id"]
    assert body["first_name"] == contestant["first_name"]
    assert body["last_name"] == contestant["last_name"]
    assert body["birth_date"] == contestant["birth_date"]
    assert body["club"] == contestant["club"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_contestant(
    http_service: Any, token: MockFixture, contestant: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/contestants"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            contestants = await response.json()
        id = contestants[0]["id"]
        url = f"{url}/{id}"
        request_body = copy.deepcopy(contestant)
        request_body["id"] = id
        request_body["last_name"] = "Updated name"
        async with session.put(url, headers=headers, json=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_contestant(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            contestants = await response.json()
        id = contestants[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204
