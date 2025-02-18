"""Module for users adapter."""

import os
from http import HTTPStatus
from typing import Any

from aiohttp import ClientSession
from aiohttp.web import (
    HTTPForbidden,
    HTTPInternalServerError,
    HTTPUnauthorized,
)

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER", "users.example.com")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT", "8080")


class UsersAdapter:
    """Class representing an adapter for events."""

    @classmethod
    async def authorize(cls: Any, token: str | None, roles: list) -> None:
        """Try to authorize."""
        url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize"
        body = {"token": token, "roles": roles}

        async with ClientSession() as session, session.post(url, json=body) as response:
            if response.status == HTTPStatus.NO_CONTENT:
                pass
            elif response.status == HTTPStatus.UNAUTHORIZED:
                raise HTTPUnauthorized from None
            elif response.status == HTTPStatus.FORBIDDEN:
                raise HTTPForbidden from None
            else:  # pragma: no cover
                raise HTTPInternalServerError(
                    reason=f"Got unknown status from users service: {response.status}."
                ) from None
