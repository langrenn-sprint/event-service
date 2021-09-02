"""Integration test cases for the contestant route."""
import copy
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
async def new_contestant() -> dict:
    """Create a mock contestant object."""
    return {
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": "1970-01-01",
        "club": "Lyn Ski",
    }


@pytest.fixture
async def contestant() -> dict:
    """Create a mock contestant object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": "1970-01-01",
        "club": "Lyn Ski",
    }


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "user", "roles": ["user"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.mark.integration
async def test_create_contestant_good_case(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_contestant: dict
) -> None:
    """Should return Created, location header."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    request_body = new_contestant

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert (
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}"
            in resp.headers[hdrs.LOCATION]
        )


@pytest.mark.integration
async def test_get_contestant_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return OK, and a body containing one contestant."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}", headers=headers
        )
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == CONTESTANT_ID
        assert body["first_name"] == contestant["first_name"]
        assert body["last_name"] == contestant["last_name"]


@pytest.mark.integration
async def test_update_contestant_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = copy.deepcopy(contestant)
    request_body["last_name"] = "New_Last_Name"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_list_contestants(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return OK and a valid json body."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",  # noqa: B950
        return_value=[contestant],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/contestants", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        contestants = await resp.json()
        assert type(contestants) is list
        assert len(contestants) == 1


@pytest.mark.integration
async def test_delete_contestant_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.delete_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.delete(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}", headers=headers
        )
        assert resp.status == 204


# Bad cases

# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_contestant_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    request_body = {"optional_property": "Optional_property"}
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_contestant_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    request_body = contestant
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_contestant_adapter_fails(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_contestant: dict
) -> None:
    """Should return 400 HTTPBadRequest."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=None,
    )
    request_body = new_contestant
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_update_contestant_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value={"id": CONTESTANT_ID, "first_name": "Missing LastName"},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=CONTESTANT_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": CONTESTANT_ID, "optional_property": "Optional_property"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_contestant_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant["id"],
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = copy.deepcopy(contestant)
    request_body["id"] = "different_id"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


# Unauthorized cases:


@pytest.mark.integration
async def test_create_contestant_no_authorization(
    client: _TestClient, mocker: MockFixture, new_contestant: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    request_body = new_contestant
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_get_contestant_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, contestant: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.get(f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_update_contestant_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, contestant: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=CONTESTANT_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )
    request_body = contestant

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_contestants_no_authorization(
    client: _TestClient, mocker: MockFixture, contestant: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",  # noqa: B950
        return_value=[contestant],
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get(f"/events/{EVENT_ID}/contestants")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_contestant_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.delete_contestant",
        return_value=CONTESTANT_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.delete(f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}")
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_contestant_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    new_contestant: dict,
) -> None:
    """Should return 403 Forbidden."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=CONTESTANT_ID,
    )
    request_body = new_contestant
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=403)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_contestant_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
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
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}", headers=headers
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_update_contestant_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = contestant

    CONTESTANT_ID = "does-not-exist"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_contestant_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.delete_contestant",
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
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}", headers=headers
        )
        assert resp.status == 404
