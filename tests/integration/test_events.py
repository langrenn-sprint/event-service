"""Integration test cases for the events route."""
from copy import deepcopy
import os
from typing import Dict, Union

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
import jwt
from multidict import MultiDict
import pytest
from pytest_mock import MockFixture

from event_service.adapters import CompetitionFormatsAdapterException


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "user", "roles": ["user"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.fixture
async def event() -> Dict[str, str]:
    """An event object for testing."""
    return {
        "name": "Oslo Skagen sprint",
        "competition_format": "Individual sprint",
        "date_of_event": "2021-08-31",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def competition_format() -> Dict[str, Union[int, str]]:
    """An competition_format object for testing."""
    return {
        "name": "Interval Start",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
        "max_no_of_contestants_in_raceclass": 9999,
        "max_no_of_contestants_in_race": 9999,
        "timezone": "Europe/Oslo",
        "datatype": "interval_start",
    }


@pytest.mark.integration
async def test_create_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
) -> None:
    """Should return Created, location header."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[competition_format],
    )

    request_body = event

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 201
        assert f"/events/{ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, event: Dict[str, str]
) -> None:
    """Should return OK, and a body containing one event."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID} | event,  # type: ignore
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/events/{ID}")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(event) is dict
        assert body["id"] == ID
        assert body["name"] == event["name"]
        assert body["competition_format"] == event["competition_format"]
        assert body["date_of_event"] == event["date_of_event"]
        assert body["organiser"] == event["organiser"]
        assert body["webpage"] == event["webpage"]
        assert body["information"] == event["information"]


@pytest.mark.integration
async def test_update_event_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID} | event,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value={"id": ID} | event,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[competition_format],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    new_name = "Oslo Skagen sprint Oppdatert"
    request_body = deepcopy(event)
    request_body["id"] = ID
    request_body["name"] = new_name

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_events(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return OK and a valid json body."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_all_events",
        return_value=[{"id": ID, "name": "Oslo Skagen Sprint"}],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get("/events")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        events = await resp.json()
        assert type(events) is list
        assert len(events) > 0
        assert ID == events[0]["id"]


@pytest.mark.integration
async def test_delete_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=ID,
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.delete(f"/events/{ID}", headers=headers)
        assert resp.status == 204


# Bad cases

# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_event_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    request_body = {"optional_property": "Optional_property"}
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_event_competition_formats_adapter_raises_exception(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
) -> None:
    """Should return Created, location header."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        side_effect=CompetitionFormatsAdapterException(
            "Got unknown status 500 from competition_formats service."
        ),
    )

    request_body = event

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_event_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    request_body = {"id": ID, "name": "Oslo Skagen sprint Oppdatert"}
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_event_adapter_fails(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=None,
    )
    request_body = {"name": "Oslo Skagen sprint Oppdatert"}
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_update_event_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {"id": ID, "optional_property": "Optional_property"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_update_event_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {"id": "different_id", "name": "Oslo Skagen sprint Oppdatert"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_event_invalid_date(
    client: _TestClient, mocker: MockFixture, token: MockFixture, event: dict
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    event_invalid_date = deepcopy(event)
    event_invalid_date["date_of_event"] = "9999-99-99"

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=event_invalid_date)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_event_invalid_time(
    client: _TestClient, mocker: MockFixture, token: MockFixture, event: dict
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    event_invalid_time = deepcopy(event)
    event_invalid_time["time_of_event"] = "99:99:99"

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=event_invalid_time)
        assert resp.status == 400


@pytest.mark.integration
async def test_update_event_invalid_date(
    client: _TestClient, mocker: MockFixture, token: MockFixture, event: dict
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID} | event,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value={"id": ID} | event,  # type: ignore
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = deepcopy(event)
    request_body["id"] = ID
    request_body["date_of_event"] = "9999-99-99"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_update_event_invalid_time(
    client: _TestClient, mocker: MockFixture, token: MockFixture, event: dict
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID} | event,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value={"id": ID} | event,  # type: ignore
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = deepcopy(event)
    request_body["id"] = ID
    request_body["time_of_event"] = "99:99:99"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_event_multiple_competition_formats(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[competition_format, competition_format],
    )

    request_body = event

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_event_invalid_competition_format(
    client: _TestClient, mocker: MockFixture, token: MockFixture, event: dict
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )

    event_invalid_competition_format = deepcopy(event)
    event_invalid_competition_format[
        "competition_format"
    ] = "Invalid Competition Format"

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/events", headers=headers, json=event_invalid_competition_format
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_update_event_invalid_competition_format(
    client: _TestClient, mocker: MockFixture, token: MockFixture, event: dict
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID} | event,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value={"id": ID} | event,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = deepcopy(event)
    request_body["id"] = ID
    request_body["competition_format"] = "Invalid Competition Format"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_create_event_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    request_body = {"name": "Oslo Skagen sprint"}
    headers = MultiDict([(hdrs.CONTENT_TYPE, "application/json")])

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_update_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
    }

    request_body = {"id": ID, "name": "Oslo Skagen sprint Oppdatert"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.delete(f"/events/{ID}")
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_event_insufficient_role(
    client: _TestClient, mocker: MockFixture, token_unsufficient_role: MockFixture
) -> None:
    """Should return 403 Forbidden."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    request_body = {"name": "Oslo Skagen sprint"}
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=403)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/events/{ID}")
        assert resp.status == 404


@pytest.mark.integration
async def test_update_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint Oppdatert",
    }

    ID = "does-not-exist"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=None,
    )

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(f"/events/{ID}", headers=headers)
        assert resp.status == 404
