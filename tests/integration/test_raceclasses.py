"""Integration test cases for the raceclasses route."""

import os
import uuid
from copy import deepcopy

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app import api
from app.models import Event, Raceclass


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
async def raceclass(event: Event) -> Raceclass:
    """Create a mock raceclass object."""
    return Raceclass.model_validate(
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "gender": "M",
            "event_id": event.id,
            "group": 1,
            "order": 1,
            "distance": "5km",
        }
    )


@pytest.mark.integration
async def test_create_raceclass(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = raceclass.model_dump(mode="json")

    resp = client.post(
        f"/events/{event.id}/raceclasses", headers=headers, json=request_body
    )
    assert resp.status_code == 201
    assert f"/events/{event.id}/raceclasses/{raceclass.id}" in resp.headers["Location"]


@pytest.mark.integration
async def test_get_raceclass_by_id(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return OK, and a list containing one raceclass."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        return_value=[],
    )

    resp = client.get(f"/events/{event.id}/raceclasses/{raceclass.id}")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(raceclass.id)
    assert body["event_id"] == str(raceclass.event_id)
    assert body["name"] == raceclass.name
    assert body["group"] == raceclass.group
    assert body["order"] == raceclass.order
    assert body["ageclasses"] == raceclass.ageclasses
    assert body["distance"] == raceclass.distance
    assert body["no_of_contestants"] == 0


@pytest.mark.integration
async def test_get_raceclass_by_name(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return 200 OK, and a list containing one raceclass."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_name",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        return_value=[],
    )

    resp = client.get(f"/events/{event.id}/raceclasses?name={raceclass.name}")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert body[0]["id"] == str(raceclass.id)
    assert body[0]["event_id"] == str(raceclass.event_id)
    assert body[0]["name"] == raceclass.name
    assert body[0]["group"] == raceclass.group
    assert body[0]["order"] == raceclass.order
    assert body[0]["ageclasses"] == raceclass.ageclasses
    assert body[0]["distance"] == raceclass.distance


@pytest.mark.integration
async def test_get_raceclass_by_ageclass_name(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return 200 OK, and a body containing one raceclass."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        return_value=[],
    )

    resp = client.get(
        f"/events/{event.id}/raceclasses?ageclass-name={raceclass.ageclasses[0]}"
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert body[0]["id"] == str(raceclass.id)
    assert body[0]["event_id"] == str(raceclass.event_id)
    assert body[0]["name"] == raceclass.name
    assert body[0]["group"] == raceclass.group
    assert body[0]["order"] == raceclass.order
    assert body[0]["ageclasses"] == raceclass.ageclasses
    assert body[0]["distance"] == raceclass.distance


@pytest.mark.integration
async def test_update_raceclass_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return No Content."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=raceclass.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    raceclass_with_updated_distance = deepcopy(raceclass)
    raceclass_with_updated_distance.distance = "New distance"
    request_body = raceclass_with_updated_distance.model_dump(mode="json")

    resp = client.put(
        f"/events/{event.id}/raceclasses/{raceclass.id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == 204


@pytest.mark.integration
async def test_get_all_raceclasses(
    client: TestClient, mocker: MockFixture, event: Event, raceclass: Raceclass
) -> None:
    """Should return OK and a valid json body."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestants_by_ageclasses",
        return_value=[],
    )

    resp = client.get(f"/events/{event.id}/raceclasses")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    raceclasses = resp.json()
    assert type(raceclasses) is list
    assert len(raceclasses) > 0
    assert str(raceclass.id) == raceclasses[0]["id"]


@pytest.mark.integration
async def test_delete_raceclass_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return No Content."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.delete_raceclass",
        return_value=raceclass.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.delete(
        f"/events/{event.id}/raceclasses/{raceclass.id}", headers=headers
    )
    assert resp.status_code == 204


@pytest.mark.integration
async def test_delete_all_raceclasses_in_event(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
) -> None:
    """Should return 204 No content."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.delete_all_raceclasses",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.delete(f"/events/{event.id}/raceclasses", headers=headers)
    assert resp.status_code == 204
    resp = client.get(f"/events/{event.id}/raceclasses")
    assert resp.status_code == 200
    raceclasses = resp.json()
    assert len(raceclasses) == 0


# Bad cases
# Event not found
@pytest.mark.integration
async def test_create_raceclass_event_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )

    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = raceclass.model_dump(mode="json")

    resp = client.post(
        f"/events/{event.id}/raceclasses", headers=headers, json=request_body
    )
    assert resp.status_code == 404


# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_raceclass_missing_mandatory_property(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = {"id": str(raceclass.id), "optional_property": "Optional_property"}

    resp = client.post(
        f"/events/{event.id}/raceclasses", headers=headers, json=request_body
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_update_raceclass_by_id_missing_mandatory_property(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value={"id": raceclass.id, "name": "missing_the_rest_of_the_properties"},
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=raceclass.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = {
        "id": str(raceclass.id),
        "name": "missing_the_rest_of_the_properties",
    }

    resp = client.put(
        f"/events/{event.id}/raceclasses/{raceclass.id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_update_raceclass_by_id_different_id_in_body(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=raceclass.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    raceclass_with_different_id = deepcopy(raceclass)
    raceclass_with_different_id.id = uuid.uuid4()
    request_body = raceclass_with_different_id.model_dump(mode="json")

    resp = client.put(
        f"/events/{event.id}/raceclasses/{raceclass.id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_raceclass_adapter_fails(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = raceclass.model_dump(mode="json")

    resp = client.post(
        f"/events/{event.id}/raceclasses", headers=headers, json=request_body
    )
    assert resp.status_code == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_create_raceclass_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event, raceclass: Raceclass
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=raceclass.id,
    )

    headers = {"Content-Type": "application/json"}
    request_body = raceclass.model_dump(mode="json")

    resp = client.post(
        f"/events/{event.id}/raceclasses", headers=headers, json=request_body
    )
    assert resp.status_code == 401


@pytest.mark.integration
async def test_put_raceclass_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event, raceclass: Raceclass
) -> None:
    """Should return 401 Unauthorizedt."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=raceclass.id,
    )

    headers = {
        "Content-Type": "application/json",
    }

    request_body = raceclass.model_dump(mode="json")

    resp = client.put(
        f"/events/{event.id}/raceclasses/{raceclass.id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == 401


@pytest.mark.integration
async def test_delete_raceclass_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event, raceclass: Raceclass
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.delete_raceclass",
        return_value=raceclass.id,
    )

    resp = client.delete(f"/events/{event.id}/raceclasses/{raceclass.id}")
    assert resp.status_code == 401


@pytest.mark.integration
async def test_delete_all_raceclasses_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.delete_all_raceclasses",
        return_value=None,
    )

    resp = client.delete(f"/events/{event.id}/raceclasses")
    assert resp.status_code == 401


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_raceclass_not_found(
    client: TestClient, mocker: MockFixture, event: Event
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=None,
    )

    raceclass_id = str(uuid.uuid4())
    resp = client.get(f"/events/{event.id}/raceclasses/{raceclass_id}")
    assert resp.status_code == 404


@pytest.mark.integration
async def test_update_raceclass_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    raceclass: Raceclass,
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = raceclass.model_dump(mode="json")

    raceclass_id = str(uuid.uuid4())
    resp = client.put(
        f"/events/{event.id}/raceclasses/{raceclass_id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == 404


@pytest.mark.integration
async def test_delete_raceclass_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.delete_raceclass",
        return_value=None,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    raceclass_id = str(uuid.uuid4())
    resp = client.delete(
        f"/events/{event.id}/raceclasses/{raceclass_id}", headers=headers
    )
    assert resp.status_code == 404
