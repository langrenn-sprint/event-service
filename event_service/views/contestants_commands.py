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
    NoRaceclassInEventError,
    NoValueForGroupInRaceclassError,
    NoValueForOrderInRaceclassError,
)
from event_service.services import (
    EventNotFoundError,
    IllegalValueError,
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
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        # Check for the start-bib parameter:
        start_bib = None
        if "start-bib" in self.request.rel_url.query:
            start_bib_query = self.request.rel_url.query["start-bib"]
            try:
                start_bib = int(start_bib_query)
            except ValueError:  # pragma: no cover
                raise HTTPBadRequest(
                    reason=f"Invalid start-bib value: {start_bib_query}. Should be an integer."
                ) from None

        # Execute command:
        event_id = self.request.match_info["eventId"]
        try:
            await ContestantsCommands.assign_bibs(
                event_id, start_bib if start_bib else None
            )
        except (EventNotFoundError, NoRaceclassInEventError) as e:
            raise HTTPNotFound(reason=str(e)) from e
        except (
            NoValueForGroupInRaceclassError,
            NoValueForOrderInRaceclassError,
            IllegalValueError,
        ) as e:
            raise HTTPBadRequest(reason=str(e)) from e

        headers = MultiDict(
            [(hdrs.LOCATION, f"{BASE_URL}/events/{event_id}/contestants")]
        )
        return Response(status=201, headers=headers)
