"""Integration test cases for the login route."""
import os

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
import jwt
from multidict import MultiDict
import pytest
from pytest_mock import MockFixture


@pytest.mark.integration
async def test_login_valid_user_password(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 200 OK and a valid token."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )

    resp = await client.post("/login", headers=headers, json=request_body)
    assert resp.status == 200
    body = await resp.json()
    assert type(body) is dict
    assert body["token"]
    jwt.decode(body["token"], os.getenv("JWT_SECRET"), algorithms="HS256")  # type: ignore


@pytest.mark.integration
async def test_login_invalid_user(client: _TestClient, mocker: MockFixture) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    request_body = {
        "username": "NON_EXISTENT_USER",
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )

    resp = await client.post("/login", headers=headers, json=request_body)
    assert resp.status == 401


@pytest.mark.integration
async def test_login_wrong_password(client: _TestClient, mocker: MockFixture) -> None:
    """Should return 401 OK."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": "WRONG_PASSWORD",
    }
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )

    resp = await client.post("/login", headers=headers, json=request_body)
    assert resp.status == 401


@pytest.mark.integration
async def test_login_no_body_in_request(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 400 Bad Request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )

    resp = await client.post("/login", headers=headers)
    assert resp.status == 400
