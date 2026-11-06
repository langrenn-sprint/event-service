"""Contract test cases for the role model (event-service-gui#215).

Users with each role are created in user-service and log in, so the tests use
real tokens with the role names user-service hands out. The tests check the
whole role model against the running service, and the raceday scenarios with
real data:
- contestant-admin adds and changes a late entry, but may not delete it.
- result-admin and event-admin publish and delete results for a raceclass.
"""

import os
import re
from collections.abc import AsyncGenerator
from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

import pytest
from httpx import AsyncClient, Response
from pymongo import AsyncMongoClient

from app.utils import db_utils
from tests.role_model import (
    ADMIN,
    CONTESTANT_ADMIN,
    EVENT_ADMIN,
    RESULT_ADMIN,
    ROLES,
    access_cases,
)

DB_NAME = os.getenv("DB_NAME", "events_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _check(response: Response, expected: HTTPStatus, action: str) -> Response:
    assert response.status_code == expected, (
        f"{action}: got {response.status_code}, {response.text[:500]}"
    )
    return response


def _url(http_service: str, response: Response) -> str:
    # Location is an absolute URL with the service's own host name:
    return http_service + urlparse(response.headers["Location"]).path


async def _login(
    client: AsyncClient, users_url: str, username: str, password: str
) -> str:
    response = await client.post(
        f"{users_url}/login", json={"username": username, "password": password}
    )
    return _check(response, HTTPStatus.OK, f"login {username}").json()["token"]


@pytest.fixture(scope="module", autouse=True)
async def clear_db(db_address: dict[str, Any]) -> AsyncGenerator:
    """Clear db before and after tests."""
    mongo = AsyncMongoClient(**db_address, username=DB_USER, password=DB_PASSWORD)
    await db_utils.drop_db_and_recreate_indexes(mongo, DB_NAME)
    yield
    await db_utils.drop_db(mongo, DB_NAME)
    await mongo.close()


@pytest.fixture(scope="module")
async def tokens(http_service: Any, users_url: str, clear_db: Any) -> dict[str, str]:
    """Log in as admin, create a user for each other role, and log in as them."""
    _ = http_service, clear_db  # the service is up, and the db is cleared first
    async with AsyncClient() as client:
        admin_token = await _login(
            client,
            users_url,
            os.environ["ADMIN_USERNAME"],
            os.environ["ADMIN_PASSWORD"],
        )
        tokens = {ADMIN: admin_token}
        for role in ROLES:
            if role == ADMIN:
                continue
            username = f"{role}@example.com"
            response = await client.post(
                f"{users_url}/users",
                headers=_auth(admin_token),
                json={"username": username, "password": "secret", "role": role},
            )
            _check(response, HTTPStatus.CREATED, f"create user with role {role}")
            tokens[role] = await _login(client, users_url, username, "secret")
    return tokens


@pytest.fixture(scope="module")
async def event_url(http_service: str, tokens: dict[str, str]) -> str:
    """Create an event, as event-admin, and return its URL."""
    event = {
        "name": "Rollerennet",
        "date_of_event": "2026-12-05",
        "time_of_event": "10:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Renn for å teste rollene.",
    }
    async with AsyncClient() as client:
        response = await client.post(
            f"{http_service}/events", headers=_auth(tokens[EVENT_ADMIN]), json=event
        )
    return _url(http_service, _check(response, HTTPStatus.CREATED, "create event"))


# --- The role model, with real tokens -------------------------------------------


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
@pytest.mark.parametrize(("method", "path", "role", "allowed"), access_cases(ROLES))
async def test_write_access(
    http_service: str,
    tokens: dict[str, str],
    method: str,
    path: str,
    role: str,
    *,
    allowed: bool,
) -> None:
    """Allowed roles pass the role check, the others get 403.

    The role check runs before validation, so with an invalid id and an empty
    body an allowed role gets 422 and nothing is changed.
    """
    url = http_service + re.sub(r"\{\w+\}", "not-a-uuid", path)
    async with AsyncClient() as client:
        response = await client.request(
            method,
            url,
            headers=_auth(tokens[role]),
            json=None if method == "DELETE" else {},
        )
    expected = HTTPStatus.UNPROCESSABLE_ENTITY if allowed else HTTPStatus.FORBIDDEN
    _check(response, expected, f"{method} {path} as {role}")


# --- Raceday scenarios ----------------------------------------------------------


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_contestant_admin_late_entry(
    http_service: str, tokens: dict[str, str], event_url: str
) -> None:
    """contestant-admin adds and changes a late entry, but may not delete it."""
    token = tokens[CONTESTANT_ADMIN]
    contestant = {
        "event_id": event_url.rsplit("/", maxsplit=1)[-1],
        "first_name": "Sen",
        "last_name": "Løper",
        "ageclass": "G 12 år",
        "club": "Alltid sent ute IL",
        "registration_date_time": "2026-12-05T09:30:00",
    }
    async with AsyncClient() as client:
        response = await client.post(
            f"{event_url}/contestants", headers=_auth(token), json=contestant
        )
        url = _url(http_service, _check(response, HTTPStatus.CREATED, "add late entry"))

        contestant = _check(await client.get(url), HTTPStatus.OK, "get").json()
        contestant["club"] = "Litt mindre sent ute IL"
        response = await client.put(url, headers=_auth(token), json=contestant)
        _check(response, HTTPStatus.NO_CONTENT, "update late entry")

        response = await client.delete(url, headers=_auth(token))
        _check(response, HTTPStatus.FORBIDDEN, "delete as contestant-admin")
        response = await client.delete(f"{event_url}/contestants", headers=_auth(token))
        _check(response, HTTPStatus.FORBIDDEN, "delete all as contestant-admin")

        contestant = _check(await client.get(url), HTTPStatus.OK, "get").json()
        assert contestant["club"] == "Litt mindre sent ute IL"


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
@pytest.mark.parametrize(
    ("role", "raceclass_name"), [(RESULT_ADMIN, "G12"), (EVENT_ADMIN, "J12")]
)
async def test_publish_results(
    http_service: str,
    tokens: dict[str, str],
    event_url: str,
    role: str,
    raceclass_name: str,
) -> None:
    """result-admin and event-admin publish and delete results.

    contestant-admin may do neither.
    """
    result = {
        "event_id": event_url.rsplit("/", maxsplit=1)[-1],
        "raceclass_name": raceclass_name,
        "timing_point": "Finish",
        "no_of_contestants": 2,
        "ranking_sequence": [{"rank": 1, "bib": 19}, {"rank": 2, "bib": 23}],
        "status": 1,
    }
    url = f"{event_url}/results/{raceclass_name}"
    async with AsyncClient() as client:
        response = await client.post(
            f"{event_url}/results", headers=_auth(tokens[CONTESTANT_ADMIN]), json=result
        )
        _check(response, HTTPStatus.FORBIDDEN, "publish as contestant-admin")

        response = await client.post(
            f"{event_url}/results", headers=_auth(tokens[role]), json=result
        )
        _check(response, HTTPStatus.CREATED, f"publish as {role}")
        _check(await client.get(url), HTTPStatus.OK, "get published result")

        response = await client.delete(url, headers=_auth(tokens[CONTESTANT_ADMIN]))
        _check(response, HTTPStatus.FORBIDDEN, "delete as contestant-admin")
        response = await client.delete(url, headers=_auth(tokens[role]))
        _check(response, HTTPStatus.NO_CONTENT, f"delete as {role}")
