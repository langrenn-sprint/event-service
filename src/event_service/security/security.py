"""Module for security functions."""
from datetime import datetime, timedelta
import logging
import os
from typing import Optional

import jwt

JWT_SECRET: Optional[str] = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 60


def valid_token(token: Optional[str]) -> bool:
    """Extract jwt from authorization header and decode it."""
    logging.debug(f"Got jwt_token {token}")
    try:
        _ = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])  # type: ignore
        return True
    except (jwt.DecodeError, jwt.ExpiredSignatureError) as e:
        logging.debug(f"Got excpetion {e}")
    return False


def create_access_token(identity: str) -> bytes:
    """Create a jwt based on identity."""
    payload = {
        "identity": identity,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS),
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)  # type: ignore

    return jwt_token
