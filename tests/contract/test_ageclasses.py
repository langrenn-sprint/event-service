"""Contract test cases for ping."""
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


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_ageclass(http_service: Any, token: MockFixture) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/ageclasses"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {"name": "Oslo Skagen sprint"}
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert "/ageclasses/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_ageclasses(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of ageclasses as json."""
    url = f"{http_service}/ageclasses"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        ageclasses = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(ageclasses) is list
    assert len(ageclasses) == 1


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_ageclass(http_service: Any, token: MockFixture) -> None:
    """Should return OK and an ageclass as json."""
    url = f"{http_service}/ageclasses"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            ageclasses = await response.json()
        id = ageclasses[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url, headers=headers) as response:
            ageclass = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(ageclass) is dict
    assert ageclass["id"]
    assert ageclass["name"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_ageclass(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/ageclasses"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            ageclasses = await response.json()
        id = ageclasses[0]["id"]
        url = f"{url}/{id}"
        request_body = {"id": id, "name": "Oslo Skagen sprint updated"}
        async with session.put(url, headers=headers, json=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_ageclass(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/ageclasses"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            ageclasses = await response.json()
        id = ageclasses[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204
