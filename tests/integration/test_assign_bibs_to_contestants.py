"""Integration test cases for the contestant route."""

import os
from datetime import date
from uuid import UUID, uuid4

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
    """Create a mock event object."""
    return Event.model_validate(
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "A test event",
            "date_of_event": "2024-06-01",
            "time_of_event": "12:00:00",
        }
    )


@pytest.fixture
async def raceclasses(event: Event) -> list[Raceclass]:
    """Create a mock raceclasses object."""
    return [
        Raceclass.model_validate(
            {
                "id": "10000000-0000-4000-8000-000000000000",
                "name": "G12",
                "ageclasses": ["G 12 år"],
                "gender": "M",
                "event_id": event.id,
                "group": 1,
                "order": 1,
            }
        ),
        Raceclass.model_validate(
            {
                "id": "20000000-0000-4000-8000-000000000000",
                "name": "J12",
                "ageclasses": ["J 12 år"],
                "gender": "K",
                "event_id": event.id,
                "group": 1,
                "order": 2,
            }
        ),
    ]


@pytest.fixture
async def raceclasses_without_group(event: Event) -> list[Raceclass]:
    """Create a mock raceclasses object."""
    return [
        Raceclass.model_validate(
            {
                "id": "10000000-0000-4000-8000-000000000000",
                "name": "G12",
                "ageclasses": ["G 12 år"],
                "gender": "M",
                "event_id": event.id,
                "order": 2,
            }
        ),
        Raceclass.model_validate(
            {
                "id": "20000000-0000-4000-8000-000000000000",
                "name": "J12",
                "ageclasses": ["J 12 år"],
                "gender": "K",
                "event_id": event.id,
                "order": 2,
            }
        ),
    ]


@pytest.fixture
async def raceclasses_without_order(event: Event) -> list[Raceclass]:
    """Create a mock raceclasses object."""
    return [
        Raceclass.model_validate(
            {
                "id": "10000000-0000-4000-8000-000000000000",
                "name": "G12",
                "ageclasses": ["G 12 år"],
                "gender": "M",
                "event_id": event.id,
                "group": 1,
            }
        ),
        Raceclass.model_validate(
            {
                "id": "20000000-0000-4000-8000-000000000000",
                "name": "J12",
                "ageclasses": ["J 12 år"],
                "gender": "K",
                "event_id": event.id,
                "group": 1,
            }
        ),
    ]


CONTESTANT_LIST = [
    {
        "id": "11111111-1111-4111-8111-111111111111",
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": date(1970, 1, 1).isoformat(),
        "gender": "M",
        "ageclass": "G 12 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "registration_date_time": "2021-08-31T12:00:00",
    },
    {
        "id": "22222222-2222-4222-8222-222222222222",
        "first_name": "Another Conte.",
        "last_name": "Stant",
        "birth_date": date(1980, 1, 1).isoformat(),
        "gender": "K",
        "ageclass": "J 12 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "registration_date_time": "2021-08-31T12:00:00",
    },
]


@pytest.fixture
async def contestants() -> list[Contestant]:
    """Create a mock contestant object."""
    return [Contestant.model_validate(contestant) for contestant in CONTESTANT_LIST]


def get_contestant_by_id(event_id: UUID, contestant_id: UUID) -> Contestant:
    """Look up correct contestant in list."""
    return next(
        Contestant.model_validate(contestant)
        for contestant in CONTESTANT_LIST
        if contestant["id"] == str(contestant_id)
    )


def get_contestant_by_ageclasses(
    event_id: UUID, ageclasses: list[str]
) -> list[Contestant]:
    """Look up correct contestant in list."""
    return [
        Contestant.model_validate(contestant)
        for contestant in CONTESTANT_LIST
        if contestant["ageclass"] in ageclasses
    ]


def update_contestant(
    event_id: UUID, contestant_id: UUID, contestant: Contestant
) -> str:
    """Return the update contestant."""
    return str(contestant_id)


@pytest.mark.integration
async def test_assign_bibs_to_contestants(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclasses: list[Raceclass],
    contestants: list[Contestant],
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        side_effect=get_contestant_by_ageclasses,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    event_id = event.id
    resp = client.post(f"/events/{event_id}/contestants/assign-bibs", headers=headers)
    assert resp.status_code == 201
    assert f"/events/{event_id}/contestants" in resp.headers["Location"]


@pytest.mark.integration
async def test_assign_bibs_to_contestants_when_event_has_no_date_time(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceclasses: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 201 Created, location header."""
    event_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        side_effect=get_contestant_by_ageclasses,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={
            "id": event_id,
            "name": "A test event",
        },
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event_id}/contestants/assign-bibs", headers=headers)
    assert resp.status_code == 201
    assert f"/events/{event_id}/contestants" in resp.headers["Location"]


@pytest.mark.integration
async def test_assign_bibs_to_contestants_start_bib_100(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclasses: list[dict],
    contestants: list[dict],
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        side_effect=get_contestant_by_ageclasses,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    event_id = event.id
    resp = client.post(
        f"/events/{event_id}/contestants/assign-bibs?start-bib=100", headers=headers
    )
    assert resp.status_code == 201
    assert f"/events/{event_id}/contestants" in resp.headers["Location"]


# Bad cases
@pytest.mark.integration
async def test_assign_bibs_to_contestants_event_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceclasses: list[Raceclass],
    contestants: list[Contestant],
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        side_effect=get_contestant_by_ageclasses,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{uuid4()}/contestants/assign-bibs", headers=headers)
    assert resp.status_code == 404


@pytest.mark.integration
async def test_assign_bibs_to_contestants_no_raceclasses(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestants: list[Contestant],
) -> None:
    """Should return 404 Not found."""
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
        return_value=contestants,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/contestants/assign-bibs", headers=headers)
    assert resp.status_code == 404


@pytest.mark.integration
async def test_assign_bibs_to_contestants_raceclasses_without_group(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclasses_without_group: list[Raceclass],
    contestants: list[Contestant],
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        side_effect=get_contestant_by_ageclasses,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses_without_group,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/contestants/assign-bibs", headers=headers)
    assert resp.status_code == 400


@pytest.mark.integration
async def test_assign_bibs_to_contestants_raceclasses_without_order(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclasses_without_order: list[Raceclass],
    contestants: list[Contestant],
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        side_effect=get_contestant_by_ageclasses,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses_without_order,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/contestants/assign-bibs", headers=headers)
    assert resp.status_code == 400


@pytest.mark.integration
async def test_assign_bibs_to_contestants_unknow_ageclass(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclasses: list[Raceclass],
    contestants: list[Contestant],
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        side_effect=get_contestant_by_ageclasses,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        side_effect=get_contestant_by_id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        side_effect=update_contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    # Set unkown value for ageclass:
    contestants[0].ageclass = "Unknown ageclass"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(f"/events/{event.id}/contestants/assign-bibs", headers=headers)
    assert resp.status_code == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_assign_bibs_to_contestants_no_authorization(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    raceclasses: list[Raceclass],
    contestants: list[Contestant],
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=contestants,
    )

    headers = {"Content-Type": "application/json"}

    resp = client.post(
        f"/events/{event.id}/contestants/assign-bibs",
        headers=headers,
    )
    assert resp.status_code == 401
