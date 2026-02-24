"""Contract test cases for generate-raceclass command."""

import logging
import os
from collections.abc import AsyncGenerator
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


@pytest.fixture(autouse=True)
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


@pytest.fixture
async def event_id(
    http_service: Any, token: MockFixture, clear_db: AsyncGenerator
) -> str | None:
    """Create an event object for testing."""
    url = f"{http_service}/events"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = {
        "name": "Oslo Skagen sprint",
        "date_of_event": "2021-09-11",
        "time_of_event": "09:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)

        if response.status_code == HTTPStatus.CREATED:
            # return the event_id, which is the last item of the path
            return response.headers["Location"].split("/")[-1]
        logger.error(
            f"Got unsuccesful status when creating event: {response.status_code}."
        )
    return None


@pytest.mark.contract
async def test_generate_raceclasses(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 201 created and a location header with url to raceclasses."""
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        # First we need to find assert that we have an event:
        url = f"{http_service}/events/{event_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK

        # Then we add contestants to event:
        url = f"{http_service}/events/{event_id}/contestants/file"
        async with aiofiles.open("tests/files/contestants_iSonen.csv") as file:
            content = await file.read()
        files = {"file": ("contestants.csv", content, "text/csv")}
        response = await client.post(url, headers=headers, files=files)
        assert response.status_code == HTTPStatus.OK, response.json()

        # We get the list of contestants:
        url = f"{http_service}/events/{event_id}/contestants"
        response = await client.get(url, headers=headers)
        assert response.status_code == HTTPStatus.OK
        contestants = response.json()

        # Finally raceclasses are generated:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        response = await client.post(url, headers=headers)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
        assert response.status_code == HTTPStatus.CREATED, body
        assert f"/events/{event_id}/raceclasses" in response.headers["Location"]

        # We check that 19 raceclasses are actually created:
        url = response.headers["Location"]
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()
        assert "application/json" in response.headers["Content-Type"]
        assert type(raceclasses) is list

        # Check that we have 19 raceclasses:
        assert len(raceclasses) == 19

        # Check sum of contestants is equal to total no of contestants:
        assert sum(item["no_of_contestants"] for item in raceclasses) == len(
            contestants
        )

        # Check that we have all raceclasses and that sum pr class is correct:
        sorted_list = sorted(raceclasses, key=lambda k: k["name"])

        assert sorted_list[0]["name"] == "G11"
        assert sorted_list[0]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "G 11 år"]
        )
        assert sorted_list[1]["name"] == "G12"
        assert sorted_list[1]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "G 12 år"]
        )
        assert sorted_list[2]["name"] == "G13"
        assert sorted_list[2]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "G 13 år"]
        )
        assert sorted_list[3]["name"] == "G14"
        assert sorted_list[3]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "G 14 år"]
        )
        assert sorted_list[4]["name"] == "G15"
        assert sorted_list[4]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "G 15 år"]
        )
        assert sorted_list[5]["name"] == "G16"
        assert sorted_list[5]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "G 16 år"]
        )
        assert sorted_list[6]["name"] == "J11"
        assert sorted_list[6]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "J 11 år"]
        )
        assert sorted_list[7]["name"] == "J13"
        assert sorted_list[7]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "J 13 år"]
        )
        assert sorted_list[8]["name"] == "J14"
        assert sorted_list[8]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "J 14 år"]
        )
        assert sorted_list[9]["name"] == "J15"
        assert sorted_list[9]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "J 15 år"]
        )
        assert sorted_list[10]["name"] == "J16"
        assert sorted_list[10]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "J 16 år"]
        )
        assert sorted_list[11]["name"] == "K17"
        assert sorted_list[11]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "Kvinner 17"]
        )
        assert sorted_list[12]["name"] == "K18"
        assert sorted_list[12]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "Kvinner 18"]
        )
        assert sorted_list[13]["name"] == "K19-20"
        assert sorted_list[13]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "Kvinner 19-20"]
        )
        assert sorted_list[14]["name"] == "KS"
        assert sorted_list[14]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "Kvinner senior"]
        )
        assert sorted_list[15]["name"] == "M17"
        assert sorted_list[15]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "Menn 17"]
        )
        assert sorted_list[16]["name"] == "M18"
        assert sorted_list[16]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "Menn 18"]
        )
        assert sorted_list[17]["name"] == "M19-20"
        assert sorted_list[17]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "Menn 19-20"]
        )
        assert sorted_list[18]["name"] == "MS"
        assert sorted_list[18]["no_of_contestants"] == len(
            [c for c in contestants if c["ageclass"] == "Menn senior"]
        )
