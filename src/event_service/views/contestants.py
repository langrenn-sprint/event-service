"""Resource module for contestants resources."""
import json
import logging
import os

from aiohttp import hdrs
from aiohttp.web import (
    HTTPBadRequest,
    HTTPNotFound,
    HTTPUnprocessableEntity,
    HTTPUnsupportedMediaType,
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

        event_id = self.request.match_info["eventId"]
        contestants = await ContestantsService.get_all_contestants(db, event_id)

        body = json.dumps(contestants, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:  # noqa: C901
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e

        # handle application/json and text/csv:
        logging.debug(
            f"Got following content-type-headers: {self.request.headers[hdrs.CONTENT_TYPE]}."
        )
        event_id = self.request.match_info["eventId"]
        if "application/json" in self.request.headers[hdrs.CONTENT_TYPE]:
            body = await self.request.json()
            logging.debug(
                f"Got create request for contestant {body} of type {type(body)}"
            )
            try:
                contestant = Contestant.from_dict(body)
            except KeyError as e:
                raise HTTPUnprocessableEntity(
                    reason=f"Mandatory property {e.args[0]} is missing."
                )

            try:
                contestant_id = await ContestantsService.create_contestant(
                    db, event_id, contestant
                )
            except IllegalValueException:
                raise HTTPUnprocessableEntity()
            if contestant_id:
                logging.debug(f"inserted document with contestant_id {contestant_id}")
                headers = MultiDict(
                    {
                        hdrs.LOCATION: f"{BASE_URL}/events/{event_id}/contestants/{contestant_id}"  # noqa: B950
                    }
                )
            else:
                raise HTTPBadRequest()

        elif "multipart/form-data" in self.request.headers[hdrs.CONTENT_TYPE]:
            async for part in (await self.request.multipart()):
                logging.debug(f"part.name {part.name}.")
                if "text/csv" in part.headers[hdrs.CONTENT_TYPE]:
                    # process csv:
                    contestants = (await part.read()).decode()
                else:
                    raise HTTPBadRequest(
                        reason=f"File's content-type {part.headers[hdrs.CONTENT_TYPE]} not supported."  # noqa: B950
                    )
                result = await ContestantsService.create_contestants(
                    db, event_id, contestants
                )
                if result:
                    logging.debug(f"inserted {result} contestans.")
                    headers = MultiDict(
                        {hdrs.LOCATION: f"{BASE_URL}/events/{event_id}/contestants"}
                    )
                else:
                    raise HTTPBadRequest()
        else:
            raise HTTPUnsupportedMediaType(
                reason=f"multipart/* content type expected, got {hdrs.CONTENT_TYPE}."
            )
        return Response(status=201, headers=headers)

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e

        event_id = self.request.match_info["eventId"]
        await ContestantsService.delete_all_contestants(db, event_id)

        return Response(status=204)


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

        event_id = self.request.match_info["eventId"]
        contestant_id = self.request.match_info["contestantId"]
        logging.debug(f"Got get request for contestant {contestant_id}")

        try:
            contestant = await ContestantsService.get_contestant_by_id(
                db, event_id, contestant_id
            )
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
        event_id = self.request.match_info["eventId"]
        contestant_id = self.request.match_info["contestantId"]
        body = await self.request.json()
        logging.debug(
            f"Got request-body {body} for {contestant_id} of type {type(body)}"
        )

        try:
            contestant = Contestant.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            )

        try:
            await ContestantsService.update_contestant(
                db, event_id, contestant_id, contestant
            )
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

        event_id = self.request.match_info["eventId"]
        contestant_id = self.request.match_info["contestantId"]
        logging.debug(
            f"Got delete request for contestant {contestant_id} in event {event_id}"
        )

        try:
            await ContestantsService.delete_contestant(db, event_id, contestant_id)
        except ContestantNotFoundException:
            raise HTTPNotFound()
        return Response(status=204)
