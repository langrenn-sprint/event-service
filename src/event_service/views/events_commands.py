"""Resource module for events resources."""
import os

from aiohttp import hdrs
from aiohttp.web import (
    HTTPBadRequest,
    HTTPNotFound,
    HTTPUnprocessableEntity,
    Response,
    View,
)
from dotenv import load_dotenv
from multidict import MultiDict

from event_service.adapters import UsersAdapter
from event_service.commands import EventsCommands
from event_service.services import (
    AgeclassCreateException,
    AgeclassNotUniqueNameException,
    AgeclassUpdateException,
    EventNotFoundException,
)
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class EventGenerateAgeclassesView(View):
    """Class representing the generate ageclasses commands resources."""

    async def post(self) -> Response:
        """Post route function."""
        # Authorize:
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        # Execute command:
        event_id = self.request.match_info["eventId"]
        try:
            await EventsCommands.generate_ageclasses(db, event_id)
        except EventNotFoundException:
            raise HTTPNotFound()
        except AgeclassNotUniqueNameException:
            raise HTTPUnprocessableEntity()
        except (AgeclassCreateException, AgeclassUpdateException):
            raise HTTPBadRequest()
        headers = MultiDict({hdrs.LOCATION: f"{BASE_URL}/events/{event_id}/ageclasses"})
        return Response(status=201, headers=headers)
