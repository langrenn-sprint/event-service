"""Resource module for raceclass results resources."""

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
from event_service.models import RaceclassResult
from event_service.services import ResultNotFoundException, ResultsService
from event_service.utils.jwt_utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class RaceclassResultsView(View):
    """Class representing raceclass results resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        event_id = self.request.match_info["eventId"]
        logging.debug(f"Got get request for event results {event_id}")

        results = await ResultsService.get_all_results(db, event_id)
        list = []
        for result in results:
            list.append(result.to_dict())

        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        event_id = self.request.match_info["eventId"]
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        logging.debug(f"Got create request for result {body} of type {type(body)}")
        try:
            result = RaceclassResult.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            result_id = await ResultsService.create_result(db, event_id, result)
        except Exception as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        if result_id:
            logging.debug(f"inserted document with result_id {result_id}")
            headers = MultiDict(
                [
                    (
                        hdrs.LOCATION,
                        f"{BASE_URL}/events/{result.event_id}/results/{result_id}",
                    )
                ]
            )

            return Response(status=201, headers=headers)
        raise HTTPBadRequest() from None


class RaceclassResultView(View):
    """Class representing raceclass result resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        event_id = self.request.match_info["eventId"]
        raceclass = self.request.match_info["raceclass"]
        logging.debug(f"Got get request for event/raceclass {event_id}/{raceclass}")

        try:
            result = await ResultsService.get_result_by_raceclass(
                db, event_id, raceclass
            )
        except ResultNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e

        body = result.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        event_id = self.request.match_info["eventId"]
        raceclass = self.request.match_info["raceclass"]
        logging.debug(f"Got delete request for result {raceclass}")

        try:
            await ResultsService.delete_result(db, event_id, raceclass)
        except ResultNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
