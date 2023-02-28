"""Contract test cases for generate-raceclass command."""
import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Optional

from aiohttp import ClientSession, hdrs
import motor.motor_asyncio
import pytest
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
def event_loop(request: Any) -> Any:
    """Redefine the event_loop fixture to have the same scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
@pytest.mark.asyncio
async def clear_db() -> AsyncGenerator:
    """Delete all events before we start."""
    mongo = motor.motor_asyncio.AsyncIOMotorClient(
        host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASSWORD
    )
    try:
        await db_utils.drop_db_and_recreate_indexes(mongo, DB_NAME)
    except Exception as error:
        logging.error(f"Failed to drop database {DB_NAME}: {error}")
        raise error

    yield

    try:
        await db_utils.drop_db(mongo, DB_NAME)
    except Exception as error:
        logging.error(f"Failed to drop database {DB_NAME}: {error}")
        raise error


@pytest.fixture(scope="module")
async def event_id(
    http_service: Any, token: MockFixture, clear_db: AsyncGenerator
) -> Optional[str]:
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
    else:
        logging.error(f"Got unsuccesful status when creating event: {status}.")
        return None


@pytest.mark.contract
@pytest.mark.asyncio
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
        files = {"file": open("tests/files/contestants_all.csv", "rb")}
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
            assert response.status == 201, body
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        # We check that 22 raceclasses are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceclasses) is list

            # Check that we have 22 raceclasses:
            assert len(raceclasses) == 22

            # Check sum of contestants is equal to total no of contestants:
            assert sum(item["no_of_contestants"] for item in raceclasses) == len(
                contestants
            )

            # Check that we have all raceclasses and that sum pr class is correct:
            sorted_list = sorted(raceclasses, key=lambda k: k["name"])

            assert sorted_list[0]["name"] == "G10"
            assert sorted_list[0]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 10 år"]
            )
            assert sorted_list[1]["name"] == "G11"
            assert sorted_list[1]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 11 år"]
            )
            assert sorted_list[2]["name"] == "G12"
            assert sorted_list[2]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 12 år"]
            )

            assert sorted_list[3]["name"] == "G13"
            assert sorted_list[3]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 13 år"]
            )

            assert sorted_list[4]["name"] == "G14"
            assert sorted_list[4]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 14 år"]
            )

            assert sorted_list[5]["name"] == "G15"
            assert sorted_list[5]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 15 år"]
            )

            assert sorted_list[6]["name"] == "G16"
            assert sorted_list[6]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 16 år"]
            )

            assert sorted_list[7]["name"] == "G9"
            assert sorted_list[7]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "G 9 år"]
            )

            assert sorted_list[8]["name"] == "J10"
            assert sorted_list[8]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 10 år"]
            )

            assert sorted_list[9]["name"] == "J11"
            assert sorted_list[9]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 11 år"]
            )

            assert sorted_list[10]["name"] == "J12"
            assert sorted_list[10]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 12 år"]
            )

            assert sorted_list[11]["name"] == "J13"
            assert sorted_list[11]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 13 år"]
            )

            assert sorted_list[12]["name"] == "J14"
            assert sorted_list[12]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 14 år"]
            )

            assert sorted_list[13]["name"] == "J15"
            assert sorted_list[13]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 15 år"]
            )

            assert sorted_list[14]["name"] == "J16"
            assert sorted_list[14]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 16 år"]
            )

            assert sorted_list[15]["name"] == "J9"
            assert sorted_list[15]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "J 9 år"]
            )

            assert sorted_list[16]["name"] == "K17"
            assert sorted_list[16]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "K 17 år"]
            )

            assert sorted_list[17]["name"] == "K18"
            assert sorted_list[17]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "K 18 år"]
            )

            assert sorted_list[18]["name"] == "K19/20"
            assert sorted_list[18]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "K 19/20 år"]
            )

            assert sorted_list[19]["name"] == "M17"
            assert sorted_list[19]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "M 17 år"]
            )

            assert sorted_list[20]["name"] == "M18"
            assert sorted_list[20]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "M 18 år"]
            )

            assert sorted_list[21]["name"] == "M19/20"
            assert sorted_list[21]["no_of_contestants"] == len(
                [c for c in contestants if c["ageclass"] == "M 19/20 år"]
            )
