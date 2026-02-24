"""Integration test cases for the results route."""

import os
import uuid
from http import HTTPStatus

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app import api
from app.models import Event, Result


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
async def result(event: Event) -> Result:
    """Create a mock result object."""
    return Result.model_validate(
        {
            "id": str(uuid.uuid4()),
            "event_id": event.id,
            "raceclass_name": "G12",
            "timing_point": "Finish",
            "no_of_contestants": 3,
            "ranking_sequence": [
                {"rank": 1, "bib": 19},
                {"rank": 2, "bib": 23},
                {"rank": 3, "bib": 11},
            ],
            "status": 1,
        }
    )


@pytest.mark.integration
async def test_create_result(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    result: Result,
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.create_result",
        return_value=result.id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = result.model_dump(mode="json")

    resp = client.post(
        f"/events/{event.id}/results", headers=headers, json=request_body
    )
    assert resp.status_code == 201
    assert f"/events/{event.id}/results/{result.id}" in resp.headers["Location"]


@pytest.mark.integration
async def test_get_result_by_id(
    client: TestClient, mocker: MockFixture, event: Event, result: Result
) -> None:
    """Should return OK, and one result."""
    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.get_result_by_raceclass_name",
        return_value=result,
    )

    resp = client.get(f"/events/{event.id}/results/{result.id}")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(result.id)
    assert body["raceclass_name"] == result.raceclass_name
    assert body["event_id"] == str(result.event_id)


@pytest.mark.integration
async def test_get_result_by_raceclass_name(
    client: TestClient, mocker: MockFixture, result: Result, event: Event
) -> None:
    """Should return OK, and a list containing one result."""
    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.get_result_by_raceclass_name",
        return_value=result,
    )

    resp = client.get(f"/events/{event.id}/results/{result.raceclass_name}")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(result.id)
    assert body["raceclass_name"] == result.raceclass_name
    assert body["event_id"] == str(result.event_id)


@pytest.mark.integration
async def test_get_all_results(
    client: TestClient,
    mocker: MockFixture,
    result: Result,
    event: Event,
) -> None:
    """Should return OK and a list of results."""
    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.get_all_results",
        return_value=[result],
    )

    resp = client.get(f"/events/{event.id}/results")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    results = resp.json()
    assert type(results) is list
    assert len(results) > 0
    assert str(result.id) == results[0]["id"]


@pytest.mark.integration
async def test_delete_result_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    result: Result,
    event: Event,
) -> None:
    """Should return No Content."""
    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.get_result_by_raceclass_name",
        return_value=result,
    )
    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.delete_result",
        return_value=result.id,
    )
    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.delete(f"/events/{event.id}/results/{result.id}", headers=headers)
    assert resp.status_code == 204


# Bad cases
# Event not found
@pytest.mark.integration
async def test_create_result_event_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    result: Result,
    event: Event,
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = result.model_dump(mode="json")

    resp = client.post(
        f"/events/{event.id}/results", headers=headers, json=request_body
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_result_missing_mandatory_property(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = {"id": str(uuid.uuid4()), "optional_property": "Optional_property"}

    resp = client.post(
        f"/events/{event.id}/results", headers=headers, json=request_body
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_result_adapter_fails(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    result: Result,
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.create_result",
        return_value=None,
    )

    request_body = result.model_dump(mode="json")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/results", headers=headers, json=request_body
    )
    assert resp.status_code == 400


# Unauthorized cases:
@pytest.mark.integration
async def test_create_result_no_authorization(
    client: TestClient, event: Event, result: Result
) -> None:
    """Should return 401 Unauthorized."""
    headers = {"Content-Type": "application/json"}
    request_body = result.model_dump(mode="json")

    resp = client.post(
        f"/events/{event.id}/results", headers=headers, json=request_body
    )
    assert resp.status_code == 401


@pytest.mark.integration
async def test_delete_result_by_id_no_authorization(
    client: TestClient, result: Result, event: Event
) -> None:
    """Should return 401 Unauthorized."""
    resp = client.delete(f"/events/{event.id}/results/{result.id}")
    assert resp.status_code == 401


# NOT FOUND CASES:
@pytest.mark.integration
async def test_get_result_by_raceclass_name_not_found(
    client: TestClient, mocker: MockFixture, event: Event
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.get_result_by_raceclass_name",
        return_value=None,
    )

    resp = client.get(f"/events/{event.id}/results/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.integration
async def test_delete_result_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.get_result_by_raceclass_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.results_adapter.ResultsAdapter.delete_result",
        return_value=None,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.delete(f"/events/{event.id}/results/does-not-exist", headers=headers)
    assert resp.status_code == 404
