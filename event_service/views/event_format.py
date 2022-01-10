"""Resource module for event specific format resources."""
import logging
import os
from typing import Union

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
from event_service.models import (
    IndividualSprintFormat,
    IntervalStartFormat,
)
from event_service.services import (
    EventFormatNotFoundException,
    EventFormatService,
    EventNotFoundException,
)
from .utils import extract_token_from_request


load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class EventFormatView(View):
    """Class representing event_format resource."""

    async def post(self) -> Response:
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        event_id = self.request.match_info["eventId"]

        body = await self.request.json()
        logging.debug(
            f"Got create request for event_format {body} of type {type(body)}"
        )

        try:
            event_format: Union[IndividualSprintFormat, IntervalStartFormat]
            if body["datatype"] == "interval_start":
                event_format = IntervalStartFormat.from_dict(body)
            elif body["datatype"] == "individual_sprint":
                event_format = IndividualSprintFormat.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            event_format_id = await EventFormatService.create_event_format(
                db, event_id, event_format
            )
        except EventNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        if event_format_id:
            logging.debug(f"inserted document with id {event_format_id}")
            headers = MultiDict(
                [(hdrs.LOCATION, f"{BASE_URL}/events/{event_id}/format")]
            )

            return Response(status=201, headers=headers)
        raise HTTPBadRequest() from None  # pragma: no cover

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        event_id = self.request.match_info["eventId"]
        logging.debug(f"Got get request for event_format for event {event_id}")

        try:
            event_format = await EventFormatService.get_event_format(db, event_id)
        except EventFormatNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        logging.debug(f"Got event_format: {event_format}")
        body = event_format.to_json()
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
        logging.debug(
            f"Got request-body {body} for format of {event_id} of type {type(body)}"
        )

        try:
            event_format: Union[IndividualSprintFormat, IntervalStartFormat]
            if body["datatype"] == "interval_start":
                event_format = IntervalStartFormat.from_dict(body)
            elif body["datatype"] == "individual_sprint":
                event_format = IndividualSprintFormat.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await EventFormatService.update_event_format(db, event_id, event_format)
        except EventFormatNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
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
        logging.debug(f"Got delete request for event_format for event {event_id}")

        try:
            await EventFormatService.delete_event_format(db, event_id)
        except EventFormatNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
