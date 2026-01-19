"""Contract test cases for contestants."""

import logging
import os
from collections.abc import AsyncGenerator
from datetime import date
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


@pytest.fixture(scope="module", autouse=True)
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
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
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
        event_id = response.headers[hdrs.LOCATION].split("/")[-1]
        logging.debug(f"Created event with id {event_id}.")
        return event_id
    logging.error(f"Got unsuccesful status when creating event: {status}.")
    return None


@pytest.mark.contract
async def test_assign_bibs_start_on_100(
    http_service: Any,
    token: MockFixture,
    event_id: str,
) -> None:
    """Should return 201 Created and a location header with url to contestants."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        # ARRANGE #

        # First we need to assert that we have an event:
        url = f"{http_service}/events/{event_id}"
        logging.debug(f"Verifying event with id {event_id} at url {url}.")
        async with session.get(url) as response:
            assert response.status == 200

        # Then we add contestants to event:
        url = f"{http_service}/events/{event_id}/contestants"
        files = {"file": open("tests/files/contestants_iSonen.csv", "rb")}
        async with session.post(url, headers=headers, data=files) as response:
            assert response.status == 200

        # We need to generate raceclasses for the event:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        async with session.post(url, headers=headers) as response:
            if response.status != 201:
                body = await response.json()
            assert response.status == 201, body["detail"]
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        start_bib = 100
        # ACT #

        # Finally assign bibs to all contestants:
        url = f"{http_service}/events/{event_id}/contestants/assign-bibs?start-bib={start_bib}"
        async with session.post(url, headers=headers) as response:
            if response.status != 201:
                body = await response.json()
            assert response.status == 201, (
                body if body else "Response status was not 201"
            )
            assert f"/events/{event_id}/contestants" in response.headers[hdrs.LOCATION]

        # ASSERT #

        # We check that bibs are actually assigned:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            contestants = await response.json()
            assert response.status == 200
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(contestants) is list
            assert len(contestants) > 0

            # Check that all bib values are ints:
            assert all(
                isinstance(o, (int)) for o in [c.get("bib", None) for c in contestants]
            )

            # Checkt that list is sorted and consecutive:
            assert sorted(set([c["bib"] for c in contestants])) == list(
                range(
                    min(set([c["bib"] for c in contestants])),
                    max(set([c["bib"] for c in contestants])) + 1,
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
