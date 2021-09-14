"""Resource module for ageclasses resources."""
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
from event_service.models import Ageclass
from event_service.services import (
    AgeclassesService,
    AgeclassNotFoundException,
    IllegalValueException,
)
from .utils import extract_token_from_request


load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class AgeclassesView(View):
    """Class representing ageclasses resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        event_id = self.request.match_info["eventId"]
        if "name" in self.request.rel_url.query:
            name = self.request.rel_url.query["name"]
            ageclasses = await AgeclassesService.get_ageclass_by_name(
                db, event_id, name
            )
        else:
            ageclasses = await AgeclassesService.get_all_ageclasses(db, event_id)

        list = []
        for a in ageclasses:
            list.append(a.to_dict())
        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        event_id = self.request.match_info["eventId"]

        body = await self.request.json()
        logging.debug(f"Got create request for ageclass {body} of type {type(body)}")

        try:
            ageclass = Ageclass.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            )

        try:
            ageclass_id = await AgeclassesService.create_ageclass(
                db, event_id, ageclass
            )
        except IllegalValueException:
            raise HTTPUnprocessableEntity()
        if ageclass_id:
            logging.debug(f"inserted document with id {ageclass_id}")
            headers = MultiDict(
                {
                    hdrs.LOCATION: f"{BASE_URL}/events/{event_id}/ageclasses/{ageclass_id}"
                }
            )  # noqa: B950

            return Response(status=201, headers=headers)
        raise HTTPBadRequest()  # pragma: no cover

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e

        event_id = self.request.match_info["eventId"]
        await AgeclassesService.delete_all_ageclasses(db, event_id)

        return Response(status=204)


class AgeclassView(View):
    """Class representing a single ageclass resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        event_id = self.request.match_info["eventId"]
        ageclass_id = self.request.match_info["ageclassId"]
        logging.debug(f"Got get request for ageclass {ageclass_id}")

        try:
            ageclass = await AgeclassesService.get_ageclass_by_id(
                db, event_id, ageclass_id
            )
        except AgeclassNotFoundException:
            raise HTTPNotFound()
        logging.debug(f"Got ageclass: {ageclass}")
        body = ageclass.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        body = await self.request.json()
        event_id = self.request.match_info["eventId"]
        ageclass_id = self.request.match_info["ageclassId"]
        logging.debug(f"Got request-body {body} for {ageclass_id} of type {type(body)}")

        try:
            ageclass = Ageclass.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            )

        try:
            await AgeclassesService.update_ageclass(db, event_id, ageclass_id, ageclass)
        except IllegalValueException:
            raise HTTPUnprocessableEntity()
        except AgeclassNotFoundException:
            raise HTTPNotFound()
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        event_id = self.request.match_info["eventId"]
        ageclass_id = self.request.match_info["ageclassId"]
        logging.debug(f"Got delete request for ageclass {ageclass_id}")

        try:
            await AgeclassesService.delete_ageclass(db, event_id, ageclass_id)
        except AgeclassNotFoundException:
            raise HTTPNotFound()
        return Response(status=204)
