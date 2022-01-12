"""Module for users adapter."""
import os
from typing import Any, Optional

from aiohttp import ClientSession
from aiohttp.web import (
    HTTPForbidden,
    HTTPInternalServerError,
    HTTPUnauthorized,
)


USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


class UsersAdapter:
    """Class representing an adapter for events."""

    @classmethod
    async def authorize(cls: Any, token: Optional[str], roles: list) -> None:
        """Try to authorize."""
        url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize"
        body = {"token": token, "roles": roles}

        async with ClientSession() as session:
            async with session.post(url, json=body) as response:
                if response.status == 204:
                    pass
                elif response.status == 401:
                    raise HTTPUnauthorized() from None
                elif response.status == 403:
                    raise HTTPForbidden() from None
                else:
                    raise HTTPInternalServerError(
                        reason=f"Got unknown status from users service: {response.status}."
                    ) from None
