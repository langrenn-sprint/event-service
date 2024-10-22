"""Integration test cases for the results route."""

import os
from typing import Dict

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
async def event() -> Dict[str, str]:
    """An event object for testing."""
    return {
        "id": "event_id_1",
        "name": "Oslo Skagen sprint",
        "competition_format": "Individual sprint",
        "date_of_event": "2021-08-31",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def new_result() -> dict:
    """Create a mock result object."""
    return {
        "event_id": "event_id_1",
        "raceclass": "G12",
        "timing_point": "Finish",
        "no_of_contestants": 3,
        "ranking_sequence": [
            {"rank": 1, "bib": 19},
            {"rank": 2, "bib": 23},
            {"rank": 3, "bib": 11},
        ],
        "status": 1,
    }


@pytest.fixture
async def result() -> dict:
    """Create a mock result object."""
    return {
        "id": "id1",
        "event_id": "event_id_1",
        "raceclass": "G12",
        "timing_point": "Finish",
        "no_of_contestants": 3,
        "ranking_sequence": [
            {"rank": 1, "bib": 19},
            {"rank": 2, "bib": 23},
            {"rank": 3, "bib": 11},
        ],
        "status": 1,
    }


@pytest.mark.integration
async def test_create_result(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_result: dict,
) -> None:
    """Should return 201 Created, location header."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.results_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.create_result",
        return_value=RACECLASS_ID,
    )

    request_body = new_result
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/results", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert (
            f"/events/{EVENT_ID}/results/{RACECLASS_ID}" in resp.headers[hdrs.LOCATION]
        )


@pytest.mark.integration
async def test_get_result(
    client: _TestClient, mocker: MockFixture, token: MockFixture, result: dict
) -> None:
    """Should return OK, and a list containing one result."""
    EVENT_ID = "event_id_1"
    RACECLASS = "G12"
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.get_result_by_raceclass",
        return_value=result,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/results/{RACECLASS}")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == result["id"]
        assert body["raceclass"] == result["raceclass"]
        assert body["event_id"] == result["event_id"]


@pytest.mark.integration
async def test_get_all_results(
    client: _TestClient, mocker: MockFixture, token: MockFixture, result: dict
) -> None:
    """Should return OK and a valid json body."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.get_all_results",
        return_value=[result],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/results")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        results = await resp.json()
        assert type(results) is list
        assert len(results) > 0
        assert result["id"] == results[0]["id"]


@pytest.mark.integration
async def test_delete_result_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, result: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    RACECLASS = "G12"
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.get_result_by_raceclass",  # noqa: B950
        return_value=result,
    )
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.delete_result",
        return_value=RACECLASS,
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(
            f"/events/{EVENT_ID}/results/{RACECLASS}", headers=headers
        )
        assert resp.status == 204


# Bad cases
# Event not found
@pytest.mark.integration
async def test_create_result_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_result: dict,
) -> None:
    """Should return 422 Event Not found."""
    EVENT_ID = "event_id_x"
    RACECLASS = "G12"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.services.results_service.create_id",
        return_value=RACECLASS,
    )
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.create_result",
        return_value=RACECLASS,
    )

    request_body = new_result
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/results", headers=headers, json=request_body
        )
        assert resp.status == 422


# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_result_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.results_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.create_result",
        return_value=RACECLASS_ID,
    )

    request_body = {"id": RACECLASS_ID, "optional_property": "Optional_property"}
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/results", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_result_with_input_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    result: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.results_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.create_result",
        return_value=RACECLASS_ID,
    )

    request_body = result
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/results", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_result_adapter_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_result: dict,
) -> None:
    """Should return 400 HTTPBadRequest."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.results_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.create_result",  # noqa: B950
        return_value=None,
    )

    request_body = new_result
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/results", headers=headers, json=request_body
        )
        assert resp.status == 400


# Unauthorized cases:
@pytest.mark.integration
async def test_create_result_no_authorization(
    client: _TestClient, mocker: MockFixture, event: dict, new_result: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.results_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.create_result",
        return_value=RACECLASS_ID,
    )

    request_body = new_result
    headers = {hdrs.CONTENT_TYPE: "application/json"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post(
            f"/events/{EVENT_ID}/results", headers=headers, json=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_result_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, result: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.get_result_by_id",
        return_value=result,
    )
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.delete_result",
        return_value=RACECLASS_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.delete(f"/events/{EVENT_ID}/results/{RACECLASS_ID}")
        assert resp.status == 401


# NOT FOUND CASES:
@pytest.mark.integration
async def test_get_result_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    RACECLASS = "does-not-exist"
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.get_result_by_raceclass",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/results/{RACECLASS}")
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_result_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    RACECLASS = "does-not-exist"
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.get_result_by_raceclass",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.results_adapter.ResultsAdapter.delete_result",
        return_value=None,
    )

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(
            f"/events/{EVENT_ID}/results/{RACECLASS}", headers=headers
        )
        assert resp.status == 404
