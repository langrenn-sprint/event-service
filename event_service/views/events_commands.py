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
    EventNotFoundError,
    RaceclassCreateError,
    RaceclassNotUniqueNameError,
    RaceclassUpdateError,
)
from event_service.utils.jwt_utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class EventGenerateRaceclassesView(View):
    """Class representing the generate raceclasses commands resources."""

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
            await EventsCommands.generate_raceclasses(db, event_id)
        except EventNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        except RaceclassNotUniqueNameError as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except (RaceclassCreateError, RaceclassUpdateError) as e:
            raise HTTPBadRequest(reason=str(e)) from e
        headers = MultiDict(
            [(hdrs.LOCATION, f"{BASE_URL}/events/{event_id}/raceclasses")]
        )
        return Response(status=201, headers=headers)
