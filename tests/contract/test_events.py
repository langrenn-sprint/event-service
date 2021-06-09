"""Contract test cases for ping."""
from typing import Any

from aiohttp import ClientSession, hdrs
import pytest


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_event(http_service: Any) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/events"
    headers = {hdrs.CONTENT_TYPE: "application/json"}
    request_body = {"name": "Oslo Skagen sprint"}
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert "/events/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_events(http_service: Any) -> None:
    """Should return OK and a list of events as json."""
    url = f"{http_service}/events"

    session = ClientSession()
    async with session.get(url) as response:
        events = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(events) is list
    assert len(events) == 1


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_event(http_service: Any) -> None:
    """Should return OK and an event as json."""
    url = f"{http_service}/events"

    async with ClientSession() as session:
        async with session.get(url) as response:
            events = await response.json()
        id = events[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url) as response:
            event = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(event) is dict
    assert event["id"]
    assert event["name"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_event(http_service: Any) -> None:
    """Should return No Content."""
    url = f"{http_service}/events"
    headers = {hdrs.CONTENT_TYPE: "application/json"}

    async with ClientSession() as session:
        async with session.get(url) as response:
            events = await response.json()
        id = events[0]["id"]
        url = f"{url}/{id}"
        request_body = {"id": id, "name": "Oslo Skagen sprint updated"}
        async with session.put(url, headers=headers, json=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_event(http_service: Any) -> None:
    """Should return No Content."""
    url = f"{http_service}/events"

    async with ClientSession() as session:
        async with session.get(url) as response:
            events = await response.json()
        id = events[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url) as response:
            pass

    assert response.status == 204
