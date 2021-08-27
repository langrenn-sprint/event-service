"""Integration test cases for the ageclasses route."""
import os

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
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


@pytest.mark.integration
async def test_create_ageclass(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return Created, location header."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=ID,
    )

    request_body = {"name": "Oslo Skagen sprint"}
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    resp = await client.post("/ageclasses", headers=headers, json=request_body)
    assert resp.status == 201
    assert f"/ageclasses/{ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_ageclass_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return OK, and a body containing one ageclass."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    resp = await client.get(f"/ageclasses/{ID}", headers=headers)
    assert resp.status == 200
    assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
    ageclass = await resp.json()
    assert type(ageclass) is dict
    assert ageclass["id"] == ID


@pytest.mark.integration
async def test_put_ageclass_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.update_ageclass",
        return_value=ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": ID, "name": "Oslo Skagen sprint Oppdatert"}

    resp = await client.put(f"/ageclasses/{ID}", headers=headers, json=request_body)
    assert resp.status == 204


@pytest.mark.integration
async def test_list_ageclasses(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return OK and a valid json body."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_all_ageclasses",
        return_value=[{"id": ID, "name": "Oslo Skagen Sprint"}],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    resp = await client.get("/ageclasses", headers=headers)
    assert resp.status == 200
    assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
    ageclasses = await resp.json()
    assert type(ageclasses) is list
    assert len(ageclasses) > 0


@pytest.mark.integration
async def test_delete_ageclass_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.delete_ageclass",
        return_value=ID,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    resp = await client.delete(f"/ageclasses/{ID}", headers=headers)
    assert resp.status == 204


# Bad cases

# Unauthorized cases:


@pytest.mark.integration
async def test_create_ageclass_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.create_ageclass",
        return_value=ID,
    )

    request_body = {"name": "Oslo Skagen sprint"}
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    resp = await client.post("/ageclasses", headers=headers, json=request_body)
    assert resp.status == 401


@pytest.mark.integration
async def test_get_ageclass_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )

    resp = await client.get(f"/ageclasses/{ID}")
    assert resp.status == 401


@pytest.mark.integration
async def test_put_ageclass_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorizedt."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.update_ageclass",
        return_value=ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )
    request_body = {"id": ID, "name": "Oslo Skagen sprint Oppdatert"}

    resp = await client.put(f"/ageclasses/{ID}", headers=headers, json=request_body)
    assert resp.status == 401


@pytest.mark.integration
async def test_list_ageclasses_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_all_ageclasses",
        return_value=[{"id": ID, "name": "Oslo Skagen Sprint"}],
    )
    resp = await client.get("/ageclasses")
    assert resp.status == 401


@pytest.mark.integration
async def test_delete_ageclass_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.delete_ageclass",
        return_value=ID,
    )

    resp = await client.delete(f"/ageclasses/{ID}")
    assert resp.status == 401


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_ageclass_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.get_ageclass",
        return_value=None,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    resp = await client.get(f"/ageclasses/{ID}", headers=headers)
    assert resp.status == 404


@pytest.mark.integration
async def test_update_ageclass_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
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
    request_body = {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint Oppdatert",
    }

    ID = "does-not-exist"
    resp = await client.put(f"/ageclasses/{ID}", headers=headers, json=request_body)
    assert resp.status == 404


@pytest.mark.integration
async def test_delete_ageclass_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.ageclasses_adapter.AgeclassesAdapter.delete_ageclass",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    resp = await client.delete(f"/ageclasses/{ID}", headers=headers)
    assert resp.status == 404
