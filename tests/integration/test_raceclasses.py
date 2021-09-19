"""Integration test cases for the raceclasses route."""
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
async def new_raceclass() -> dict:
    """Create a mock raceclass object."""
    return {
        "name": "G16",
        "ageclass_name": "G 16 år",
        "order": 1,
        "event_id": "ref_to_event",
        "distance": "5km",
    }


@pytest.fixture
async def raceclass() -> dict:
    """Create a mock raceclass object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "G16",
        "ageclass_name": "G 16 år",
        "order": 1,
        "event_id": "ref_to_event",
        "distance": "5km",
    }


@pytest.mark.integration
async def test_create_raceclass(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_raceclass: dict
) -> None:
    """Should return Created, location header."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.raceclasses_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=RACECLASS_ID,
    )

    request_body = new_raceclass
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/raceclasses", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert (
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}"
            in resp.headers[hdrs.LOCATION]
        )


@pytest.mark.integration
async def test_get_raceclass_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceclass: dict
) -> None:
    """Should return OK, and a body containing one raceclass."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}", headers=headers
        )
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == raceclass["id"]
        assert body["name"] == raceclass["name"]
        assert body["order"] == raceclass["order"]
        assert body["ageclass_name"] == raceclass["ageclass_name"]
        assert body["event_id"] == raceclass["event_id"]
        assert body["distance"] == raceclass["distance"]


@pytest.mark.integration
async def test_get_raceclass_by_ageclass_name(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceclass: dict
) -> None:
    """Should return 200 OK, and a body containing one raceclass."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_ageclass_name",  # noqa: B950
        return_value=[raceclass],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    ageclass_name = raceclass["ageclass_name"]
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(
            f"/events/{EVENT_ID}/raceclasses?ageclass-name={ageclass_name}",
            headers=headers,
        )
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert body[0]["id"] == raceclass["id"]
        assert body[0]["name"] == raceclass["name"]
        assert body[0]["order"] == raceclass["order"]
        assert body[0]["ageclass_name"] == raceclass["ageclass_name"]
        assert body[0]["event_id"] == raceclass["event_id"]
        assert body[0]["distance"] == raceclass["distance"]


@pytest.mark.integration
async def test_update_raceclass_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceclass: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",  # noqa: B950
        return_value=raceclass,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=RACECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = deepcopy(raceclass)
    request_body["distance"] = "New distance"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_raceclasses(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceclass: dict
) -> None:
    """Should return OK and a valid json body."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/raceclasses", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        raceclasses = await resp.json()
        assert type(raceclasses) is list
        assert len(raceclasses) > 0
        assert raceclass["id"] == raceclasses[0]["id"]


@pytest.mark.integration
async def test_delete_raceclass_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceclass: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",  # noqa: B950
        return_value=raceclass,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.delete_raceclass",
        return_value=RACECLASS_ID,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}", headers=headers
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_delete_all_raceclasses_in_event(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceclass: dict
) -> None:
    """Should return 204 No content."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.delete_all_raceclasses",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",  # noqa: B950
        return_value=[],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(f"/events/{EVENT_ID}/raceclasses", headers=headers)
        assert resp.status == 204
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/raceclasses", headers=headers)
        assert resp.status == 200
        raceclasses = await resp.json()
        assert len(raceclasses) == 0


# Bad cases
# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_raceclass_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.raceclasses_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
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
            f"/events/{EVENT_ID}/raceclasses", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_raceclass_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",  # noqa: B950
        return_value={"id": RACECLASS_ID, "name": "missing_the_rest_of_the_properties"},
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
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
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_raceclass_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceclass: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.raceclasses_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=RACECLASS_ID,
    )

    request_body = raceclass
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/raceclasses", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_raceclass_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceclass: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",  # noqa: B950
        return_value=raceclass,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=RACECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = deepcopy(raceclass)
    request_body["id"] = "different_id"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_raceclass_adapter_fails(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_raceclass: dict
) -> None:
    """Should return 400 HTTPBadRequest."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.services.raceclasses_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",  # noqa: B950
        return_value=None,
    )
    request_body = new_raceclass
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/raceclasses", headers=headers, json=request_body
        )
        assert resp.status == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_create_raceclass_no_authorization(
    client: _TestClient, mocker: MockFixture, new_raceclass: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.raceclasses_service.create_id",
        return_value=RACECLASS_ID,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.create_raceclass",
        return_value=RACECLASS_ID,
    )

    request_body = new_raceclass
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post(
            f"/events/{EVENT_ID}/raceclasses", headers=headers, json=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_get_raceclass_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, raceclass: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get(f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_put_raceclass_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, raceclass: dict
) -> None:
    """Should return 401 Unauthorizedt."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=RACECLASS_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )
    request_body = raceclass

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.put(
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_raceclasses_no_authorization(
    client: _TestClient, mocker: MockFixture, raceclass: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[raceclass],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get(f"/events/{EVENT_ID}/raceclasses")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_raceclass_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, raceclass: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=raceclass,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.delete_raceclass",
        return_value=RACECLASS_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.delete(f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_all_raceclasses_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.delete_all_raceclasses",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.delete(f"/events/{EVENT_ID}/raceclasses")
        assert resp.status == 401


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_raceclass_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
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
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}", headers=headers
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_update_raceclass_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceclass: dict
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = raceclass

    RACECLASS_ID = "does-not-exist"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_raceclass_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    RACECLASS_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.delete_raceclass",
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
            f"/events/{EVENT_ID}/raceclasses/{RACECLASS_ID}", headers=headers
        )
        assert resp.status == 404