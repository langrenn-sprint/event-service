"""Contract test cases for generate-raceclass command."""
import asyncio
from datetime import date
import logging
import os
from typing import Any, Optional

from aiohttp import ClientSession, hdrs
import pytest
from pytest_mock import MockFixture

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


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


@pytest.fixture(scope="module")
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
        async with session.get(url, headers=headers) as response:
            assert response.status == 200

        # Then we add contestants to event:
        url = f"{http_service}/events/{event_id}/contestants"
        files = {"file": open("tests/files/allcontestants_eventid_364892.csv", "rb")}
        async with session.post(url, headers=headers, data=files) as response:
            assert response.status == 200

        # Finally raceclasses are generated:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        # We check that 12 raceclasses are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceclasses = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceclasses) is list

            # Check that we have 12 raceclasses:
            assert len(raceclasses) == 12

            # Check sum of contestants is equal to total no of contestants:
            assert sum(item["no_of_contestants"] for item in raceclasses) == 333

            # Check that we have all raceclasses and that sum pr class is correct:
            sorted_list = sorted(raceclasses, key=lambda k: k["name"])
            assert (
                sorted_list[0]["name"] == "G11"
                and sorted_list[0]["no_of_contestants"] == 17
            )
            assert (
                sorted_list[1]["name"] == "G12"
                and sorted_list[1]["no_of_contestants"] == 37
            )
            assert (
                sorted_list[2]["name"] == "G13"
                and sorted_list[2]["no_of_contestants"] == 29
            )
            assert (
                sorted_list[3]["name"] == "G14"
                and sorted_list[3]["no_of_contestants"] == 26
            )
            assert (
                sorted_list[4]["name"] == "G15"
                and sorted_list[4]["no_of_contestants"] == 45
            )
            assert (
                sorted_list[5]["name"] == "G16"
                and sorted_list[5]["no_of_contestants"] == 36
            )
            assert (
                sorted_list[6]["name"] == "J11"
                and sorted_list[6]["no_of_contestants"] == 17
            )
            assert (
                sorted_list[7]["name"] == "J12"
                and sorted_list[7]["no_of_contestants"] == 18
            )
            assert (
                sorted_list[8]["name"] == "J13"
                and sorted_list[8]["no_of_contestants"] == 29
            )
            assert (
                sorted_list[9]["name"] == "J14"
                and sorted_list[9]["no_of_contestants"] == 19
            )
            assert (
                sorted_list[10]["name"] == "J15"
                and sorted_list[10]["no_of_contestants"] == 42
            )
            assert (
                sorted_list[11]["name"] == "J16"
                and sorted_list[11]["no_of_contestants"] == 18
            )
