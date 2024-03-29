"""Resource module for events resources."""
import os

from aiohttp import hdrs
from aiohttp.web import (
    HTTPBadRequest,
    HTTPNotFound,
    Response,
    View,
)
from dotenv import load_dotenv
from multidict import MultiDict

from event_service.adapters import UsersAdapter
from event_service.commands import (
    ContestantsCommands,
    NoRaceclassInEventException,
    NoValueForGroupInRaceclassExcpetion,
    NoValueForOrderInRaceclassExcpetion,
)
from event_service.services import (
    EventNotFoundException,
    IllegalValueException,
)
from event_service.utils.jwt_utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class ContestantsAssignBibsView(View):
    """Class representing the assign bibs to contestants commands resources."""

    async def post(self) -> Response:
        """Post route function."""
        # Authorize:
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        # Execute command:
        event_id = self.request.match_info["eventId"]
        try:
            await ContestantsCommands.assign_bibs(db, event_id)
        except (EventNotFoundException, NoRaceclassInEventException) as e:
            raise HTTPNotFound(reason=str(e)) from e
        except (
            NoValueForGroupInRaceclassExcpetion,
            NoValueForOrderInRaceclassExcpetion,
            IllegalValueException,
        ) as e:
            raise HTTPBadRequest(reason=str(e)) from e

        headers = MultiDict(
            [(hdrs.LOCATION, f"{BASE_URL}/events/{event_id}/contestants")]
        )
        return Response(status=201, headers=headers)
