"""Integration test cases for the events route."""

import os
import uuid
from copy import deepcopy
from http import HTTPStatus

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app import api
from app.adapters import CompetitionFormatsAdapterError
from app.models import Event


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
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {
        "username": "any_user",
        "exp": 9999999999,
        "role": "user",
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
async def competition_format() -> dict[str, int | str]:
    """An competition_format object for testing."""
    return {
        "name": "Interval Start",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "timezone": "Europe/Oslo",
        "intervals": "00:00:30",
        "max_no_of_contestants_in_raceclass": 9999,
        "max_no_of_contestants_in_race": 9999,
        "datatype": "interval_start",
    }


@pytest.mark.integration
async def test_create_event(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    competition_format: dict,
) -> None:
    """Should return Created, location header."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event", return_value=event.id
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format],
    )

    request_body = event.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 201
    assert f"/events/{event.id}" in resp.headers["Location"]


@pytest.mark.integration
async def test_create_event_with_input_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    competition_format: dict,
) -> None:
    """Should return Created, location header."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event",
        return_value=event.id,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={},
    )

    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format],
    )

    request_body = event.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 201
    assert f"/events/{event.id}" in resp.headers["Location"]


@pytest.mark.integration
async def test_get_event_by_id(
    client: TestClient, mocker: MockFixture, event: Event
) -> None:
    """Should return OK, and a body containing one event."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    resp = client.get(f"/events/{event.id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(event.id)
    assert body["name"] == event.name
    assert body["competition_format"] == event.competition_format
    assert body["timezone"] == event.timezone
    assert body["date_of_event"] == event.date_of_event.isoformat()
    assert body["time_of_event"] == event.time_of_event.isoformat()  # type: ignore[attr-defined]
    assert body["organiser"] == event.organiser
    assert body["webpage"] == str(event.webpage)
    assert body["information"] == event.information


@pytest.mark.integration
async def test_update_event_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    competition_format: dict,
) -> None:
    """Should return No Content."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.update_event",
        return_value=event.id,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    new_name = "Oslo Skagen sprint Oppdatert"
    updated_event = deepcopy(event)
    updated_event.name = new_name
    request_body = updated_event.model_dump(mode="json")

    resp = client.put(f"/events/{event.id}", headers=headers, json=request_body)
    assert resp.status_code == 204


@pytest.mark.integration
async def test_get_all_events(
    client: TestClient, mocker: MockFixture, event: Event
) -> None:
    """Should return OK and a valid json body."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_all_events",
        return_value=[event],
    )

    resp = client.get("/events")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    events = resp.json()
    assert type(events) is list
    assert len(events) > 0
    assert events[0]["id"] == str(event.id)


@pytest.mark.integration
async def test_delete_event_by_id(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return No Content."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=event.id,
    )
    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.delete(f"/events/{event.id}", headers=headers)
    assert resp.status_code == 204


# Bad cases


# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_event_missing_mandatory_property(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event", return_value=event.id
    )
    request_body = {"optional_property": "Optional_property"}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_event_competition_formats_adapter_raises_exception(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
) -> None:
    """Should return Created, location header."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event",
        return_value=event.id,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        side_effect=CompetitionFormatsAdapterError(
            "Got unknown status 500 from competition_formats service."
        ),
    )

    request_body = event.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 400


@pytest.mark.integration
async def test_create_event_with_input_duplicate_id(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format],
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event",
        return_value=event.id,
    )
    request_body = event.model_dump(mode="json")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_event_adapter_fails(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format],
    )

    request_body = event.model_dump(mode="json")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 500


@pytest.mark.integration
async def test_create_event_invalid_timezone(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    competition_format: dict,
) -> None:
    """Should return 422 Unprocessable entity."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event",
        return_value=event.id,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format],
    )

    event_invalid_timezone = deepcopy(event)
    event_invalid_timezone.timezone = "Europe/Invalid"
    request_body = event_invalid_timezone.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 422


@pytest.mark.integration
async def test_update_event_by_id_missing_mandatory_property(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.update_event",
        return_value=event.id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = event.model_dump(mode="json", exclude={"name"})

    resp = client.put(f"/events/{event.id}", headers=headers, json=request_body)
    assert resp.status_code == 422


@pytest.mark.integration
async def test_update_event_by_id_different_id_in_body(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.update_event",
        return_value=event.id,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    event_with_different_id = deepcopy(event)
    event_with_different_id.id = uuid.uuid4()
    request_body = event_with_different_id.model_dump(mode="json")

    resp = client.put(f"/events/{event.id}", headers=headers, json=request_body)
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_event_multiple_competition_formats(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    competition_format: dict,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event",
        return_value=event.id,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format, competition_format],
    )

    request_body = event.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 400


@pytest.mark.integration
async def test_create_event_invalid_competition_format(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event", return_value=event.id
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[],
    )

    event_invalid_competition_format = deepcopy(event)
    event_invalid_competition_format.competition_format = "Invalid Competition Format"
    request_body = event_invalid_competition_format.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 400


@pytest.mark.integration
async def test_update_event_invalid_competition_format(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.update_event",
        return_value=event.id,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    event_with_invalid_competition_format = deepcopy(event)
    event_with_invalid_competition_format.competition_format = (
        "Invalid Competition Format"
    )
    request_body = event_with_invalid_competition_format.model_dump(mode="json")

    resp = client.put(f"/events/{event.id}", headers=headers, json=request_body)
    assert resp.status_code == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_create_event_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event",
        return_value=event.id,
    )

    request_body = {"name": "Oslo Skagen sprint"}
    headers = {"Content-Type": "application/json"}

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 401


@pytest.mark.integration
async def test_update_event_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event, competition_format: dict
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.update_event",
        return_value=event.id,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format],
    )

    headers = {
        "Content-Type": "application/json",
    }

    request_body = event.model_dump(mode="json")

    resp = client.put(f"/events/{event.id}", headers=headers, json=request_body)
    assert resp.status_code == 401


@pytest.mark.integration
async def test_delete_event_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=event.id,
    )
    resp = client.delete(f"/events/{event.id}")
    assert resp.status_code == 401


# Forbidden:
@pytest.mark.integration
async def test_create_event_insufficient_role(
    client: TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    event: Event,
) -> None:
    """Should return 403 Forbidden."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.create_event",
        return_value=event.id,
    )
    request_body = {"name": "Oslo Skagen sprint"}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token_unsufficient_role}",
    }

    resp = client.post("/events", headers=headers, json=request_body)
    assert resp.status_code == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_event_not_found(client: TestClient, mocker: MockFixture) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )

    resp = client.get(f"/events/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.integration
async def test_update_event_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.update_event",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",
        return_value=[competition_format],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = Event.model_validate(
        {
            "id": uuid.uuid4(),
            "name": "Oslo Skagen sprint",
            "competition_format": "Individual sprint",
            "date_of_event": "2021-08-31",
            "time_of_event": "09:00:00",
            "timezone": "Europe/Oslo",
            "organiser": "Lyn Ski",
        }
    ).model_dump(mode="json")

    resp = client.put(f"/events/{uuid.uuid4()}", headers=headers, json=request_body)
    assert resp.status_code == 404


@pytest.mark.integration
async def test_delete_event_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=None,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }
    resp = client.delete(f"/events/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404
