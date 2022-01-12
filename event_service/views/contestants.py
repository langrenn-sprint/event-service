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
    ContestantAllreadyExistException,
    ContestantNotFoundException,
    ContestantsService,
    EventNotFoundException,
    IllegalValueException,
    RaceclassNotFoundException,
)
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class ContestantsView(View):
    """Class representing contestants resource."""

    async def get(self) -> Response:  # noqa: C901
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e from e

        event_id = self.request.match_info["eventId"]
        if "raceclass" in self.request.rel_url.query:
            raceclass = self.request.rel_url.query["raceclass"]
            try:
                contestants = await ContestantsService.get_contestants_by_raceclass(
                    db, event_id, raceclass
                )
            except RaceclassNotFoundException as e:
                raise HTTPBadRequest(reason=str(e)) from e
        elif "ageclass" in self.request.rel_url.query:
            ageclass = self.request.rel_url.query["ageclass"]
            contestants = await ContestantsService.get_contestants_by_ageclass(
                db, event_id, ageclass
            )
        elif "bib" in self.request.rel_url.query:
            bib_param = self.request.rel_url.query["bib"]
            try:
                bib = int(bib_param)
            except ValueError as e:
                raise HTTPBadRequest(
                    reason=f"Query-param bib {bib_param} must be a valid int."
                ) from e
            contestants = await ContestantsService.get_contestant_by_bib(
                db, event_id, bib
            )
        else:
            contestants = await ContestantsService.get_all_contestants(db, event_id)

        list = []
        for _c in contestants:
            list.append(_c.to_dict())

        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:  # noqa: C901
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e from e

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
                ) from e

            try:
                contestant_id = await ContestantsService.create_contestant(
                    db, event_id, contestant
                )
            except EventNotFoundException as e:
                raise HTTPNotFound(reason=str(e)) from e
            except IllegalValueException as e:
                raise HTTPUnprocessableEntity(reason=str(e)) from e
            except ContestantAllreadyExistException as e:
                raise HTTPBadRequest(reason=str(e)) from e

            if contestant_id:
                logging.debug(f"inserted document with contestant_id {contestant_id}")
                headers = MultiDict(
                    [
                        (
                            hdrs.LOCATION,
                            f"{BASE_URL}/events/{event_id}/contestants/{contestant_id}",  # noqa: B950
                        )
                    ]
                )
                return Response(status=201, headers=headers)
            else:
                raise HTTPBadRequest() from None

        elif "multipart/form-data" in self.request.headers[hdrs.CONTENT_TYPE]:
            async for part in (await self.request.multipart()):
                logging.debug(f"part.name {part.name}.")
                if "text/csv" in part.headers[hdrs.CONTENT_TYPE]:
                    # process csv:
                    contestants = (await part.read()).decode()
                else:
                    raise HTTPBadRequest(
                        reason=f"File's content-type {part.headers[hdrs.CONTENT_TYPE]} not supported."  # noqa: B950
                    ) from None
                try:
                    result = await ContestantsService.create_contestants(
                        db, event_id, contestants
                    )
                except EventNotFoundException as e:
                    raise HTTPNotFound(reason=str(e)) from e

                logging.debug(f"result:\n {result}")
                body = json.dumps(result)
                return Response(status=200, body=body, content_type="application/json")

        elif "text/csv" in self.request.headers[hdrs.CONTENT_TYPE]:
            content = await self.request.content.read()
            contestants = content.decode()
            try:
                result = await ContestantsService.create_contestants(
                    db, event_id, contestants
                )
            except EventNotFoundException as e:
                raise HTTPNotFound(reason=str(e)) from e
            logging.debug(f"result:\n {result}")
            body = json.dumps(result)
            return Response(status=200, body=body, content_type="application/json")
        else:
            pass

        raise HTTPUnsupportedMediaType(
            reason=f"multipart/* content type expected, got {self.request.headers[hdrs.CONTENT_TYPE]}."  # noqa: B950
        ) from None

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e from e

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
            raise e from e

        event_id = self.request.match_info["eventId"]
        contestant_id = self.request.match_info["contestantId"]
        logging.debug(f"Got get request for contestant {contestant_id}")

        try:
            contestant = await ContestantsService.get_contestant_by_id(
                db, event_id, contestant_id
            )
        except ContestantNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
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
            raise e from e

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
            ) from e

        try:
            await ContestantsService.update_contestant(
                db, event_id, contestant_id, contestant
            )
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except ContestantNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "contestant-admin"])
        except Exception as e:
            raise e from e

        event_id = self.request.match_info["eventId"]
        contestant_id = self.request.match_info["contestantId"]
        logging.debug(
            f"Got delete request for contestant {contestant_id} in event {event_id}"
        )

        try:
            await ContestantsService.delete_contestant(db, event_id, contestant_id)
        except ContestantNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
