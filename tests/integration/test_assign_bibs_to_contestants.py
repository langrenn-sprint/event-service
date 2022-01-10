"""Integration test cases for the contestant route."""
from datetime import date
import os
from typing import Any, List

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
import jwt
import pytest
from pytest_mock import MockFixture


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME")}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.fixture
async def event() -> dict:
    """Create a mock event object."""
    return {"id": "290e70d5-0933-4af0-bb53-1d705ba7eb95", "name": "A test event"}


@pytest.fixture
async def raceclasses() -> List[dict]:
    """Create a mock raceclasses object."""
    return [
        {
            "id": "11111111-11111-1111-1111-11111111111",
            "name": "G12",
            "ageclass_name": "G 12 år",
            "event_id": "ref_to_event",
            "group": 1,
            "order": 1,
        },
        {
            "id": "99999999-99999-9999-9999-99999999999",
            "name": "J12",
            "ageclass_name": "J 12 år",
            "event_id": "ref_to_event",
            "group": 1,
            "order": 2,
        },
    ]


@pytest.fixture
async def raceclasses_without_group() -> List[dict]:
    """Create a mock raceclasses object."""
    return [
        {
            "id": "11111111-11111-1111-1111-11111111111",
            "name": "G12",
            "ageclass_name": "G 12 år",
            "event_id": "ref_to_event",
            "order": 2,
        },
        {
            "id": "99999999-99999-9999-9999-99999999999",
            "name": "J12",
            "ageclass_name": "J 12 år",
            "event_id": "ref_to_event",
            "order": 2,
        },
    ]


@pytest.fixture
async def raceclasses_without_order() -> List[dict]:
    """Create a mock raceclasses object."""
    return [
        {
            "id": "11111111-11111-1111-1111-11111111111",
            "name": "G12",
            "ageclass_name": "G 12 år",
            "event_id": "ref_to_event",
            "group": 1,
        },
        {
            "id": "99999999-99999-9999-9999-99999999999",
            "name": "J12",
            "ageclass_name": "J 12 år",
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
    },
]


@pytest.fixture
async def contestants() -> List[dict]:
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
    raceclasses: List[dict],
    contestants: List[dict],
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

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs", headers=headers
        )
        assert resp.status == 201
        assert f"/events/{event_id}/contestants" in resp.headers[hdrs.LOCATION]


# Bad cases
@pytest.mark.integration
async def test_assign_bibs_to_contestants_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceclasses: List[dict],
    contestants: List[dict],
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
        m.post("http://example.com:8081/authorize", status=204)
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
    raceclasses: List[dict],
    contestants: List[dict],
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
        m.post("http://example.com:8081/authorize", status=204)
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
    raceclasses_without_group: List[dict],
    contestants: List[dict],
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
        m.post("http://example.com:8081/authorize", status=204)
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
    raceclasses_without_order: List[dict],
    contestants: List[dict],
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
        m.post("http://example.com:8081/authorize", status=204)
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
    raceclasses: List[dict],
    contestants: List[dict],
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
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs",
            headers=headers,
        )
        assert resp.status == 401
