"""Contract test cases for contestants."""

import copy
from datetime import date
import logging
import os
from typing import Any, AsyncGenerator, Optional, Tuple
from urllib.parse import quote


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
    mongo = motor.motor_asyncio.AsyncIOMotorClient(  # type: ignore
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
        "date_of_event": "2021-08-31",
        "time_of_event": "09:00:00",
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


@pytest.fixture(scope="module")
async def contestant(event_id: str) -> dict:
    """Create a contestant object for testing."""
    return {
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": date(1970, 1, 1).isoformat(),
        "gender": "M",
        "ageclass": "G 12 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": event_id,
        "registration_date_time": "2021-11-08T22:06:30",
    }


@pytest.mark.contract
async def test_create_single_contestant(
    http_service: Any,
    token: MockFixture,
    event_id: str,
    contestant: dict,
) -> None:
    """Should return 201 Created, location header and no body."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = contestant
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert f"/events/{event_id}/contestants/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
async def test_get_contestant_by_id(
    http_service: Any, token: MockFixture, event_id: str, contestant: dict
) -> None:
    """Should return OK and an contestant as json."""
    url = f"{http_service}/events/{event_id}/contestants"

    async with ClientSession() as session:
        async with session.get(url) as response:
            contestants = await response.json()
        assert len(contestants) > 0
        assert type(contestants) is list
        id = contestants[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url) as response:
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(body) is dict
    assert body["id"]
    assert body["first_name"] == contestant["first_name"]
    assert body["last_name"] == contestant["last_name"]
    assert body["birth_date"] == contestant["birth_date"]
    assert body["gender"] == contestant["gender"]
    assert body["ageclass"] == contestant["ageclass"]
    assert body["region"] == contestant["region"]
    assert body["club"] == contestant["club"]
    assert body["team"] == contestant["team"]
    assert body["email"] == contestant["email"]
    assert body["registration_date_time"] == contestant["registration_date_time"]
    assert body["event_id"] == event_id


@pytest.mark.contract
async def test_update_contestant(
    http_service: Any, token: MockFixture, event_id: str, contestant: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            contestants = await response.json()
        assert len(contestants) > 0
        assert type(contestants) is list
        id = contestants[0]["id"]
        url = f"{url}/{id}"
        request_body = copy.deepcopy(contestant)
        request_body["id"] = id
        request_body["last_name"] = "Updated name"
        async with session.put(url, headers=headers, json=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
async def test_delete_contestant(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            contestants = await response.json()
        assert len(contestants) > 0
        assert type(contestants) is list
        id = contestants[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
async def test_create_many_contestants_as_csv_file(
    http_service: Any,
    token: MockFixture,
    event_id: str,
) -> None:
    """Should return 200 OK and a report."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    # Send csv-file in request:
    files = {"file": open("tests/files/contestants_Sportsadmin.csv", "rb")}
    async with ClientSession() as session:
        async with session.delete(url) as response:
            pass
        async with session.post(url, headers=headers, data=files) as response:
            status = response.status
            body = await response.json()

    assert status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]

    assert len(body) > 0

    assert body["total"] == 670
    assert body["created"] == 670
    assert len(body["updated"]) == 0
    assert len(body["failures"]) == 0
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.contract
async def test_update_many_existing_contestants_as_csv_file(
    http_service: Any,
    token: MockFixture,
    event_id: str,
) -> None:
    """Should return 200 OK and a report."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    # Send csv-file in request:
    files = {"file": open("tests/files/contestants_G11_Sportsadmin.csv", "rb")}
    async with ClientSession() as session:
        async with session.post(url, headers=headers, data=files) as response:
            status = response.status
            body = await response.json()

    assert status == 200, response
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]

    assert len(body) > 0

    assert body["total"] == 3
    assert body["created"] == 0
    assert len(body["updated"]) == 3
    assert len(body["failures"]) == 0
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.contract
async def test_get_all_contestants_in_given_event(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    url = f"{http_service}/events/{event_id}/contestants"

    async with ClientSession() as session:
        async with session.get(url) as response:
            contestants = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(contestants) is list
    assert len(contestants) == 670


@pytest.mark.contract
async def test_get_all_contestants_in_given_event_by_raceclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    async with ClientSession() as session:
        # In this case we have to generate raceclasses first:
        url = f"{http_service}/events/{event_id}/generate-raceclasses"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201

        raceclass_parameter = "J15"
        url = f"{http_service}/events/{event_id}/contestants?raceclass={raceclass_parameter}"

        async with session.get(url) as response:
            contestants = await response.json()

    assert response.status == 200, response
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(contestants) is list
    assert len(contestants) == 28
    for contestant in contestants:
        assert contestant["ageclass"] == "J 15 år"


@pytest.mark.contract
async def test_get_all_contestants_in_given_event_by_ageclass(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list of contestants as json."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    async with ClientSession() as session:
        query_param = f'ageclass={quote("J 15 år")}'
        url = f"{http_service}/events/{event_id}/contestants"
        async with session.get(f"{url}?{query_param}", headers=headers) as response:
            contestants = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(contestants) is list
    assert len(contestants) == 28
    for contestant in contestants:
        assert contestant["ageclass"] == "J 15 år"


@pytest.mark.contract
async def test_get_all_contestants_in_given_event_by_bib(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return OK and a list with exactly contestant as json."""
    bib = 1

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        # Also we need to set order for all raceclasses:
        url = f"{http_service}/events/{event_id}/raceclasses"
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()
            for raceclass in raceclasses:
                id = raceclass["id"]
                (
                    raceclass["group"],
                    raceclass["order"],
                    raceclass["ranking"],
                ) = await _decide_group_order_and_ranking(raceclass)
                async with session.put(
                    f"{url}/{id}", headers=headers, json=raceclass
                ) as response:
                    assert response.status == 204

        # Finally assign bibs to all contestants:
        url = f"{http_service}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/contestants" in response.headers[hdrs.LOCATION]

        # We can now get the contestants
        url = f"{http_service}/events/{event_id}/contestants"
        async with session.get(url) as response:
            contestants = await response.json()
        assert response.status == 200
        assert len(contestants) > 0
        # We can now get the contestant by bib.
        url = f"{http_service}/events/{event_id}/contestants?bib={bib}"
        async with session.get(url) as response:
            contestants_with_bib = await response.json()

        assert response.status == 200
        assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
        assert type(contestants_with_bib) is list
        assert len(contestants_with_bib) == 1
        assert contestants_with_bib[0]["bib"] == 1


@pytest.mark.contract
async def test_search_contestant_by_name(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/contestants/search"
    body = {"name": "Bjørn"}
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
        hdrs.CONTENT_TYPE: "application/json",
    }

    async with ClientSession() as session:
        async with session.post(url, headers=headers, json=body) as response:
            if response.status != 200:
                body = await response.json()
            assert response.status == 200, body
            contestants = await response.json()

    assert len(contestants) == 3


@pytest.mark.contract
async def test_delete_all_contestant(
    http_service: Any, token: MockFixture, event_id: str
) -> None:
    """Should return 204 No Content."""
    url = f"{http_service}/events/{event_id}/contestants"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204

        async with session.get(url) as response:
            assert response.status == 200
            contestants = await response.json()
            assert len(contestants) == 0


# ---
async def _decide_group_order_and_ranking(  # noqa: C901
    raceclass: dict,
) -> Tuple[int, int, bool]:
    if raceclass["name"] == "MS":
        return (1, 1, True)
    elif raceclass["name"] == "KS":
        return (1, 2, True)
    elif raceclass["name"] == "M19/20":
        return (1, 3, True)
    elif raceclass["name"] == "K19/20":
        return (1, 4, True)
    elif raceclass["name"] == "M18":
        return (2, 1, True)
    elif raceclass["name"] == "K18":
        return (2, 2, True)
    elif raceclass["name"] == "M17":
        return (3, 1, True)
    elif raceclass["name"] == "K17":
        return (3, 2, True)
    elif raceclass["name"] == "G16":
        return (4, 1, True)
    elif raceclass["name"] == "J16":
        return (4, 2, True)
    elif raceclass["name"] == "G15":
        return (4, 3, True)
    elif raceclass["name"] == "J15":
        return (4, 4, True)
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
