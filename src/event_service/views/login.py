"""Resource module for liveness resources."""
import json
import os

from aiohttp import web
from dotenv import load_dotenv

from event_service.security import create_access_token


load_dotenv()
CONFIG = os.getenv("CONFIG", "production")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 20

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


class Login(web.View):
    """Class representing login resource."""

    async def post(self) -> web.Response:
        """Login route function."""
        try:
            body = await self.request.json()
        except json.decoder.JSONDecodeError:
            raise web.HTTPBadRequest(reason="Invalid data in request body.")

        username = body.get("username", None)
        password = body.get("password", None)

        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            raise web.HTTPUnauthorized()

        jwt_token = create_access_token(identity=username)

        return web.json_response({"token": jwt_token})
