"""Contract test cases for contestants."""
import asyncio
from datetime import date
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

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
@pytest.mark.asyncio
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
    """Clear db before and after tests."""
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
@pytest.mark.asyncio
async def event_id(
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
) -> Optional[str]:
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
    else:
        logging.error(f"Got unsuccesful status when creating event: {status}.")
        return None


@pytest.mark.contract
@pytest.mark.asyncio
async def test_assign_bibs(
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
        files = {"file": open("tests/files/contestants_all.csv", "rb")}
        async with session.post(url, headers=headers, data=files) as response:
            assert response.status == 200

        # We need to generate raceclasses for the event:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        async with session.post(url, headers=headers) as response:
            if response.status != 201:
                body = await response.json()
            assert response.status == 201, body["detail"]
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        # We need to work on the raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()

        await _print_raceclasses(raceclasses)

        # We assign ageclasses "G 16 år" and "G 15 år" to the same new raceclass "G15/16":
        raceclass_G16 = await _get_raceclass_by_ageclass(raceclasses, "G 16 år")
        raceclass_G15 = await _get_raceclass_by_ageclass(raceclasses, "G 15 år")
        raceclass_G15_16: Dict = {
            "event_id": event_id,
            "name": "G15/16",
            "ageclasses": raceclass_G15["ageclasses"] + raceclass_G16["ageclasses"],
            "no_of_contestants": raceclass_G15["no_of_contestants"]
            + raceclass_G16["no_of_contestants"],
            "ranking": True,
            "seeding": False,
        }
        request_body = raceclass_G15_16
        url = f"{http_service}/events/{event_id}/raceclasses"
        async with session.post(url, headers=headers, json=request_body) as response:
            assert response.status == 201
        url = f'{http_service}/events/{event_id}/raceclasses/{raceclass_G15["id"]}'
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204
        url = f'{http_service}/events/{event_id}/raceclasses/{raceclass_G16["id"]}'
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204

        # We get the updated list of raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()

        # Also we need to set order for the remaining raceclasses:
        for raceclass in raceclasses:
            id = raceclass["id"]
            (
                raceclass["group"],
                raceclass["order"],
                raceclass["ranking"],
            ) = await _decide_group_order_and_ranking(raceclass)
            url = f"{http_service}/events/{event_id}/raceclasses/{id}"
            async with session.put(url, headers=headers, json=raceclass) as response:
                assert response.status == 204

        # We again get the updated list of raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()

        await _print_raceclasses(raceclasses)

        # ACT #

        # Finally assign bibs to all contestants:
        url = f"{http_service}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            if response.status != 201:
                body = await response.json()
            assert response.status == 201, body
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

            await _print_contestants(contestants)
            await _dump_contestants_to_json(contestants)

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

            # Check that raceclasses has correct number of contestants:
            assert len(contestants) == sum(
                raceclass["no_of_contestants"] for raceclass in raceclasses
            )


# ---
async def _get_raceclass_by_ageclass(raceclasses: List[Dict], ageclass: str) -> Dict:
    # Pick out the raceclass where ageclass is in its ageclasses-list:
    for raceclass in raceclasses:
        if ageclass in raceclass["ageclasses"]:
            return raceclass
    return {}


async def _decide_group_order_and_ranking(  # noqa: C901
    raceclass: dict,
) -> Tuple[int, int, bool]:
    if raceclass["name"] == "M19/20":
        return (1, 1, True)
    elif raceclass["name"] == "K19/20":
        return (1, 2, True)
    elif raceclass["name"] == "M18":
        return (2, 1, True)
    elif raceclass["name"] == "K18":
        return (2, 2, True)
    elif raceclass["name"] == "M17":
        return (3, 1, True)
    elif raceclass["name"] == "K17":
        return (3, 2, True)
    elif raceclass["name"] == "G15/16":
        return (4, 1, True)
    elif raceclass["name"] == "J16":
        return (4, 2, True)
    elif raceclass["name"] == "J15":
        return (4, 3, True)
    elif raceclass["name"] == "G14":
        return (5, 1, True)
    elif raceclass["name"] == "J14":
        return (5, 2, True)
    elif raceclass["name"] == "G13":
        return (5, 3, True)
    elif raceclass["name"] == "J13":
        return (5, 4, True)
    elif raceclass["name"] == "G12":
        return (6, 1, True)
    elif raceclass["name"] == "J12":
        return (6, 2, True)
    elif raceclass["name"] == "G11":
        return (6, 3, True)
    elif raceclass["name"] == "J11":
        return (6, 4, True)
    elif raceclass["name"] == "G10":
        return (7, 1, False)
    elif raceclass["name"] == "J10":
        return (7, 2, False)
    elif raceclass["name"] == "G9":
        return (8, 1, False)
    elif raceclass["name"] == "J9":
        return (8, 2, False)
    return (0, 0, True)  # should not reach this point


async def _print_raceclasses(raceclasses: List[Dict]) -> None:  # noqa: E800
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


async def _print_contestants(contestants: List[dict]) -> None:  # noqa: E800
    # print("--- CONTESTANTS ---")
    # print(f"Number of contestants: {len(contestants)}.")
    # print("bib;ageclass")
    # for contestant in contestants:
    #     print(str(contestant["bib"]) + ";" + str(contestant["ageclass"]))
    pass


async def _dump_contestants_to_json(contestants: List[dict]) -> None:
    # with open("tests/files/tmp_startlist.json", "w") as file:
    #     json.dump(contestants, file)
    pass
