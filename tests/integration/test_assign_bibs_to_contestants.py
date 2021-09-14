"""Integration test cases for the contestant route."""
import os

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
import jwt
from multidict import MultiDict
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
async def contestant() -> dict:
    """Create a mock contestant object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": "1970-01-01",
        "gender": "M",
        "ageclass": "G 12 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": "ref_to_event",
    }


@pytest.mark.integration
async def test_assign_bibs_to_contestants(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
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
    contestant: dict,
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/events/does_not_exist/contestants/assign-bibs", headers=headers
        )
        assert resp.status == 404


# Unauthorized cases:


@pytest.mark.integration
async def test_assign_bibs_to_contestants_no_authorization(
    client: _TestClient, mocker: MockFixture, event: dict
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )

    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post(
            f"/events/{event_id}/contestants/assign-bibs",
            headers=headers,
        )
        assert resp.status == 401
