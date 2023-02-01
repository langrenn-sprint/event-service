"""Resource module for raceclasses resources."""
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
from event_service.models import Raceclass
from event_service.services import (
    EventNotFoundException,
    IllegalValueException,
    RaceclassesService,
    RaceclassNotFoundException,
)
from event_service.utils.jwt_utils import extract_token_from_request


load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class RaceclassesView(View):
    """Class representing raceclasses resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        event_id = self.request.match_info["eventId"]
        if "name" in self.request.rel_url.query:
            name = self.request.rel_url.query["name"]
            raceclasses = await RaceclassesService.get_raceclass_by_name(
                db, event_id, name
            )
        elif "ageclass-name" in self.request.rel_url.query:
            ageclass_name = self.request.rel_url.query["ageclass-name"]
            raceclasses = await RaceclassesService.get_raceclass_by_ageclass_name(
                db, event_id, ageclass_name
            )
        else:
            raceclasses = await RaceclassesService.get_all_raceclasses(db, event_id)

        list = []
        for race in raceclasses:
            list.append(race.to_dict())
        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

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
        logging.debug(f"Got create request for raceclass {body} of type {type(body)}")

        try:
            raceclass = Raceclass.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            raceclass_id = await RaceclassesService.create_raceclass(
                db, event_id, raceclass
            )
        except EventNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        if raceclass_id:
            logging.debug(f"inserted document with id {raceclass_id}")
            headers = MultiDict(
                [
                    (
                        hdrs.LOCATION,
                        f"{BASE_URL}/events/{event_id}/raceclasses/{raceclass_id}",
                    )
                ]
            )

            return Response(status=201, headers=headers)
        raise HTTPBadRequest() from None  # pragma: no cover

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        event_id = self.request.match_info["eventId"]
        await RaceclassesService.delete_all_raceclasses(db, event_id)

        return Response(status=204)


class RaceclassView(View):
    """Class representing a single raceclass resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        event_id = self.request.match_info["eventId"]
        raceclass_id = self.request.match_info["raceclassId"]
        logging.debug(f"Got get request for raceclass {raceclass_id}")

        try:
            raceclass = await RaceclassesService.get_raceclass_by_id(
                db, event_id, raceclass_id
            )
        except RaceclassNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        logging.debug(f"Got raceclass: {raceclass}")
        body = raceclass.to_json()
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
        raceclass_id = self.request.match_info["raceclassId"]
        logging.debug(
            f"Got request-body {body} for {raceclass_id} of type {type(body)}"
        )

        try:
            raceclass = Raceclass.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await RaceclassesService.update_raceclass(
                db, event_id, raceclass_id, raceclass
            )
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except RaceclassNotFoundException as e:
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
        raceclass_id = self.request.match_info["raceclassId"]
        logging.debug(f"Got delete request for raceclass {raceclass_id}")

        try:
            await RaceclassesService.delete_raceclass(db, event_id, raceclass_id)
        except RaceclassNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
