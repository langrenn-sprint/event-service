"""Integration test cases for the contestant route."""

import os
from datetime import date
from typing import Any

import jwt
import pytest
from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
from dotenv import load_dotenv
from pytest_mock import MockFixture

load_dotenv()

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME")}
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
async def event() -> dict:
    """Create a mock event object."""
    return {"id": "290e70d5-0933-4af0-bb53-1d705ba7eb95", "name": "A test event"}


@pytest.fixture
async def raceclasses() -> list[dict]:
    """Create a mock raceclasses object."""
    return [
        {
            "id": "11111111-11111-1111-1111-11111111111",
            "name": "G12",
            "ageclasses": ["G 12 år"],
            "event_id": "ref_to_event",
            "group": 1,
            "order": 1,
        },
        {
            "id": "99999999-99999-9999-9999-99999999999",
            "name": "J12",
            "ageclasses": ["J 12 år"],
            "event_id": "ref_to_event",
            "group": 1,
            "order": 2,
        },
    ]


@pytest.fixture
async def raceclasses_without_group() -> list[dict]:
    """Create a mock raceclasses object."""
    return [
        {
            "id": "11111111-11111-1111-1111-11111111111",
            "name": "G12",
            "ageclasses": ["G 12 år"],
            "event_id": "ref_to_event",
            "order": 2,
        },
        {
            "id": "99999999-99999-9999-9999-99999999999",
            "name": "J12",
            "ageclasses": ["J 12 år"],
            "event_id": "ref_to_event",
            "order": 2,
        },
    ]


@pytest.fixture
async def raceclasses_without_order() -> list[dict]:
    """Create a mock raceclasses object."""
    return [
        {
            "id": "11111111-11111-1111-1111-11111111111",
            "name": "G12",
            "ageclasses": ["G 12 år"],
            "event_id": "ref_to_event",
            "group": 1,
        },
        {
            "id": "99999999-99999-9999-9999-99999999999",
            "name": "J12",
            "ageclasses": ["J 12 år"],
            "event_id": "ref_to_event",
            "group": 1,
        },
    ]


CONTESTANT_LIST = [
    {
        "id": "11111111-11111-1111-1111-11111111111",
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": date(1970, 1, 1).isoformat(),
        "gender": "M",
        "ageclass": "G 12 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": "ref_to_event",
        "registration_date_time": "2021-08-31T12:00:00",
    },
    {
        "id": "99999999-99999-9999-9999-99999999999",
        "first_name": "Another Conte.",
        "last_name": "Stant",
        "birth_date": date(1980, 1, 1).isoformat(),
        "gender": "F",
        "ageclass": "J 12 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": "ref_to_event",
        "registration_date_time": "2021-08-31T12:00:00",
    },
]


@pytest.fixture
async def contestants() -> list[dict]:
    """Create a mock contestant object."""
    return CONTESTANT_LIST


def get_contestant_by_id(arg1: Any, event_id: str, contestant_id: str) -> dict:
    """Look up correct contestant in list."""
    return next(item for item in CONTESTANT_LIST if item["id"] == contestant_id)


def update_contestant(
    arg1: Any, event_id: str, contestant_id: str, contestant: dict
) -> dict:
    """Return the update contestant."""
    return contestant


@pytest.mark.integration
async def test_assign_bibs_to_contestants(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    raceclasses: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs", headers=headers
        )
        assert resp.status == 201
        assert f"/events/{event_id}/contestants" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_assign_bibs_to_contestants_start_bib_100(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    raceclasses: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs?start-bib=100", headers=headers
        )
        assert resp.status == 201
        assert f"/events/{event_id}/contestants" in resp.headers[hdrs.LOCATION]


# Bad cases
@pytest.mark.integration
async def test_assign_bibs_to_contestants_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceclasses: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            "/events/does_not_exist/contestants/assign-bibs", headers=headers
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_assign_bibs_to_contestants_no_raceclasses(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    raceclasses: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=list(),
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs", headers=headers
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_assign_bibs_to_contestants_raceclasses_without_group(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    raceclasses_without_group: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses_without_group,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs", headers=headers
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_assign_bibs_to_contestants_raceclasses_without_order(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    raceclasses_without_order: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses_without_order,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs", headers=headers
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_assign_bibs_to_contestants_unknow_ageclass(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    raceclasses: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    # Set unkown value for ageclass:
    contestants[0]["ageclass"] = "Unknown ageclass"

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs", headers=headers
        )
        assert resp.status == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_assign_bibs_to_contestants_no_authorization(
    client: _TestClient,
    mocker: MockFixture,
    event: dict,
    raceclasses: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs",
            headers=headers,
        )
        assert resp.status == 401
