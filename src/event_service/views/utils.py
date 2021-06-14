"""Module for view utilities functions."""
from typing import Optional

from aiohttp import web


def extract_token_from_request(request: web.Request) -> Optional[str]:
    """Extract jwt_token from authorization header in request."""
    jwt_token = None
    authorization = request.headers.get("authorization", None)
    if authorization:
        jwt_token = str.replace(str(authorization), "Bearer ", "")

    return jwt_token
