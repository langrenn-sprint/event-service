"""Contract test cases for contestants."""

import logging
import os
from collections.abc import AsyncGenerator
from datetime import date, time
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
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)
        body = response.json()
    if response.status_code != HTTPStatus.OK:
        logger.error(
            f"Got unexpected status {response.status_code}/{response.text} from {http_service}."
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
        event_id = response.headers["Location"].split("/")[-1]
        logger.debug(f"Created event with id {event_id}.")
        return event_id
    logger.error(f"Got unsuccesful status when creating event: {status}.")
    return None


@pytest.mark.contract
async def test_assign_bibs(
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
        assert response.status_code == HTTPStatus.OK, response.text

        # Then we add contestants to event:
        headers = {
            "Authorization": f"Bearer {admin_token}",
        }
        url = f"{http_service}/events/{event_id}/contestants/file"
        async with aiofiles.open("tests/files/contestants_iSonen.csv") as file:
            content = await file.read()
        files = {"file": ("contestants.csv", content, "text/csv")}
        response = await client.post(url, headers=headers, files=files)
        assert response.status_code == HTTPStatus.OK, response.text

        # We need to generate raceclasses for the event:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        response = await client.post(url, headers=headers)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
        assert response.status_code == HTTPStatus.CREATED, body["detail"]
        assert f"/events/{event_id}/raceclasses" in response.headers["Location"]

        # We need to work on the raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()

        await _print_raceclasses(raceclasses)

        # We assign ageclasses "G 16 år" and "G 15 år" to the same new raceclass "G15/16":
        raceclass_G16 = await _get_raceclass_by_ageclass(raceclasses, "G 16 år")  # noqa: N806
        raceclass_G15 = await _get_raceclass_by_ageclass(raceclasses, "G 15 år")  # noqa: N806
        raceclass_G15_16: dict = {  # noqa: N806
            "event_id": event_id,
            "name": "G15-16",
            "ageclasses": raceclass_G15["ageclasses"] + raceclass_G16["ageclasses"],
            "gender": "M",
            "ranking": True,
            "seeding": False,
        }
        request_body = raceclass_G15_16
        url = f"{http_service}/events/{event_id}/raceclasses"
        response = await client.post(url, headers=headers, json=request_body)
        assert response.status_code == HTTPStatus.CREATED
        url = f"{http_service}/events/{event_id}/raceclasses/{raceclass_G15['id']}"
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT
        url = f"{http_service}/events/{event_id}/raceclasses/{raceclass_G16['id']}"
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT

        # We get the updated list of raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()

        # Also we need to set order for the remaining raceclasses:
        for raceclass in raceclasses:
            raceclass_id = raceclass["id"]
            (
                raceclass["group"],
                raceclass["order"],
                raceclass["ranking"],
            ) = await _decide_group_order_and_ranking(raceclass)
            url = f"{http_service}/events/{event_id}/raceclasses/{raceclass_id}"
            response = await client.put(url, headers=headers, json=raceclass)
            assert response.status_code == HTTPStatus.NO_CONTENT

        # We again get the updated list of raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()

        await _print_raceclasses(raceclasses)

        # ACT #

        # Finally assign bibs to all contestants:
        url = f"{http_service}/events/{event_id}/contestants/assign-bibs"
        response = await client.post(url, headers=headers)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
        assert response.status_code == HTTPStatus.CREATED, body
        assert f"/events/{event_id}/contestants" in response.headers["Location"]

        # ASSERT #

        # We check that bibs are actually assigned:
        url = response.headers["Location"]
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        contestants = response.json()
        assert type(contestants) is list
        assert len(contestants) > 0

        await _print_contestants(contestants)
        await _dump_contestants_to_json(contestants)

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

        # Check that raceclasses has correct number of contestants:
        assert len(contestants) == sum(
            raceclass["no_of_contestants"] for raceclass in raceclasses
        )


# ---
async def _get_raceclass_by_ageclass(raceclasses: list[dict], ageclass: str) -> dict:
    # Pick out the raceclass where ageclass is in its ageclasses-list:
    for raceclass in raceclasses:
        if ageclass in raceclass["ageclasses"]:
            return raceclass
    return {}


async def _decide_group_order_and_ranking(  # noqa: PLR0911, PLR0912, C901
    raceclass: dict,
) -> tuple[int, int, bool]:
    if raceclass["name"] == "KS":
        return (1, 1, True)
    if raceclass["name"] == "MS":
        return (1, 2, True)
    if raceclass["name"] == "M19-20":
        return (1, 3, True)
    if raceclass["name"] == "K19-20":
        return (1, 4, True)
    if raceclass["name"] == "M18":
        return (2, 1, True)
    if raceclass["name"] == "K18":
        return (2, 2, True)
    if raceclass["name"] == "M17":
        return (3, 1, True)
    if raceclass["name"] == "K17":
        return (3, 2, True)
    if raceclass["name"] == "G15-16":
        return (4, 1, True)
    if raceclass["name"] == "J16":
        return (4, 2, True)
    if raceclass["name"] == "J15":
        return (4, 3, True)
    if raceclass["name"] == "G14":
        return (5, 1, True)
    if raceclass["name"] == "J14":
        return (5, 2, True)
    if raceclass["name"] == "G13":
        return (5, 3, True)
    if raceclass["name"] == "J13":
        return (5, 4, True)
    if raceclass["name"] == "G12":
        return (6, 1, True)
    if raceclass["name"] == "J12":
        return (6, 2, True)
    if raceclass["name"] == "G11":
        return (6, 3, True)
    if raceclass["name"] == "J11":
        return (6, 4, True)
    if raceclass["name"] == "G10":
        return (7, 1, False)
    if raceclass["name"] == "J10":
        return (7, 2, False)
    if raceclass["name"] == "G9":
        return (8, 1, False)
    if raceclass["name"] == "J9":
        return (8, 2, False)
    return (0, 0, True)  # should not reach this point


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
