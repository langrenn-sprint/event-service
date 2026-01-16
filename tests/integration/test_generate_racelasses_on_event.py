"""Integration test cases for the events route."""

import os
from datetime import date

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
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
async def event() -> dict:
    """Create a mock event object."""
    return {"id": "290e70d5-0933-4af0-bb53-1d705ba7eb95", "name": "A test event"}


@pytest.fixture
async def contestant() -> dict:
    """Create a mock contestant object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "ageclass": "G 16 år",
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": date(1970, 1, 1).isoformat(),
        "gender": "M",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": "ref_to_event",
        "registration_date_time": "2021-08-31T12:00:00",
    }


@pytest.fixture
async def raceclass() -> dict:
    """Create a mock raceclass object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "G 16 år",
        "ageclasses": ["G 16 år"],
        "gender": "M",
        "event_id": "ref_to_event",
        "group": 1,
        "order": 1,
        "ranking": True,
        "seeding": False,
        "distance": "5km",
    }


@pytest.mark.integration
async def test_generate_raceclasses_on_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    raceclass: dict,
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass["id"],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-raceclasses", headers=headers
        )
        assert resp.status == 201
        assert f"/events/{event_id}/raceclasses" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_generate_raceclasses_on_event_raceclass_exist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    raceclass: dict,
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=raceclass,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-raceclasses", headers=headers
        )
        assert resp.status == 201
        assert f"/events/{event_id}/raceclasses" in resp.headers[hdrs.LOCATION]


# Bad cases:
@pytest.mark.integration
async def test_generate_raceclasses_on_event_duplicate_raceclasses(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    raceclass: dict,
) -> None:
    """Should return 422 Unprocessable entity."""
    raceclass_id = raceclass["id"]
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass, raceclass],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-raceclasses", headers=headers
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_generate_raceclasses_on_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    raceclass: dict,
) -> None:
    """Should return 404 Not found."""
    raceclass_id = raceclass["id"]
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass, raceclass],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-raceclasses", headers=headers
        )
        assert resp.status == 404


# Not authenticated
@pytest.mark.integration
async def test_generate_raceclasses_on_event_unauthorized(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    raceclass: dict,
) -> None:
    """Should return 401 Unauthorized."""
    AGECLASS_ID = "raceclass_id_1"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=AGECLASS_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)
        resp = await client.post(
            f"/events/{event_id}/generate-raceclasses", headers=headers
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_generate_raceclasses_on_event_create_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    raceclass: dict,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
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
            f"/events/{event_id}/generate-raceclasses", headers=headers
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_generate_raceclasses_on_event_update_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    raceclass: dict,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
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
            f"/events/{event_id}/generate-raceclasses", headers=headers
        )
        assert resp.status == 400
