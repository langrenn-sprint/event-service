"""Integration test cases for the ping route."""

import pytest
from fastapi.testclient import TestClient

from app import api


@pytest.fixture
def client() -> TestClient:
    """Fixture to create a test client for the FastAPI application."""
    return TestClient(api)


@pytest.mark.integration
async def test_ready(client: TestClient) -> None:
    """Should return OK."""
    resp = client.get("/ping")
    assert resp.status_code == 200
    text = resp.text
    assert "OK" in text
