"""Integration test cases for the ready route."""

import pytest
from aiohttp.test_utils import TestClient as _TestClient


@pytest.mark.integration
async def test_ready(client: _TestClient) -> None:
    """Should return OK."""
    resp = await client.get("/ready")
    assert resp.status == 200
    text = await resp.text()
    assert "OK" in text
