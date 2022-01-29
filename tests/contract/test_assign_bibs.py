"""Contract test cases for contestants."""
import asyncio
from datetime import date
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

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


@pytest.fixture(scope="module")
@pytest.mark.asyncio
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
        event_id = response.headers[hdrs.LOCATION].split("/")[-1]
        logging.debug(f"Created event with id {event_id}.")
        return event_id
    else:
        logging.error(f"Got unsuccesful status when creating event: {status}.")
        return None


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def clear_db(
    http_service: Any, token: MockFixture, event_id: str
) -> AsyncGenerator:
    """Clear db before and after tests."""
    await delete_contestants(http_service, token, event_id)
    await delete_raceclasses(http_service, token, event_id)
    yield
    await delete_raceclasses(http_service, token, event_id)
    await delete_contestants(http_service, token, event_id)


async def delete_contestants(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Delete all contestants."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.delete(url, headers=headers) as response:
        assert response.status == 204
    await session.close()


async def delete_raceclasses(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Delete all raceclasses."""
    url = f"{http_service}/events/{event_id}/raceclasses"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url) as response:
        raceclasses = await response.json()
        for raceclass in raceclasses:
            raceclass_id = raceclass["id"]
            async with session.delete(
                f"{url}/{raceclass_id}", headers=headers
            ) as response:
                assert response.status == 204
    await session.close()


@pytest.mark.contract
@pytest.mark.asyncio
async def test_assign_bibs(
    http_service: Any,
    token: MockFixture,
    event_id: str,
    clear_db: None,
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
        files = {"file": open("tests/files/allcontestants_eventid_364892.csv", "rb")}
        async with session.post(url, headers=headers, data=files) as response:
            assert response.status == 200

        # We need to generate raceclasses for the event:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        # We need to work on the raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()

        # We assign ageclasses "G 16 år" and "G 15 år" to the same new raceclass "G15-16":
        raceclass_G16 = await _get_raceclass_by_ageclass(raceclasses, "G 16 år")
        raceclass_G15 = await _get_raceclass_by_ageclass(raceclasses, "G 15 år")
        raceclass_G15_16: Dict = {
            "event_id": event_id,
            "name": "G15-16",
            "ageclasses": raceclass_G15["ageclasses"] + raceclass_G16["ageclasses"],
            "no_of_contestants": raceclass_G15["no_of_contestants"]
            + raceclass_G16["no_of_contestants"],
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
            raceclass["group"], raceclass["order"] = await _decide_group_and_order(
                raceclass
            )
            url = f"{http_service}/events/{event_id}/raceclasses/{id}"
            async with session.put(url, headers=headers, json=raceclass) as response:
                assert response.status == 204

        await _print_raceclasses(raceclasses)

        # ACT #

        # Finally assign bibs to all contestants:
        url = f"{http_service}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
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


async def _decide_group_and_order(raceclass: dict) -> Tuple[int, int]:  # noqa: C901
    if raceclass["name"] == "G15-16":  # race-order: 1
        return (1, 1)
    elif raceclass["name"] == "J16":  # race-order: 2
        return (1, 2)
    elif raceclass["name"] == "J15":  # race-order: 3
        return (1, 3)
    elif raceclass["name"] == "G14":  # race-order: 4
        return (2, 1)
    elif raceclass["name"] == "J14":  # race-order: 5
        return (2, 2)
    elif raceclass["name"] == "G13":  # race-order: 6
        return (2, 3)
    elif raceclass["name"] == "J13":  # race-order: 7
        return (2, 4)
    elif raceclass["name"] == "G12":  # race-order: 8
        return (3, 1)
    elif raceclass["name"] == "J12":  # race-order: 9
        return (3, 2)
    elif raceclass["name"] == "G11":  # race-order: 10
        return (3, 3)
    elif raceclass["name"] == "J11":  # race-order: 11
        return (3, 4)
    return (0, 0)  # should not reach this point


async def _print_raceclasses(raceclasses: List[Dict]) -> None:
    # print("--- RACECLASSES ---")
    # print("group;order;name;ageclasses;no_of_contestants;distance;event_id")
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
    #         + raceclass["event_id"]
    #     )
    pass


async def _print_contestants(contestants: List[dict]) -> None:
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
