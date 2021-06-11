"""Resource module for events resources."""
import json
import logging
import os
from typing import Optional

from aiohttp import hdrs
from aiohttp.web import HTTPBadRequest, HTTPNotFound, Response, View
from dotenv import load_dotenv
from multidict import MultiDict

from event_service.adapters import EventsAdapter


load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT")
if HOST_PORT:
    BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"
else:  # pragma: no cover
    BASE_URL = f"http://{HOST_SERVER}"


class Events(View):
    """Class representing events resource."""

    async def get(self) -> Response:
        """Get route function."""
        logging.debug("Got get all events request")
        events = await EventsAdapter.get_all_events(self.request.app["db"])

        body = json.dumps(events, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:
        """Post route function."""
        body = await self.request.json()
        logging.debug(f"Got create request for event {body} of type {type(body)}")

        id = await EventsAdapter.create_event(self.request.app["db"], body)
        if id:
            logging.debug(f"inserted document with id {id}")
            headers = MultiDict({hdrs.LOCATION: f"{BASE_URL}/events/{id}"})

            return Response(status=201, headers=headers)
        return HTTPBadRequest  # pragma: no cover


class Event(View):
    """Class representing a single event resource."""

    async def get(self) -> Response:
        """Get route function."""
        id = self.request.match_info["id"]
        logging.debug(f"Got get request for event {id}")

        event: Optional[dict] = await EventsAdapter.get_event(
            self.request.app["db"], id
        )
        logging.debug(f"Got event: {event}")
        if event:
            body = json.dumps(event, default=str, ensure_ascii=False)
            return Response(status=200, body=body, content_type="application/json")
        raise HTTPNotFound

    async def put(self) -> Response:
        """Put route function."""
        body = await self.request.json()
        id = self.request.match_info["id"]
        logging.debug(f"Got request-body {body} for {id} of type {type(body)}")

        id = await EventsAdapter.update_event(self.request.app["db"], id, body)
        if id:
            return Response(status=204)
        raise HTTPNotFound

    async def delete(self) -> Response:
        """Delete route function."""
        id = self.request.match_info["id"]
        logging.debug(f"Got delete request for event {id}")

        id = await EventsAdapter.delete_event(self.request.app["db"], id)
        if id:
            return Response(status=204)
        raise HTTPNotFound
