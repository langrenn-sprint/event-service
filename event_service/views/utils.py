"""Utilities module for events resources."""

from typing import Optional

from aiohttp.web import Request


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract jwt_token from authorization header in request."""
    jwt_token = None
    authorization = request.headers.getone("authorization", None)
    if authorization:
        jwt_token = str.replace(str(authorization), "Bearer ", "")

    return jwt_token
