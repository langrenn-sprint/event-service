"""Resource module for events resources."""

import json
import logging
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
from event_service.models import Event
from event_service.services import (
    CompetitionFormatNotFoundError,
    EventNotFoundError,
    EventsService,
    IllegalValueError,
    InvalidDateFormatError,
    InvalidTimezoneError,
)
from event_service.utils.jwt_utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class EventsView(View):
    """Class representing events resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        events = await EventsService.get_all_events(db)
        event_list = [event.to_dict() for event in events]

        body = json.dumps(event_list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        logging.debug(f"Got create request for event {body} of type {type(body)}")
        try:
            event = Event.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            event_id = await EventsService.create_event(db, event)
        except (IllegalValueError, InvalidTimezoneError) as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except (CompetitionFormatNotFoundError, InvalidDateFormatError) as e:
            raise HTTPBadRequest(reason=str(e)) from e
        if event_id:
            logging.debug(f"inserted document with event_id {event_id}")
            headers = MultiDict([(hdrs.LOCATION, f"{BASE_URL}/events/{event_id}")])

            return Response(status=201, headers=headers)
        raise HTTPBadRequest from None


class EventView(View):
    """Class representing a single event resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        event_id = self.request.match_info["eventId"]
        logging.debug(f"Got get request for event {event_id}")

        try:
            event = await EventsService.get_event_by_id(db, event_id)
        except EventNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        logging.debug(f"Got event: {event}")
        body = event.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        event_id = self.request.match_info["eventId"]
        logging.debug(f"Got request-body {body} for {event_id} of type {type(body)}")
        body = await self.request.json()
        logging.debug(f"Got put request for event {body} of type {type(body)}")
        try:
            event = Event.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await EventsService.update_event(db, event_id, event)
        except IllegalValueError as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except EventNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        except (CompetitionFormatNotFoundError, InvalidDateFormatError) as e:
            raise HTTPBadRequest(reason=str(e)) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        event_id = self.request.match_info["eventId"]
        logging.debug(f"Got delete request for event {event_id}")

        try:
            await EventsService.delete_event(db, event_id)
        except EventNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
