"""Contract test cases for contestants."""

import copy
import logging
import os
from collections.abc import AsyncGenerator
from datetime import date, time
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
    """Clear db before and after tests."""
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
        "date_of_event": date(2021, 8, 31).isoformat(),
        "time_of_event": time(9, 0, 0).isoformat(),
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
async def contestant(event_id: str) -> dict:
    """Create a contestant object for testing."""
    return {
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": date(1970, 1, 1).isoformat(),
        "gender": "M",
        "ageclass": "G 12 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": event_id,
        "registration_date_time": "2021-11-08T22:06:30",
    }


@pytest.mark.contract
async def test_create_single_contestant(
    http_service: Any,
    token: MockFixture,
    event_id: str,
    contestant: dict,
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
async def test_get_contestant_by_id(
    http_service: Any, token: MockFixture, event_id: str, contestant: dict
) -> None:
    """Should return OK and an contestant as json."""
    url = f"{http_service}/events/{event_id}/contestants"

    async with ClientSession() as session:
        async with session.get(url) as response:
            contestants = await response.json()
        assert len(contestants) > 0
        assert type(contestants) is list
        id = contestants[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url) as response:
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(body) is dict
    assert body["id"]
    assert body["first_name"] == contestant["first_name"]
    assert body["last_name"] == contestant["last_name"]
    assert body["birth_date"] == contestant["birth_date"]
    assert body["gender"] == contestant["gender"]
    assert body["ageclass"] == contestant["ageclass"]
    assert body["region"] == contestant["region"]
    assert body["club"] == contestant["club"]
    assert body["team"] == contestant["team"]
    assert body["email"] == contestant["email"]
    assert body["registration_date_time"] == contestant["registration_date_time"]
    assert body["event_id"] == event_id


@pytest.mark.contract
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
        async with session.get(url) as response:
            contestants = await response.json()
        assert len(contestants) > 0
        assert type(contestants) is list
        id = contestants[0]["id"]
        url = f"{url}/{id}"
        request_body = copy.deepcopy(contestant)
        request_body["id"] = id
        request_body["last_name"] = "Updated name"
        async with session.put(url, headers=headers, json=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
async def test_delete_contestant(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            contestants = await response.json()
        assert len(contestants) > 0
        assert type(contestants) is list
        id = contestants[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
async def test_create_many_contestants_as_csv_file_from_iSonen(
    http_service: Any,
    token: MockFixture,
    event_id: str,
) -> None:
    """Should return 200 OK and a report."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    # Send csv-file in request:
    files = {"file": open("tests/files/contestants_iSonen.csv", "rb")}
    async with ClientSession() as session:
        async with session.delete(url) as response:
            pass
        async with session.post(url, headers=headers, data=files) as response:
            status = response.status
            body = await response.json()

    assert status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]

    assert len(body) > 0

    assert body["total"] == 77
    assert body["created"] == 77
    assert len(body["updated"]) == 0
    assert len(body["failures"]) == 0
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.contract
async def test_get_all_contestants_in_given_event(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    url = f"{http_service}/events/{event_id}/contestants"

    async with ClientSession() as session:
        async with session.get(url) as response:
            contestants = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(contestants) is list
    assert len(contestants) == 77


@pytest.mark.contract
async def test_get_all_contestants_in_given_event_by_raceclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    async with ClientSession() as session:
        # In this case we have to generate raceclasses first:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201

        raceclass_name = "J 13 år"
        raceclass_parameter = quote(raceclass_name)
        url = f"{http_service}/events/{event_id}/contestants?raceclass={raceclass_parameter}"

        async with session.get(url) as response:
            contestants = await response.json()

    assert response.status == 200, response
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(contestants) is list
    assert len(contestants) == 3
    for contestant in contestants:
        assert contestant["ageclass"] == "J 13 år"


@pytest.mark.contract
async def test_get_all_contestants_in_given_event_by_ageclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    async with ClientSession() as session:
        query_param = f"ageclass={quote('J 13 år')}"
        url = f"{http_service}/events/{event_id}/contestants"
        async with session.get(f"{url}?{query_param}", headers=headers) as response:
            contestants = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(contestants) is list
    assert len(contestants) == 3
    for contestant in contestants:
        assert contestant["ageclass"] == "J 13 år"


@pytest.mark.contract
async def test_get_all_contestants_in_given_event_by_bib(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list with exactly contestant as json."""
    bib = 1

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        # First we add contestants to event:
        url = f"{http_service}/events/{event_id}/contestants"
        files = {"file": open("tests/files/contestants_iSonen.csv", "rb")}
        async with session.post(url, headers=headers, data=files) as response:
            assert response.status == 200

        # We need to generate raceclasses for the event:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        async with session.post(url, headers=headers) as response:
            if response.status != 201:
                body = await response.json()
            assert response.status == 201, body["detail"]  # type: ignore [reportAttributeAccessIssue]
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        # Check that we got the raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()
            assert len(raceclasses) > 0, "No raceclasses found"

        # Finally assign bibs to all contestants:
        url = f"{http_service}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/contestants" in response.headers[hdrs.LOCATION]

        # We can now get the contestants
        url = f"{http_service}/events/{event_id}/contestants"
        async with session.get(url) as response:
            contestants = await response.json()
        assert response.status == 200
        assert len(contestants) > 0
        # We can now get the contestant by bib.
        url = f"{http_service}/events/{event_id}/contestants?bib={bib}"
        async with session.get(url) as response:
            contestants_with_bib = await response.json()

        assert response.status == 200
        assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
        assert type(contestants_with_bib) is list
        assert len(contestants_with_bib) == 1
        assert contestants_with_bib[0]["bib"] == 1


@pytest.mark.contract
async def test_search_contestant_by_name(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 200 OK."""
    url = f"{http_service}/events/{event_id}/contestants/search"
    body = {"name": "Turid"}
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
        hdrs.CONTENT_TYPE: "application/json",
    }

    async with ClientSession() as session:
        async with session.post(url, headers=headers, json=body) as response:
            if response.status != 200:
                body = await response.json()
            assert response.status == 200, body
            contestants = await response.json()

    assert len(contestants) == 1


@pytest.mark.contract
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

        async with session.get(url) as response:
            assert response.status == 200
            contestants = await response.json()
            assert len(contestants) == 0
