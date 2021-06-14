"""Unit test cases for the security module."""
import os
from typing import Optional

import jwt
import pytest

from event_service.security import create_access_token, valid_token


@pytest.mark.unit
async def test_valid_token() -> None:
    """Should return True."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "test_user"}
    token: Optional[str] = jwt.encode(payload, secret, algorithm)  # type: ignore

    assert valid_token(token)


@pytest.mark.unit
async def test_create_access_token() -> None:
    """Should return a token."""
    identity = "test_user"
    token = create_access_token(identity)
    assert token
    assert len(token) > 0
    secret = os.getenv("JWT_SECRET")
    jwt.decode(token, secret, algorithms="HS256")  # type: ignore
