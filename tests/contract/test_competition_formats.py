"""Contract test cases for competition-formats."""
import asyncio
from copy import deepcopy
import logging
import os
from typing import Any, AsyncGenerator
from urllib.parse import quote

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
async def clear_db(http_service: Any, token: MockFixture) -> AsyncGenerator:
    """Clear DB before and after tests."""
    await delete_competition_formats(http_service, token)
    yield
    await delete_competition_formats(http_service, token)


async def delete_competition_formats(http_service: Any, token: MockFixture) -> None:
    """Delete all Competition_formats before we start."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        competition_formats = await response.json()
        for competition_format in competition_formats:
            competition_format_id = competition_format["id"]
            async with session.delete(
                f"{url}/{competition_format_id}", headers=headers
            ) as response:
                pass
    await session.close()


@pytest.fixture(scope="module")
async def competition_format_interval_start() -> dict:
    """An competition_format object for testing."""
    return {
        "name": "Interval Start",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "intervals": "00:00:30",
        "datatype": "interval_start",
    }


@pytest.fixture(scope="module")
async def competition_format_individual_sprint() -> dict:
    """An competition_format object for testing."""
    return {
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_rounds": "00:05:00",
        "time_between_heats": "00:02:30",
        "max_no_of_contestants": 80,
        "datatype": "individual_sprint",
    }


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


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_competition_format_interval_start(
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
    competition_format_interval_start: dict,
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = competition_format_interval_start

    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert "/competition-formats/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_competition_format_individual_sprint(
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
    competition_format_individual_sprint: dict,
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = competition_format_individual_sprint

    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert "/competition-formats/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_competition_formats(
    http_service: Any, token: MockFixture
) -> None:
    """Should return OK and a list of competition_formats as json."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        competition_formats = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(competition_formats) is list
    assert len(competition_formats) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_competition_format_by_id(
    http_service: Any, token: MockFixture, competition_format_individual_sprint: dict
) -> None:
    """Should return OK and an competition_format as json."""
    url = f"{http_service}/competition-formats"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        query_param = f'name={quote(competition_format_individual_sprint["name"])}'
        async with session.get(f"{url}?{query_param}", headers=headers) as response:
            competition_formats = await response.json()
        id = competition_formats[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url, headers=headers) as response:
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(competition_format_individual_sprint) is dict
    assert body["id"] == id
    assert body["name"] == competition_format_individual_sprint["name"]
    assert (
        body["starting_order"] == competition_format_individual_sprint["starting_order"]
    )
    assert (
        body["start_procedure"]
        == competition_format_individual_sprint["start_procedure"]
    )
    assert (
        body["time_between_rounds"]
        == competition_format_individual_sprint["time_between_rounds"]
    )
    assert (
        body["time_between_heats"]
        == competition_format_individual_sprint["time_between_heats"]
    )
    assert (
        body["max_no_of_contestants"]
        == competition_format_individual_sprint["max_no_of_contestants"]
    )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_competition_format_by_name(
    http_service: Any, token: MockFixture, competition_format_interval_start: dict
) -> None:
    """Should return OK and an competition_format as json."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        query_param = f'name={quote(competition_format_interval_start["name"])}'
        async with session.get(f"{url}?{query_param}", headers=headers) as response:
            assert str(response.url) == f"{url}?name=Interval%20Start"
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["id"]
    assert body[0]["name"] == competition_format_interval_start["name"]
    assert (
        body[0]["starting_order"] == competition_format_interval_start["starting_order"]
    )
    assert (
        body[0]["start_procedure"]
        == competition_format_interval_start["start_procedure"]
    )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_competition_format_interval_start(
    http_service: Any, token: MockFixture, competition_format_interval_start: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            competition_formats = await response.json()
        id = competition_formats[0]["id"]
        url = f"{url}/{id}"

        request_body = deepcopy(competition_format_interval_start)
        new_name = "Interval Start updated"
        request_body["id"] = id
        request_body["name"] = new_name

        async with session.put(url, headers=headers, json=request_body) as response:
            assert response.status == 204

        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            updated_competition_format = await response.json()
            assert updated_competition_format["name"] == new_name


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_competition_format_individual_sprint(
    http_service: Any, token: MockFixture, competition_format_individual_sprint: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            competition_formats = await response.json()
        id = competition_formats[0]["id"]
        url = f"{url}/{id}"

        request_body = deepcopy(competition_format_individual_sprint)
        new_name = "Interval Start updated"
        request_body["id"] = id
        request_body["name"] = new_name

        async with session.put(url, headers=headers, json=request_body) as response:
            assert response.status == 204

        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            updated_competition_format = await response.json()
            assert updated_competition_format["name"] == new_name


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_competition_format(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/competition-formats"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            competition_formats = await response.json()
        id = competition_formats[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204

        async with session.get(url, headers=headers) as response:
            assert response.status == 404
