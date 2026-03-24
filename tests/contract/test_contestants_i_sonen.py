"""Contract test cases for contestants."""

import copy
import logging
import os
from collections.abc import AsyncGenerator
from datetime import date, time
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import aiofiles
import motor.motor_asyncio
import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture

from app.utils import db_utils

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "27017"))
DB_NAME = os.getenv("DB_NAME", "events_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
async def admin_token(http_service: Any) -> str:
    """Create a valid token for admin user."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {"Content-Type": "application/json"}
    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)
        body = response.json()
    if response.status_code != HTTPStatus.OK:
        logger.error(
            f"Got unexpected status {response.status_code} from {http_service}."
        )
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
        logger.exception(f"Failed to drop database {DB_NAME}")
        raise error from error

    yield

    try:
        await db_utils.drop_db(mongo, DB_NAME)
    except Exception as error:
        logger.exception(f"Failed to drop database {DB_NAME}")
        raise error from error


@pytest.fixture(scope="module")
async def event_id(
    http_service: Any, admin_token: MockFixture, clear_db: AsyncGenerator
) -> str | None:
    """Create an event object for testing."""
    url = f"{http_service}/events"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}",
    }
    request_body = {
        "name": "Oslo Skagen sprint",
        "date_of_event": date(2021, 8, 31).isoformat(),
        "time_of_event": time(9, 0, 0).isoformat(),
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)
        status = response.status_code
    if status == HTTPStatus.CREATED:
        # return the event_id, which is the last item of the path
        return response.headers["Location"].split("/")[-1]
    logger.error(f"Got unsuccesful status when creating event: {status}.")
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
    admin_token: MockFixture,
    event_id: str,
    contestant: dict,
) -> None:
    """Should return 201 Created, location header and no body."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}",
    }
    request_body = contestant
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)
        status = response.status_code

    assert status == HTTPStatus.CREATED
    assert f"/events/{event_id}/contestants/" in response.headers["Location"]


@pytest.mark.contract
async def test_get_contestant_by_id(
    http_service: Any, admin_token: MockFixture, event_id: str, contestant: dict
) -> None:
    """Should return OK and an contestant as json."""
    url = f"{http_service}/events/{event_id}/contestants"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        contestants = response.json()
        assert len(contestants) > 0
        assert type(contestants) is list
        contestant_id = contestants[0]["id"]
        url = f"{url}/{contestant_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        body = response.json()

    assert response.status_code == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
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
    http_service: Any, admin_token: MockFixture, event_id: str, contestant: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        contestants = response.json()
        assert len(contestants) > 0
        assert type(contestants) is list
        contestant_id = contestants[0]["id"]
        url = f"{url}/{contestant_id}"
        request_body = copy.deepcopy(contestant)
        request_body["id"] = contestant_id
        request_body["last_name"] = "Updated name"
        response = await client.put(url, headers=headers, json=request_body)

    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.contract
async def test_delete_contestant(
    http_service: Any, admin_token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        "Authorization": f"Bearer {admin_token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        contestants = response.json()
        assert len(contestants) > 0
        assert type(contestants) is list
        contestant_id = contestants[0]["id"]
        url = f"{url}/{contestant_id}"
        response = await client.delete(url, headers=headers)

    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.contract
async def test_create_many_contestants_as_csv_file_from_isonen(
    http_service: Any,
    admin_token: MockFixture,
    event_id: str,
) -> None:
    """Should return 200 OK and a report."""
    headers = {
        "Authorization": f"Bearer {admin_token}",
    }

    async with aiofiles.open("tests/files/contestants_iSonen.csv") as file:
        content = await file.read()
    files = {"file": ("contestants.csv", content, "text/csv")}
    async with AsyncClient() as client:
        # We need to delete all contestants before we can add the contestants from the file:
        url = f"{http_service}/events/{event_id}/contestants"
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT, response.json()
        url = f"{http_service}/events/{event_id}/contestants/file"
        response = await client.post(url, headers=headers, files=files)
        status = response.status_code
        body = response.json()
        assert status == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]

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
    http_service: Any, admin_token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    url = f"{http_service}/events/{event_id}/contestants"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        contestants = response.json()
        assert type(contestants) is list
        assert len(contestants) == 77


@pytest.mark.contract
async def test_get_all_contestants_in_given_event_by_raceclass(
    http_service: Any, admin_token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    headers = {
        "Authorization": f"Bearer {admin_token}",
    }

    async with AsyncClient() as client:
        # In this case we have to generate raceclasses first:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        response = await client.post(url, headers=headers)
        assert response.status_code == HTTPStatus.CREATED

        raceclass_name = "J13"
        raceclass_parameter = quote(raceclass_name)
        url = f"{http_service}/events/{event_id}/contestants?raceclass-name={raceclass_parameter}"

        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK, response
        assert "application/json" in response.headers["Content-Type"]
        contestants = response.json()
        assert type(contestants) is list
        assert len(contestants) == 3
        for contestant in contestants:
            assert contestant["ageclass"] == "J 13 år"


@pytest.mark.contract
async def test_get_all_contestants_in_given_event_by_ageclass(
    http_service: Any, admin_token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    headers = {
        "Authorization": f"Bearer {admin_token}",
    }
    async with AsyncClient() as client:
        query_param = f"ageclass-name={quote('J 13 år')}"
        url = f"{http_service}/events/{event_id}/contestants"
        response = await client.get(f"{url}?{query_param}", headers=headers)
        assert response.status_code == HTTPStatus.OK, response
        response = await client.get(f"{url}?{query_param}", headers=headers)
        contestants = response.json()

        assert response.status_code == HTTPStatus.OK, response
        assert "application/json" in response.headers["Content-Type"]
        assert type(contestants) is list
        assert len(contestants) == 3
        for contestant in contestants:
            assert contestant["ageclass"] == "J 13 år"


@pytest.mark.contract
async def test_get_all_contestants_in_given_event_by_bib(
    http_service: Any, admin_token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list with exactly contestant as json."""
    bib = 1

    headers = {
        "Authorization": f"Bearer {admin_token}",
    }

    async with AsyncClient() as client:
        # First we add contestants to event:
        url = f"{http_service}/events/{event_id}/contestants/file"
        async with aiofiles.open("tests/files/contestants_iSonen.csv") as file:
            content = await file.read()
        files = {"file": ("contestants.csv", content, "text/csv")}
        response = await client.post(url, headers=headers, files=files)
        assert response.status_code == HTTPStatus.OK, response

        # We need to generate raceclasses for the event:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        response = await client.post(url, headers=headers)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
        assert response.status_code == HTTPStatus.CREATED, body["detail"]
        assert f"/events/{event_id}/raceclasses" in response.headers["Location"]

        # Check that we got the raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()
        assert len(raceclasses) > 0, "No raceclasses found"

        # Finally assign bibs to all contestants:
        url = f"{http_service}/events/{event_id}/contestants/assign-bibs"
        response = await client.post(url, headers=headers)
        assert response.status_code == HTTPStatus.CREATED, response
        assert f"/events/{event_id}/contestants" in response.headers["Location"]

        # We can now get the contestants
        url = f"{http_service}/events/{event_id}/contestants"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        contestants = response.json()
        assert len(contestants) > 0
        # We can now get the contestant by bib.
        url = f"{http_service}/events/{event_id}/contestants?bib={bib}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        contestants_with_bib = response.json()
        assert type(contestants_with_bib) is list
        assert len(contestants_with_bib) == 1
        assert contestants_with_bib[0]["bib"] == 1


@pytest.mark.contract
async def test_search_contestant_by_name(
    http_service: Any, admin_token: MockFixture, event_id: str
) -> None:
    """Should return 200 OK."""
    url = f"{http_service}/events/{event_id}/contestants/search"
    body = {"name": "Turid"}
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }

    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body)
        if response.status_code != HTTPStatus.OK:
            body = response.json()
        assert response.status_code == HTTPStatus.OK, body
        contestants = response.json()
        assert len(contestants) == 1


@pytest.mark.contract
async def test_delete_all_contestant(
    http_service: Any, admin_token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        "Authorization": f"Bearer {admin_token}",
    }

    async with AsyncClient() as client:
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        contestants = response.json()
        assert len(contestants) == 0
