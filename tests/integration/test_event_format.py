"""Integration test cases for the event_format route."""
from copy import deepcopy
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
async def event() -> dict[str, str]:
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
async def new_event_format_interval_start() -> dict:
    """Create a mock event_format object."""
    return {
        "name": "Interval Start",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
        "datatype": "interval_start",
    }


@pytest.fixture
async def new_event_format_individual_sprint() -> dict:
    """Create a mock event_format object."""
    return {
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "time_between_rounds": "00:05:00",
        "time_between_heats": "00:02:30",
        "max_no_of_contestants": 80,
        "datatype": "individual_sprint",
    }


@pytest.fixture
async def event_format_interval_start() -> dict:
    """Create a mock event_format object."""
    return {
        "name": "Interval Start",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
        "datatype": "interval_start",
    }


@pytest.fixture
async def event_format_individual_sprint() -> dict:
    """Create a mock event_format object."""
    return {
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "time_between_rounds": "00:05:00",
        "time_between_heats": "00:02:30",
        "max_no_of_contestants": 80,
        "datatype": "individual_sprint",
    }


@pytest.mark.integration
async def test_create_event_format_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_event_format_interval_start: dict,
) -> None:
    """Should return Created, location header."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.event_format_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.create_event_format",
        return_value=RACECLASS_ID,
    )

    request_body = new_event_format_interval_start
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/format", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert f"/events/{EVENT_ID}/format" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_create_event_format_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_event_format_individual_sprint: dict,
) -> None:
    """Should return Created, location header."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.event_format_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.create_event_format",
        return_value=RACECLASS_ID,
    )

    request_body = new_event_format_individual_sprint
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/format", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert f"/events/{EVENT_ID}/format" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_event_format_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_format_interval_start: dict,
) -> None:
    """Should return OK, and a body containing one event_format."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",
        return_value=event_format_interval_start,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/format", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["name"] == event_format_interval_start["name"]
        assert body["starting_order"] == event_format_interval_start["starting_order"]
        assert body["start_procedure"] == event_format_interval_start["start_procedure"]
        assert body["intervals"] == event_format_interval_start["intervals"]


@pytest.mark.integration
async def test_get_event_format_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_format_individual_sprint: dict,
) -> None:
    """Should return OK, and a body containing one event_format."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",
        return_value=event_format_individual_sprint,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/format", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["name"] == event_format_individual_sprint["name"]
        assert (
            body["starting_order"] == event_format_individual_sprint["starting_order"]
        )
        assert (
            body["start_procedure"] == event_format_individual_sprint["start_procedure"]
        )
        assert (
            body["time_between_heats"]
            == event_format_individual_sprint["time_between_heats"]
        )
        assert (
            body["time_between_rounds"]
            == event_format_individual_sprint["time_between_rounds"]
        )
        assert (
            body["max_no_of_contestants"]
            == event_format_individual_sprint["max_no_of_contestants"]
        )


@pytest.mark.integration
async def test_update_event_format_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_format_interval_start: dict,
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",  # noqa: B950
        return_value=event_format_interval_start,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.update_event_format",
        return_value=RACECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = deepcopy(event_format_interval_start)
    request_body["starting_order"] = "Manual Draw"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/format",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_update_event_format_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_format_individual_sprint: dict,
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",  # noqa: B950
        return_value=event_format_individual_sprint,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.update_event_format",
        return_value=RACECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = deepcopy(event_format_individual_sprint)
    request_body["starting_order"] = "Manual Draw"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/format",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_delete_event_format(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_format_interval_start: dict,
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",  # noqa: B950
        return_value=event_format_interval_start,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.delete_event_format",
        return_value=RACECLASS_ID,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(f"/events/{EVENT_ID}/format", headers=headers)
        assert resp.status == 204


# Bad cases
# Event not found
@pytest.mark.integration
async def test_create_event_format_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_event_format_interval_start: dict,
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.services.event_format_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.create_event_format",
        return_value=RACECLASS_ID,
    )

    request_body = new_event_format_interval_start
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/format", headers=headers, json=request_body
        )
        assert resp.status == 404


# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_event_format_missing_mandatory_property(
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
        "event_service.services.event_format_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.create_event_format",
        return_value=RACECLASS_ID,
    )

    request_body = {"id": RACECLASS_ID, "optional_property": "Optional_property"}
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/format", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_event_format_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",  # noqa: B950
        return_value={"id": RACECLASS_ID, "name": "missing_the_rest_of_the_properties"},
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.update_event_format",
        return_value=RACECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": RACECLASS_ID, "name": "missing_the_rest_of_the_properties"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/format",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_event_format_adapter_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_event_format_interval_start: dict,
) -> None:
    """Should return 400 HTTPBadRequest."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.event_format_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.create_event_format",  # noqa: B950
        return_value=None,
    )
    request_body = new_event_format_interval_start
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/format", headers=headers, json=request_body
        )
        assert resp.status == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_create_event_format_no_authorization(
    client: _TestClient,
    mocker: MockFixture,
    event: dict,
    new_event_format_interval_start: dict,
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.event_format_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.create_event_format",
        return_value=RACECLASS_ID,
    )

    request_body = new_event_format_interval_start
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post(
            f"/events/{EVENT_ID}/format", headers=headers, json=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_get_event_format_no_authorization(
    client: _TestClient, mocker: MockFixture, event_format_interval_start: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",
        return_value=event_format_interval_start,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get(f"/events/{EVENT_ID}/format")
        assert resp.status == 401


@pytest.mark.integration
async def test_put_event_format_no_authorization(
    client: _TestClient, mocker: MockFixture, event_format_interval_start: dict
) -> None:
    """Should return 401 Unauthorizedt."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",
        return_value=event_format_interval_start,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.update_event_format",
        return_value=RACECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )
    request_body = event_format_interval_start

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.put(
            f"/events/{EVENT_ID}/format",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_event_format_no_authorization(
    client: _TestClient, mocker: MockFixture, event_format_interval_start: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",
        return_value=[event_format_interval_start],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get(f"/events/{EVENT_ID}/format")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_event_format_no_authorization(
    client: _TestClient, mocker: MockFixture, event_format_interval_start: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",
        return_value=event_format_interval_start,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.delete_event_format",
        return_value=RACECLASS_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.delete(f"/events/{EVENT_ID}/format")
        assert resp.status == 401


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_event_format_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",
        return_value=None,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/format", headers=headers)
        assert resp.status == 404


@pytest.mark.integration
async def test_update_event_format_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_format_interval_start: dict,
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.update_event_format",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = event_format_interval_start

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/format",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_event_format_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.get_event_format",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.event_format_adapter.EventFormatAdapter.delete_event_format",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(f"/events/{EVENT_ID}/format", headers=headers)
        assert resp.status == 404
