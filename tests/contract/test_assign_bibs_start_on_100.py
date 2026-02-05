"""Contract test cases for contestants."""

import logging
import os
from collections.abc import AsyncGenerator
from datetime import date
from http import HTTPStatus
from typing import Any

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


@pytest.fixture(scope="module", autouse=True)
async def admin_token(http_service: Any) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {"Content-Type": "application/json"}
    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    async with AsyncClient() as session:
        response = await session.post(url, headers=headers, json=request_body)
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
    http_service: Any,
    admin_token: MockFixture,
    clear_db: AsyncGenerator,
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
        "time_of_event": "12:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }

    async with AsyncClient() as session:
        response = await session.post(url, headers=headers, json=request_body)
        status = response.status_code
    if status == HTTPStatus.CREATED:
        # return the event_id, which is the last item of the path
        event_id = response.headers["Location"].split("/")[-1]
        logger.debug(f"Created event with id {event_id}.")
        return event_id
    logger.error(f"Got unsuccesful status when creating event: {status}.")
    return None


@pytest.mark.contract
async def test_assign_bibs_start_on_100(
    http_service: Any,
    admin_token: MockFixture,
    event_id: str,
) -> None:
    """Should return 201 Created and a location header with url to contestants."""
    headers = {
        "Authorization": f"Bearer {admin_token}",
    }

    async with AsyncClient() as client:
        # ARRANGE #

        # First we need to assert that we have an event:
        url = f"{http_service}/events/{event_id}"
        logger.debug(f"Verifying event with id {event_id} at url {url}.")
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK

        # Then we add contestants to event:
        url = f"{http_service}/events/{event_id}/contestants/file"
        async with aiofiles.open("tests/files/contestants_iSonen.csv") as file:
            content = await file.read()
        files = {"file": ("contestants.csv", content, "text/csv")}
        response = await client.post(url, headers=headers, files=files)
        assert response.status_code == HTTPStatus.OK

        # We need to generate raceclasses for the event:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        response = await client.post(url, headers=headers)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
        assert response.status_code == HTTPStatus.CREATED, body["detail"]
        assert f"/events/{event_id}/raceclasses" in response.headers["Location"]
        start_bib = 100
        # ACT #

        # Finally assign bibs to all contestants:
        url = f"{http_service}/events/{event_id}/contestants/assign-bibs?start-bib={start_bib}"
        response = await client.post(url, headers=headers)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
        assert response.status_code == HTTPStatus.CREATED, (
            body or "Response status was not 201"
        )
        assert f"/events/{event_id}/contestants" in response.headers["Location"]

        # ASSERT #

        # We check that bibs are actually assigned:
        url = response.headers["Location"]
        response = await client.get(url)
        contestants = response.json()
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        assert type(contestants) is list
        assert len(contestants) > 0

        # Check that all bib values are ints:
        assert all(
            isinstance(o, (int)) for o in [c.get("bib", None) for c in contestants]
        )

        # Checkt that list is sorted and consecutive:
        assert sorted(c["bib"] for c in contestants) == list(
            range(
                min(c["bib"] for c in contestants),
                max(c["bib"] for c in contestants) + 1,
            )
        )

        # Check that the first bib is 100:
        assert contestants[0]["bib"] == start_bib


# ---


async def _print_raceclasses(raceclasses: list[dict]) -> None:
    # print("--- RACECLASSES ---")
    # print("group;order;name;ageclasses;no_of_contestants;distance;ranking;event_id")
    # for raceclass in raceclasses:
    #     print(
    #         str(raceclass["group"])
    #         + ";"
    #         + str(raceclass["order"])
    #         + ";"
    #         + raceclass["name"]
    #         + ";"
    #         + "".join(raceclass["ageclasses"])
    #         + ";"
    #         + str(raceclass["no_of_contestants"])
    #         + ";"
    #         + str(raceclass["distance"])
    #         + ";"
    #         + str(raceclass["ranking"])
    #         + ";"
    #         + str(raceclass["seeding"])
    #         + ";"
    #         + raceclass["event_id"]
    #     )
    pass


async def _print_contestants(contestants: list[dict]) -> None:
    # print("--- CONTESTANTS ---")
    # print(f"Number of contestants: {len(contestants)}.")
    # print("bib;ageclass")
    # for contestant in contestants:
    #     print(str(contestant["bib"]) + ";" + str(contestant["ageclass"]))
    pass


async def _dump_contestants_to_json(contestants: list[dict]) -> None:
    # with open("tests/files/tmp_startlist.json", "w") as file:
    #     json.dump(contestants, file)
    pass
