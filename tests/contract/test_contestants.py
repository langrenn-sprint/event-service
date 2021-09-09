"""Contract test cases for contestants."""
import asyncio
import copy
import logging
import os
from typing import Any, Optional

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


@pytest.fixture(scope="session")
async def contestant(event_id: str) -> dict:
    """Create a contestant object for testing."""
    return {
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": "1970-01-01",
        "gender": "M",
        "age_class": "G 12 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": event_id,
    }


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_single_contestant(
    http_service: Any, token: MockFixture, event_id: str, contestant: dict
) -> None:
    """Should return 201 Created, location header and no body."""
    url = f"{http_service}/events/{event_id}/contestants"
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
    assert f"/events/{event_id}/contestants/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_many_contestants_as_csv_file(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 200 OK and a report."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    # Send csv-file in request:
    files = {"file": open("tests/files/contestants_eventid_364892.csv", "rb")}
    async with ClientSession() as session:
        async with session.delete(url) as response:
            pass
        async with session.post(url, headers=headers, data=files) as response:
            status = response.status
            body = await response.json()

    assert status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]

    assert len(body) > 0

    assert body["total"] > 0
    assert body["created"] > 0
    assert body["updated"] == 0
    assert body["failures"] == 0
    assert body["total"] == body["created"] + body["updated"] + body["failures"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_many_existing_contestants_as_csv_file(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 200 OK and a report."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    # Send csv-file in request:
    files = {"file": open("tests/files/contestants_eventid_364892.csv", "rb")}
    async with ClientSession() as session:
        async with session.post(url, headers=headers, data=files) as response:
            status = response.status
            body = await response.json()

    assert status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]

    assert len(body) > 0

    assert body["total"] > 0
    assert body["created"] == 0
    assert body["updated"] > 0
    assert body["failures"] == 0
    assert body["total"] == body["created"] + body["updated"] + body["failures"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_contestants_in_given_event(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            contestants = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(contestants) is list
    assert len(contestants) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_contestant_by_id(
    http_service: Any, token: MockFixture, event_id: str, contestant: dict
) -> None:
    """Should return OK and an contestant as json."""
    url = f"{http_service}/events/{event_id}/contestants"

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
    assert body["gender"] == contestant["gender"]
    assert body["age_class"] == contestant["age_class"]
    assert body["region"] == contestant["region"]
    assert body["club"] == contestant["club"]
    assert body["team"] == contestant["team"]
    assert body["email"] == contestant["email"]
    assert body["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_contestant(
    http_service: Any, token: MockFixture, event_id: str, contestant: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
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
async def test_delete_contestant(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
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


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_all_contestant(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204

        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            contestants = await response.json()
            assert len(contestants) == 0
