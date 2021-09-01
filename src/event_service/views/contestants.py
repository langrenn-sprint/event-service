"""Resource module for contestants resources."""
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
from event_service.models import Contestant
from event_service.services import (
    ContestantNotFoundException,
    ContestantsService,
    IllegalValueException,
)
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class ContestantsView(View):
    """Class representing contestants resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e

        contestants = await ContestantsService.get_all_contestants(db)

        body = json.dumps(contestants, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e

        body = await self.request.json()
        logging.debug(f"Got create request for contestant {body} of type {type(body)}")
        try:
            contestant = Contestant.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            )

        try:
            id = await ContestantsService.create_contestant(db, contestant)
        except IllegalValueException:
            raise HTTPUnprocessableEntity()
        if id:
            logging.debug(f"inserted document with id {id}")
            headers = MultiDict({hdrs.LOCATION: f"{BASE_URL}/contestants/{id}"})

            return Response(status=201, headers=headers)
        raise HTTPBadRequest()


class ContestantView(View):
    """Class representing a single contestant resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e

        id = self.request.match_info["id"]
        logging.debug(f"Got get request for contestant {id}")

        try:
            contestant = await ContestantsService.get_contestant_by_id(db, id)
        except ContestantNotFoundException:
            raise HTTPNotFound()
        logging.debug(f"Got contestant: {contestant}")
        body = contestant.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e

        body = await self.request.json()
        id = self.request.match_info["id"]
        logging.debug(f"Got request-body {body} for {id} of type {type(body)}")
        body = await self.request.json()
        logging.debug(f"Got create request for contestant {body} of type {type(body)}")
        try:
            contestant = Contestant.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            )

        id = self.request.match_info["id"]
        logging.debug(f"Got request-body {body} for {id} of type {type(body)}")
        try:
            id = await ContestantsService.update_contestant(db, id, contestant)
        except IllegalValueException:
            raise HTTPUnprocessableEntity()
        except ContestantNotFoundException:
            raise HTTPNotFound()
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e

        id = self.request.match_info["id"]
        logging.debug(f"Got delete request for contestant {id}")

        try:
            await ContestantsService.delete_contestant(db, id)
        except ContestantNotFoundException:
            raise HTTPNotFound()
        return Response(status=204)
