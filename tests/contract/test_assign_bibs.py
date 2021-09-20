"""Contract test cases for contestants."""
import asyncio
from datetime import date
import logging
import os
from typing import Any, AsyncGenerator, Optional

from aiohttp import ClientSession, hdrs
import pytest
from pytest_mock import MockFixture

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture(scope="session")
def event_loop(request: Any) -> Any:
    """Redefine the event_loop fixture to have the same scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
async def event_id(http_service: Any, token: MockFixture) -> Optional[str]:
    """Create an event object for testing."""
    url = f"{http_service}/events"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {
        "name": "Oslo Skagen sprint",
        "date_of_event": date(2021, 8, 31).isoformat(),
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


@pytest.fixture
@pytest.mark.asyncio
async def clear_db(
    http_service: Any, token: MockFixture, event_id: str
) -> AsyncGenerator:
    """Clear db before and after tests."""
    delete_contestants
    delete_raceclasses
    yield
    delete_raceclasses
    delete_contestants


async def delete_contestants(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Delete all contestants."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.delete(url, headers=headers) as response:
        assert response.status == 204
    await session.close()


async def delete_raceclasses(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Delete all raceclasses."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    url = f"{http_service}/events"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        raceclasses = await response.json()
        for raceclass in raceclasses:
            raceclass_id = raceclass["id"]
            async with session.delete(
                f"{url}/{raceclass_id}", headers=headers
            ) as response:
                assert response.status == 204
    await session.close()


@pytest.mark.contract
@pytest.mark.asyncio
async def test_assign_bibs(
    http_service: Any,
    token: MockFixture,
    event_id: str,
    clear_db: None,
) -> None:
    """Should return 201 Created and a location header with url to contestants."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:

        # First we need to assert that we have an event:
        url = f"{http_service}/events/{event_id}"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200

        # Then we add contestants to event:
        url = f"{http_service}/events/{event_id}/contestants"
        files = {"file": open("tests/files/allcontestants_eventid_364892.csv", "rb")}
        async with session.post(url, headers=headers, data=files) as response:
            assert response.status == 200

        # We need to generate raceclasses for the event:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        # Also we need to set order for all raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceclasses = await response.json()
            order = 0
            for raceclass in raceclasses:
                order += 1
                raceclass["order"] = order
                raceclass_id = raceclass["id"]
                async with session.put(
                    f"{url}/{raceclass_id}", headers=headers, json=raceclass
                ) as response:
                    assert response.status == 204

        # Finally assign bibs to all contestants:
        url = f"{http_service}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/contestants" in response.headers[hdrs.LOCATION]

        # We check that bibs are actually assigned:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url, headers=headers) as response:
            contestants = await response.json()
            assert response.status == 200
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(contestants) is list
            assert len(contestants) > 0
            for c in contestants:
                assert c["bib"] > 0
