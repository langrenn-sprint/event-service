"""Resource module for ageclasses resources."""
import json
import logging
import os
from typing import Optional

from aiohttp import hdrs
from aiohttp.web import HTTPBadRequest, HTTPNotFound, Response, View
from dotenv import load_dotenv
from multidict import MultiDict

from event_service.adapters import AgeclassesAdapter, UsersAdapter
from .utils import extract_token_from_request


load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class Ageclasses(View):
    """Class representing ageclasses resource."""

    async def get(self) -> Response:
        """Get route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        ageclasses = await AgeclassesAdapter.get_all_ageclasses(self.request.app["db"])

        body = json.dumps(ageclasses, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:
        """Post route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        body = await self.request.json()
        logging.debug(f"Got create request for ageclass {body} of type {type(body)}")

        id = await AgeclassesAdapter.create_ageclass(self.request.app["db"], body)
        if id:
            logging.debug(f"inserted document with id {id}")
            headers = MultiDict({hdrs.LOCATION: f"{BASE_URL}/ageclasses/{id}"})

            return Response(status=201, headers=headers)
        raise HTTPBadRequest()  # pragma: no cover


class Ageclass(View):
    """Class representing a single ageclass resource."""

    async def get(self) -> Response:
        """Get route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        id = self.request.match_info["id"]
        logging.debug(f"Got get request for ageclass {id}")

        ageclass: Optional[dict] = await AgeclassesAdapter.get_ageclass(
            self.request.app["db"], id
        )
        logging.debug(f"Got ageclass: {ageclass}")
        if ageclass:
            body = json.dumps(ageclass, default=str, ensure_ascii=False)
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

        id = await AgeclassesAdapter.update_ageclass(self.request.app["db"], id, body)
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
        logging.debug(f"Got delete request for ageclass {id}")

        id = await AgeclassesAdapter.delete_ageclass(self.request.app["db"], id)
        if id:
            return Response(status=204)
        raise HTTPNotFound()
