"""Integration test cases for the events route."""
from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from multidict import MultiDict
import pytest
from pytest_mock import MockFixture


@pytest.mark.integration
async def test_create_event(client: _TestClient, mocker: MockFixture) -> None:
    """Should return Created, location header."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    request_body = {"name": "Oslo Skagen sprint"}
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    resp = await client.post("/events", headers=headers, json=request_body)
    assert resp.status == 201
    assert f"/events/{ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_event_by_id(client: _TestClient, mocker: MockFixture) -> None:
    """Should return OK, and a body containing one event."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )

    resp = await client.get(f"/events/{ID}")
    assert resp.status == 200
    assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
    event = await resp.json()
    assert type(event) is dict
    assert event["id"] == ID


@pytest.mark.integration
async def test_put_event_by_id(client: _TestClient, mocker: MockFixture) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=ID,
    )

    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})
    request_body = {"id": ID, "name": "Oslo Skagen sprint Oppdatert"}

    resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
    assert resp.status == 204


@pytest.mark.integration
async def test_list_events(client: _TestClient, mocker: MockFixture) -> None:
    """Should return OK and a valid json body."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_all_events",
        return_value=[{"id": ID, "name": "Oslo Skagen Sprint"}],
    )
    resp = await client.get("/events")
    assert resp.status == 200
    assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
    events = await resp.json()
    assert type(events) is list
    assert len(events) > 0


@pytest.mark.integration
async def test_delete_event_by_id(client: _TestClient, mocker: MockFixture) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=ID,
    )

    resp = await client.delete(f"/events/{ID}")
    assert resp.status == 204


# Bad cases


@pytest.mark.integration
async def test_get_event_not_found(client: _TestClient, mocker: MockFixture) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event",
        return_value=None,
    )

    resp = await client.get(f"/events/{ID}")
    assert resp.status == 404


@pytest.mark.integration
async def test_update_event_not_found(client: _TestClient, mocker: MockFixture) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=None,
    )
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})
    request_body = {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint Oppdatert",
    }

    ID = "does-not-exist"
    resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
    assert resp.status == 404


@pytest.mark.integration
async def test_delete_event_not_found(client: _TestClient, mocker: MockFixture) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=None,
    )
    resp = await client.delete(f"/events/{ID}")
    assert resp.status == 404
