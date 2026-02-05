"""Integration test cases for the events route."""

import os
import uuid
from datetime import date
from http import HTTPStatus

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app import api
from app.models import Contestant, Event, Raceclass


@pytest.fixture
def client() -> TestClient:
    """Fixture to create a test client for the FastAPI application."""
    return TestClient(api)


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {
        "username": os.getenv("ADMIN_USERNAME"),
        "exp": 9999999999,
        "role": "admin",
    }
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
async def event() -> Event:
    """An event object for testing."""
    return Event.model_validate(
        {
            "id": str(uuid.uuid4()),
            "name": "Oslo Skagen sprint",
            "competition_format": "Individual sprint",
            "date_of_event": "2021-08-31",
            "time_of_event": "09:00:00",
            "timezone": "Europe/Oslo",
            "organiser": "Lyn Ski",
            "webpage": "https://example.com/",
            "information": "Testarr for å teste den nye løysinga.",
        }
    )


@pytest.fixture
async def contestant(event: Event) -> Contestant:
    """Create a mock contestant object."""
    return Contestant.model_validate(
        {
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
            "event_id": event.id,
            "registration_date_time": "2021-08-31T12:00:00",
        }
    )


@pytest.fixture
async def raceclass(event: Event) -> Raceclass:
    """Create a mock raceclass object."""
    return Raceclass.model_validate(
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G 16 år",
            "ageclasses": ["G 16 år"],
            "gender": "M",
            "event_id": event.id,
            "group": 1,
            "order": 1,
            "ranking": True,
            "seeding": False,
            "distance": "5km",
        }
    )


@pytest.mark.integration
async def test_generate_raceclasses_on_event(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
    raceclass: Raceclass,
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass.id,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        return_value=[contestant],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/generate-raceclasses", headers=headers)
    assert resp.status_code == 201
    assert f"/events/{event.id}/raceclasses" in resp.headers["Location"]


@pytest.mark.integration
async def test_generate_raceclasses_on_event_raceclass_exist(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
    raceclass: Raceclass,
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=raceclass,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/generate-raceclasses", headers=headers)
    assert resp.status_code == 201
    assert f"/events/{event.id}/raceclasses" in resp.headers["Location"]


# Bad cases:
@pytest.mark.integration
async def test_generate_raceclasses_on_event_duplicate_raceclasses(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
    raceclass: Raceclass,
) -> None:
    """Should return 400 Bad Request."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",
        return_value=[raceclass, raceclass],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass.id,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=raceclass,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/generate-raceclasses", headers=headers)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
async def test_generate_raceclasses_on_event_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
    raceclass: Raceclass,
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass, raceclass],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass.id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/generate-raceclasses", headers=headers)
    assert resp.status_code == 404


# Not authenticated
@pytest.mark.integration
async def test_generate_raceclasses_on_event_unauthorized(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    contestant: Contestant,
    raceclass: Raceclass,
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass.id,
    )

    headers = {
        "Content-Type": "application/json",
    }

    resp = client.post(f"/events/{event.id}/generate-raceclasses", headers=headers)
    assert resp.status_code == 401


@pytest.mark.integration
async def test_generate_raceclasses_on_event_create_fails(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/generate-raceclasses", headers=headers)
    assert resp.status_code == 400


@pytest.mark.integration
async def test_generate_raceclasses_on_event_update_fails(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
    raceclass: Raceclass,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/generate-raceclasses", headers=headers)
    assert resp.status_code == 400
