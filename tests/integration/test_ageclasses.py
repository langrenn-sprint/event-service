"""Integration test cases for the ageclasses route."""
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
async def new_ageclass() -> dict:
    """Create a mock ageclass object."""
    return {
        "name": "G 16 år",
        "order": 1,
        "raceclass": "G16",
        "event_id": "ref_to_event",
        "distance": "5km",
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
async def test_create_ageclass(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_ageclass: dict
) -> None:
    """Should return Created, location header."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.ageclasses_service.create_id",
        return_value=AGECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=AGECLASS_ID,
    )

    request_body = new_ageclass
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/ageclasses", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert (
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}"
            in resp.headers[hdrs.LOCATION]
        )


@pytest.mark.integration
async def test_get_ageclass_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, ageclass: dict
) -> None:
    """Should return OK, and a body containing one ageclass."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",
        return_value=ageclass,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}", headers=headers
        )
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == ageclass["id"]
        assert body["name"] == ageclass["name"]
        assert body["order"] == ageclass["order"]
        assert body["raceclass"] == ageclass["raceclass"]
        assert body["event_id"] == ageclass["event_id"]
        assert body["distance"] == ageclass["distance"]


@pytest.mark.integration
async def test_get_ageclass_by_name(
    client: _TestClient, mocker: MockFixture, token: MockFixture, ageclass: dict
) -> None:
    """Should return 200 OK, and a body containing one ageclass."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_name",
        return_value=[ageclass],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    name = ageclass["name"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(
            f"/events/{EVENT_ID}/ageclasses?name={name}", headers=headers
        )
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert body[0]["id"] == ageclass["id"]
        assert body[0]["name"] == ageclass["name"]
        assert body[0]["order"] == ageclass["order"]
        assert body[0]["raceclass"] == ageclass["raceclass"]
        assert body[0]["event_id"] == ageclass["event_id"]
        assert body[0]["distance"] == ageclass["distance"]


@pytest.mark.integration
async def test_update_ageclass_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, ageclass: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",  # noqa: B950
        return_value=ageclass,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.update_ageclass",
        return_value=AGECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = deepcopy(ageclass)
    request_body["distance"] = "New distance"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_ageclasses(
    client: _TestClient, mocker: MockFixture, token: MockFixture, ageclass: dict
) -> None:
    """Should return OK and a valid json body."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_all_ageclasses",
        return_value=[ageclass],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/ageclasses", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        ageclasses = await resp.json()
        assert type(ageclasses) is list
        assert len(ageclasses) > 0
        assert ageclass["id"] == ageclasses[0]["id"]


@pytest.mark.integration
async def test_delete_ageclass_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, ageclass: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",  # noqa: B950
        return_value=ageclass,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.delete_ageclass",
        return_value=AGECLASS_ID,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}", headers=headers
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_delete_all_ageclasses_in_event(
    client: _TestClient, mocker: MockFixture, token: MockFixture, ageclass: dict
) -> None:
    """Should return 204 No content."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.delete_all_ageclasses",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_all_ageclasses",  # noqa: B950
        return_value=[],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(f"/events/{EVENT_ID}/ageclasses", headers=headers)
        assert resp.status == 204
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/ageclasses", headers=headers)
        assert resp.status == 200
        ageclasses = await resp.json()
        assert len(ageclasses) == 0


# Bad cases
# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_ageclass_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.ageclasses_service.create_id",
        return_value=AGECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=AGECLASS_ID,
    )

    request_body = {"id": AGECLASS_ID, "optional_property": "Optional_property"}
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/ageclasses", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_ageclass_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",  # noqa: B950
        return_value={"id": AGECLASS_ID, "name": "missing_the_rest_of_the_properties"},
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.update_ageclass",
        return_value=AGECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": AGECLASS_ID, "name": "missing_the_rest_of_the_properties"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_ageclass_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, ageclass: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.ageclasses_service.create_id",
        return_value=AGECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=AGECLASS_ID,
    )

    request_body = ageclass
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/ageclasses", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_ageclass_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture, ageclass: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",  # noqa: B950
        return_value=ageclass,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.update_ageclass",
        return_value=AGECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = deepcopy(ageclass)
    request_body["id"] = "different_id"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_ageclass_adapter_fails(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_ageclass: dict
) -> None:
    """Should return 400 HTTPBadRequest."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.services.ageclasses_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",  # noqa: B950
        return_value=None,
    )
    request_body = new_ageclass
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/ageclasses", headers=headers, json=request_body
        )
        assert resp.status == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_create_ageclass_no_authorization(
    client: _TestClient, mocker: MockFixture, new_ageclass: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.ageclasses_service.create_id",
        return_value=AGECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=AGECLASS_ID,
    )

    request_body = new_ageclass
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post(
            f"/events/{EVENT_ID}/ageclasses", headers=headers, json=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_get_ageclass_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, ageclass: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",
        return_value=ageclass,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get(f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_put_ageclass_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, ageclass: dict
) -> None:
    """Should return 401 Unauthorizedt."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",
        return_value=ageclass,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.update_ageclass",
        return_value=AGECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )
    request_body = ageclass

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.put(
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_ageclasses_no_authorization(
    client: _TestClient, mocker: MockFixture, ageclass: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_all_ageclasses",
        return_value=[ageclass],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get(f"/events/{EVENT_ID}/ageclasses")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_ageclass_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, ageclass: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",
        return_value=ageclass,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.delete_ageclass",
        return_value=AGECLASS_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.delete(f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_all_ageclasses_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.delete_all_ageclasses",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.delete(f"/events/{EVENT_ID}/ageclasses")
        assert resp.status == 401


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_ageclass_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",
        return_value=None,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}", headers=headers
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_update_ageclass_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, ageclass: dict
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",
        return_value=None,
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
    request_body = ageclass

    AGECLASS_ID = "does-not-exist"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_ageclass_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    AGECLASS_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.delete_ageclass",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(
            f"/events/{EVENT_ID}/ageclasses/{AGECLASS_ID}", headers=headers
        )
        assert resp.status == 404
