"""Resource module for events resources."""
import json
import logging
import os
from typing import Optional

from aiohttp import hdrs
from aiohttp.web import (
    HTTPBadRequest,
    HTTPNotFound,
    Request,
    Response,
    View,
)
from dotenv import load_dotenv
from multidict import MultiDict

from event_service.adapters import EventsAdapter, UsersAdapter


load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract jwt_token from authorization header in request."""
    jwt_token = None
    authorization = request.headers.get("authorization", None)
    if authorization:
        jwt_token = str.replace(str(authorization), "Bearer ", "")

    return jwt_token


class Events(View):
    """Class representing events resource."""

    async def get(self) -> Response:
        """Get route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        events = await EventsAdapter.get_all_events(self.request.app["db"])

        body = json.dumps(events, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:
        """Post route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        body = await self.request.json()
        logging.debug(f"Got create request for event {body} of type {type(body)}")

        # TODO: consider using a model to do validation on the body before creation

        id = await EventsAdapter.create_event(self.request.app["db"], body)
        if id:
            logging.debug(f"inserted document with id {id}")
            headers = MultiDict({hdrs.LOCATION: f"{BASE_URL}/events/{id}"})

            return Response(status=201, headers=headers)
        raise HTTPBadRequest()  # pragma: no cover


class Event(View):
    """Class representing a single event resource."""

    async def get(self) -> Response:
        """Get route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        id = self.request.match_info["id"]
        logging.debug(f"Got get request for event {id}")

        event: Optional[dict] = await EventsAdapter.get_event(
            self.request.app["db"], id
        )
        logging.debug(f"Got event: {event}")
        if event:
            body = json.dumps(event, default=str, ensure_ascii=False)
            return Response(status=200, body=body, content_type="application/json")
        raise HTTPNotFound()

    async def put(self) -> Response:
        """Put route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        body = await self.request.json()
        id = self.request.match_info["id"]
        logging.debug(f"Got request-body {body} for {id} of type {type(body)}")

        id = await EventsAdapter.update_event(self.request.app["db"], id, body)
        if id:
            return Response(status=204)
        raise HTTPNotFound()

    async def delete(self) -> Response:
        """Delete route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        id = self.request.match_info["id"]
        logging.debug(f"Got delete request for event {id}")

        id = await EventsAdapter.delete_event(self.request.app["db"], id)
        if id:
            return Response(status=204)
        raise HTTPNotFound()
