"""Integration test cases for the events route."""
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
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


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
        "birth_date": "1970-01-01",
        "gender": "M",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": "ref_to_event",
    }


@pytest.fixture
async def ageclass() -> dict:
    """Create a mock ageclass object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "G 16 år",
        "order": 1,
        "raceclass": "G16",
        "event_id": "ref_to_event",
        "distance": "5km",
    }


@pytest.mark.integration
async def test_generate_ageclasses_on_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    ageclass: dict,
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_name",
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=ageclass["id"],
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-ageclasses", headers=headers
        )
        assert resp.status == 201
        assert f"/events/{event_id}/ageclasses" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_generate_ageclasses_on_event_ageclass_exist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    ageclass: dict,
) -> None:
    """Should return 201 Created, location header."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",
        return_value=ageclass,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_name",
        return_value=[ageclass],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.update_ageclass",
        return_value=ageclass,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-ageclasses", headers=headers
        )
        assert resp.status == 201
        assert f"/events/{event_id}/ageclasses" in resp.headers[hdrs.LOCATION]


# Bad cases:
@pytest.mark.integration
async def test_generate_ageclasses_on_event_duplicate_ageclasses(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    ageclass: dict,
) -> None:
    """Should return 422 Unprocessable entity."""
    ageclass_id = ageclass["id"]
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_name",
        return_value=[ageclass, ageclass],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=ageclass_id,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-ageclasses", headers=headers
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_generate_ageclasses_on_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    ageclass: dict,
) -> None:
    """Should return 404 Not found."""
    ageclass_id = ageclass["id"]
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_name",
        return_value=[ageclass, ageclass],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=ageclass_id,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-ageclasses", headers=headers
        )
        assert resp.status == 404


# Not authenticated
@pytest.mark.integration
async def test_generate_ageclasses_on_event_unauthorized(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    ageclass: dict,
) -> None:
    """Should return 401 Unauthorized."""
    AGECLASS_ID = "ageclass_id_1"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_name",
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=AGECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.post(
            f"/events/{event_id}/generate-ageclasses", headers=headers
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_generate_ageclasses_on_event_create_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    ageclass: dict,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_name",
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-ageclasses", headers=headers
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_generate_ageclasses_on_event_update_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
    ageclass: dict,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_name",
        return_value=[ageclass],
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",
        return_value=ageclass,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.update_ageclass",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    event_id = event["id"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{event_id}/generate-ageclasses", headers=headers
        )
        assert resp.status == 400
