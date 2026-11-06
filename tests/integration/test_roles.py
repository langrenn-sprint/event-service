"""Integration test cases for the role model (event-service-gui#215).

FastAPI runs the role check before it validates path parameters and body. A
request with an invalid id and an empty body therefore gets 403 if the role
is not allowed, and 422 if it is, without reaching the handler.
"""

import os
import re
from http import HTTPStatus

import jwt
import pytest
from fastapi.testclient import TestClient

from app import api
from tests.role_model import REMOVED_ROLES, ROLES, WRITE_ACCESS, access_cases


@pytest.fixture
def client() -> TestClient:
    """Fixture to create a test client for the FastAPI application."""
    return TestClient(api)


def _token(role: str) -> str:
    payload = {"username": "tester", "role": role, "exp": 9999999999}
    return jwt.encode(payload, os.environ["JWT_SECRET"], "HS256")


@pytest.mark.integration
@pytest.mark.parametrize(
    ("method", "path", "role", "allowed"), access_cases(ROLES + REMOVED_ROLES)
)
async def test_write_access(
    client: TestClient, method: str, path: str, role: str, *, allowed: bool
) -> None:
    """Allowed roles pass the role check (422), the others get 403."""
    # "not-a-uuid" fails validation of every path parameter:
    resp = client.request(
        method,
        re.sub(r"\{\w+\}", "not-a-uuid", path),
        headers={"Authorization": f"Bearer {_token(role)}"},
        json=None if method == "DELETE" else {},
    )
    expected = HTTPStatus.UNPROCESSABLE_ENTITY if allowed else HTTPStatus.FORBIDDEN
    assert resp.status_code == expected, resp.text


@pytest.mark.integration
async def test_openapi_shows_the_role_model(client: TestClient) -> None:
    """Every write operation shows exactly the roles in the role model."""
    resp = client.get("/openapi.json")
    assert resp.status_code == HTTPStatus.OK
    shown = {
        (method.upper(), path): set(operation["security"][0]["HTTPBearer"])
        for path, item in resp.json()["paths"].items()
        for method, operation in item.items()
        if "security" in operation
    }
    # A new write operation must be added to the role model:
    assert shown == WRITE_ACCESS

    for path, item in resp.json()["paths"].items():
        for method, operation in item.items():
            if method == "get" or path.endswith("/contestants/search"):
                assert "security" not in operation, f"{method} {path} should be open"
            if "security" in operation:
                assert "**Roles:**" in operation["description"]
                assert {"401", "403"} <= set(operation["responses"])
    # The schema is generated once, so the roles are not added twice:
    assert client.get("/openapi.json").json() == resp.json()
