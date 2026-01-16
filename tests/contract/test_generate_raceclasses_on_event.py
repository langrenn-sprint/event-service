"""Contract test cases for generate-raceclass command."""

import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

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


@pytest.fixture(scope="function", autouse=True)
async def clear_db() -> AsyncGenerator:
    """Delete all events before we start."""
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


@pytest.fixture(scope="function")
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
        "date_of_event": "2021-09-11",
        "tim_of_event": "09:00:00",
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


@pytest.mark.contract
async def test_generate_raceclasses(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 201 created and a location header with url to raceclasses."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        # First we need to find assert that we have an event:
        url = f"{http_service}/events/{event_id}"
        async with session.get(url) as response:
            assert response.status == 200

        # Then we add contestants to event:
        url = f"{http_service}/events/{event_id}/contestants"
        files = {"file": open("tests/files/contestants_iSonen.csv", "rb")}
        async with session.post(url, headers=headers, data=files) as response:
            assert response.status == 200

        # We get the list of contestants:
        url = f"{http_service}/events/{event_id}/contestants"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            contestants = await response.json()

        # Finally raceclasses are generated:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        async with session.post(url, headers=headers) as response:
            if response.status != 201:
                body = await response.json()
            assert response.status == 201, body  # type: ignore [reportAttributeAccessIssue]
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        # We check that 19 raceclasses are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceclasses) is list

            # Check that we have 19 raceclasses:
            assert len(raceclasses) == 19

            # Check sum of contestants is equal to total no of contestants:
            assert sum(item["no_of_contestants"] for item in raceclasses) == len(
                contestants
            )

            # Check that we have all raceclasses and that sum pr class is correct:
            sorted_list = sorted(raceclasses, key=lambda k: k["name"])

            assert sorted_list[0]["name"] == "G 11 år"
            assert sorted_list[0]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 11 år"]
            )
            assert sorted_list[1]["name"] == "G 12 år"
            assert sorted_list[1]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 12 år"]
            )
            assert sorted_list[2]["name"] == "G 13 år"
            assert sorted_list[2]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 13 år"]
            )
            assert sorted_list[3]["name"] == "G 14 år"
            assert sorted_list[3]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 14 år"]
            )
            assert sorted_list[4]["name"] == "G 15 år"
            assert sorted_list[4]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 15 år"]
            )
            assert sorted_list[5]["name"] == "G 16 år"
            assert sorted_list[5]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 16 år"]
            )
            assert sorted_list[6]["name"] == "J 11 år"
            assert sorted_list[6]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 11 år"]
            )
            assert sorted_list[7]["name"] == "J 13 år"
            assert sorted_list[7]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 13 år"]
            )
            assert sorted_list[8]["name"] == "J 14 år"
            assert sorted_list[8]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 14 år"]
            )
            assert sorted_list[9]["name"] == "J 15 år"
            assert sorted_list[9]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 15 år"]
            )
            assert sorted_list[10]["name"] == "J 16 år"
            assert sorted_list[10]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 16 år"]
            )
            assert sorted_list[11]["name"] == "Kvinner 17"
            assert sorted_list[11]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "Kvinner 17"]
            )
            assert sorted_list[12]["name"] == "Kvinner 18"
            assert sorted_list[12]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "Kvinner 18"]
            )
            assert sorted_list[13]["name"] == "Kvinner 19-20"
            assert sorted_list[13]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "Kvinner 19-20"]
            )
            assert sorted_list[14]["name"] == "Kvinner senior"
            assert sorted_list[14]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "Kvinner senior"]
            )
            assert sorted_list[15]["name"] == "Menn 17"
            assert sorted_list[15]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "Menn 17"]
            )
            assert sorted_list[16]["name"] == "Menn 18"
            assert sorted_list[16]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "Menn 18"]
            )
            assert sorted_list[17]["name"] == "Menn 19-20"
            assert sorted_list[17]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "Menn 19-20"]
            )
            assert sorted_list[18]["name"] == "Menn senior"
            assert sorted_list[18]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "Menn senior"]
            )
