"""Contract test cases for ping."""

import logging
import os
from collections.abc import AsyncGenerator
from datetime import date
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

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
async def token(http_service: Any) -> str:
    """Create a valid token."""
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
    """Delete all events before we start."""
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
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
) -> str | None:
    """Create an event object for testing."""
    url = f"{http_service}/events"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = {
        "name": "Oslo Skagen sprint",
        "date_of_event": "2021-08-31",
        "time_of_event": "12:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)

        assert response.status_code == HTTPStatus.CREATED, response.text
        return response.headers["Location"].split("/")[-1]


@pytest.fixture(scope="module")
async def raceclasses(event_id: str) -> list[dict]:
    """Create a raceclass object for testing."""
    return [
        {
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "gender": "M",
            "event_id": event_id,
            "group": 1,
            "order": 1,
            "no_of_contestants": 0,
            "ranking": True,
            "seeding": False,
            "distance": "5km",
        },
        {
            "name": "G15",
            "ageclasses": ["G 15 år"],
            "gender": "M",
            "event_id": event_id,
            "group": 1,
            "order": 2,
            "no_of_contestants": 0,
            "ranking": True,
            "seeding": False,
            "distance": "5km",
        },
    ]


@pytest.mark.contract
async def test_create_raceclass(
    http_service: Any, token: MockFixture, event_id: str, raceclasses: list[dict]
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    for raceclass in raceclasses:
        request_body = raceclass
        async with AsyncClient() as client:
            response = await client.post(url, headers=headers, json=request_body)
            assert response.status_code == HTTPStatus.CREATED, response.text
            assert f"/events/{event_id}/raceclasses/" in response.headers["Location"]


@pytest.mark.contract
async def test_get_all_raceclasses(
    http_service: Any,
    event_id: str,
) -> None:
    """Should return OK and a list of raceclasses as json."""
    url = f"{http_service}/events/{event_id}/raceclasses"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        raceclasses = response.json()
        assert type(raceclasses) is list
        assert len(raceclasses) == 2


@pytest.mark.contract
async def test_get_all_raceclasses_by_name(http_service: Any, event_id: str) -> None:
    """Should return OK and a list of raceclasses as json."""
    name_parameter = "G16"
    url = f"{http_service}/events/{event_id}/raceclasses?name={name_parameter}"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        raceclasses = response.json()
        assert type(raceclasses) is list
        assert len(raceclasses) == 1
        assert raceclasses[0]["name"] == name_parameter


@pytest.mark.contract
async def test_get_all_raceclasses_by_ageclass_name(
    http_service: Any, event_id: str
) -> None:
    """Should return OK and a list of raceclasses as json."""
    ageclass_name = "G 16 år"
    ageclass_name_parameter = quote(ageclass_name)
    url = (
        f"{http_service}/events/{event_id}/raceclasses?ageclass-name"
        f"={ageclass_name_parameter}"
    )

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        raceclasses = response.json()
        assert type(raceclasses) is list
        assert len(raceclasses) == 1
        assert raceclasses[0]["ageclasses"] == [ageclass_name]


@pytest.mark.contract
async def test_get_raceclass_by_id(
    http_service: Any, event_id: str, raceclasses: list[dict]
) -> None:
    """Should return OK and an raceclass as json."""
    url = f"{http_service}/events/{event_id}/raceclasses"

    async with AsyncClient() as client:
        response = await client.get(url)
        raceclasses = response.json()
        raceclass_id = raceclasses[0]["id"]
        url = f"{url}/{raceclass_id}"
        response = await client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        body = response.json()
        assert type(body) is dict
        assert (
            body["name"] == raceclasses[0]["name"]
            or body["name"] == raceclasses[1]["name"]
        )
        assert (
            body["ageclasses"] == raceclasses[0]["ageclasses"]
            or body["ageclasses"] == raceclasses[1]["ageclasses"]
        )
        assert body["gender"] == "M"
        assert body["event_id"] == event_id
        assert body["group"] == 1
        assert body["order"] == 1 or body["order"] == 2
        assert body["no_of_contestants"] == 0
        assert body["ranking"] is True
        assert body["seeding"] is False
        assert body["distance"] == "5km"


@pytest.mark.contract
async def test_update_raceclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return No Content."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        raceclasses = response.json()
        assert response.status_code == HTTPStatus.OK

        _raceclass = raceclasses[0]
        raceclass_id = _raceclass["id"]
        _raceclass["name"] = _raceclass["name"] + "/G15"
        _raceclass["ageclasses"].append("G 15 år")

        url = f"{url}/{raceclass_id}"
        response = await client.put(url, headers=headers, json=_raceclass)
        assert response.status_code == HTTPStatus.NO_CONTENT

        response = await client.get(url)
        raceclass = response.json()
        assert response.status_code == HTTPStatus.OK
        assert raceclass["name"] == _raceclass["name"]
        assert raceclass["ageclasses"] == _raceclass["ageclasses"]


@pytest.mark.contract
async def test_delete_raceclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return No Content."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        raceclasses = response.json()
        raceclass_id = raceclasses[0]["id"]
        url = f"{url}/{raceclass_id}"
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.contract
async def test_delete_all_raceclasses(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT

        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()
        assert len(raceclasses) == 0


@pytest.mark.contract
async def test_add_contestant_to_raceclass(
    http_service: Any, token: MockFixture, event_id: str, raceclasses: list[dict]
) -> None:
    """Should update the number of contestants."""
    # First we create a raceclass:
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    for raceclass in raceclasses:
        request_body = raceclass
        async with AsyncClient() as client:
            response = await client.post(url, headers=headers, json=request_body)

            assert response.status_code == HTTPStatus.CREATED
            assert f"/events/{event_id}/raceclasses/" in response.headers["Location"]

    # Create a contestant:
    contestant = {
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": date(1970, 1, 1).isoformat(),
        "gender": "M",
        "ageclass": "G 16 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": event_id,
        "registration_date_time": "2021-11-08T22:06:30",
    }
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=contestant)

        assert response.status_code == HTTPStatus.CREATED
        assert f"/events/{event_id}/contestants/" in response.headers["Location"]

        # Get the raceclass and check number of contestants:
        ageclass_name = contestant["ageclass"]
        ageclass_name_parameter = quote(ageclass_name)

        url = f"{http_service}/events/{event_id}/raceclasses?ageclass-name={ageclass_name_parameter}"

        response = await client.get(url)
        raceclasses = response.json()

        assert response.status_code == HTTPStatus.OK
        assert type(raceclasses) is list
        assert len(raceclasses) == 1
        assert raceclasses[0]["ageclasses"] == [ageclass_name]
        assert raceclasses[0]["no_of_contestants"] == 1


@pytest.mark.contract
async def test_delete_contestant_to_raceclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should update the number of contestants."""
    # Create another contestant:
    contestant = {
        "first_name": "Another Conte.",
        "last_name": "Stant",
        "birth_date": date(1970, 1, 1).isoformat(),
        "gender": "M",
        "ageclass": "G 16 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": event_id,
        "registration_date_time": "2021-11-08T22:06:30",
    }
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=contestant)

        assert response.status_code == HTTPStatus.CREATED
        assert f"/events/{event_id}/contestants/" in response.headers["Location"]
        contestant_id = response.headers["Location"].split("/")[-1]

        # Get the raceclass and check number of contestants:
        ageclass_name = contestant["ageclass"]
        ageclass_name_parameter = quote(ageclass_name)
        url = f"{http_service}/events/{event_id}/raceclasses?ageclass-name={ageclass_name_parameter}"

        response = await client.get(url)

        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()
        assert type(raceclasses) is list
        assert len(raceclasses) == 1
        assert raceclasses[0]["ageclasses"] == [ageclass_name]
        assert raceclasses[0]["no_of_contestants"] == 2

        # Now we delete the contestant:
        url = f"{http_service}/events/{event_id}/contestants/{contestant_id}"
        headers = {
            "Authorization": f"Bearer {token}",
        }
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT

        # Get the raceclass and check number of contestants:
        ageclass_name = contestant["ageclass"]
        ageclass_name_parameter = quote(ageclass_name)
        url = f"{http_service}/events/{event_id}/raceclasses?ageclass-name={ageclass_name_parameter}"

        response = await client.get(url)
        raceclasses = response.json()

        assert response.status_code == HTTPStatus.OK
        assert type(raceclasses) is list
        assert len(raceclasses) == 1
        assert raceclasses[0]["ageclasses"] == [ageclass_name]
        assert raceclasses[0]["no_of_contestants"] == 1


@pytest.mark.contract
async def test_change_contestants_ageclass(
    http_service: Any, token: MockFixture, event_id: str, raceclasses: list[dict]
) -> None:
    """Should update the number of contestants in old and new ageclasses."""
    # Create another contestant:
    contestant = {
        "first_name": "Just Another Conte.",
        "last_name": "Stant",
        "birth_date": date(1970, 1, 1).isoformat(),
        "gender": "M",
        "ageclass": "G 16 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": event_id,
        "registration_date_time": "2021-11-08T22:06:30",
    }
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    async with AsyncClient() as client:
        await client.delete(url, headers=headers)
        response = await client.post(url, headers=headers, json=contestant)
        assert response.status_code == HTTPStatus.CREATED
        assert f"/events/{event_id}/contestants/" in response.headers["Location"]
        contestant_id = response.headers["Location"].split("/")[-1]

        # We need to clean up and create the raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT, response.json()
        for raceclass in raceclasses:
            request_body = raceclass
            response = await client.post(
                url,
                headers=headers,
                json=request_body,
            )
            assert response.status_code == HTTPStatus.CREATED, response.json()
            assert f"/events/{event_id}/raceclasses/" in response.headers["Location"]

        # Get the raceclass and check number of contestants:
        ageclass_name = contestant["ageclass"]
        ageclass_name_parameter = quote(ageclass_name)
        url = f"{http_service}/events/{event_id}/raceclasses?ageclass-name={ageclass_name_parameter}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()
        assert type(raceclasses) is list
        assert len(raceclasses) == 1
        assert raceclasses[0]["ageclasses"] == [ageclass_name]
        assert raceclasses[0]["no_of_contestants"] == 1

        # Now we change the ageclass of the contestant:
        url = f"{http_service}/events/{event_id}/contestants/{contestant_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        contestant["id"] = contestant_id
        contestant["ageclass"] = "G 15 år"

        response = await client.put(url, headers=headers, json=contestant)

        assert response.status_code == HTTPStatus.NO_CONTENT

        # Get the old raceclass and check number of contestants:
        ageclass_name = "G 16 år"
        ageclass_name_parameter = quote(ageclass_name)
        url = f"{http_service}/events/{event_id}/raceclasses?ageclass-name={ageclass_name_parameter}"

        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()
        assert type(raceclasses) is list
        assert len(raceclasses) == 1
        assert raceclasses[0]["ageclasses"] == [ageclass_name]
        assert raceclasses[0]["no_of_contestants"] == 0

        # Get the new raceclass and check number of contestants:
        ageclass_name = "G 15 år"
        ageclass_name_parameter = quote(ageclass_name)
        url = f"{http_service}/events/{event_id}/raceclasses?ageclass-name={ageclass_name_parameter}"

        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()
        assert type(raceclasses) is list
        assert len(raceclasses) == 1
        assert raceclasses[0]["ageclasses"] == [ageclass_name]
        assert raceclasses[0]["no_of_contestants"] == 1
