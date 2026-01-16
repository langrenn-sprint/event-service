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
    BibAlreadyInUseError,
    ContestantAllreadyExistError,
    ContestantNotFoundError,
    ContestantsService,
    EventNotFoundError,
    IllegalValueError,
    RaceclassNotFoundError,
)
from event_service.utils.jwt_utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class ContestantsView(View):
    """Class representing contestants resource."""

    logger = logging.getLogger("event_service.views.contestants")

    async def get(self) -> Response:
        """Get route function."""
        event_id = self.request.match_info["eventId"]
        if "raceclass" in self.request.rel_url.query:
            raceclass = self.request.rel_url.query["raceclass"]
            try:
                contestants = await ContestantsService.get_contestants_by_raceclass(
                    event_id, raceclass
                )
            except RaceclassNotFoundError as e:
                raise HTTPBadRequest(reason=str(e)) from e
        elif "ageclass" in self.request.rel_url.query:
            ageclass = self.request.rel_url.query["ageclass"]
            contestants = await ContestantsService.get_contestants_by_ageclass(
                event_id, ageclass
            )
        elif "bib" in self.request.rel_url.query:
            bib_param = self.request.rel_url.query["bib"]
            try:
                bib = int(bib_param)
            except ValueError as e:
                raise HTTPBadRequest(
                    reason=f"Query-param bib {bib_param} must be a valid int."
                ) from e
            contestants = await ContestantsService.get_contestant_by_bib(event_id, bib)
        else:
            contestants = await ContestantsService.get_all_contestants(event_id)

        contestant_list = [contestant.to_dict() for contestant in contestants]
        body = json.dumps(contestant_list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:  # noqa: PLR0915, PLR0912, C901
        """Post route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(
                token, roles=["admin", "event-admin", "race-office"]
            )
        except Exception as e:
            raise e from e

        # handle application/json and text/csv:
        self.logger.debug(
            f"Got following content-type-headers: {self.request.headers[hdrs.CONTENT_TYPE]}."
        )
        event_id = self.request.match_info["eventId"]
        if "application/json" in self.request.headers[hdrs.CONTENT_TYPE]:
            body = await self.request.json()
            self.logger.debug(
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
                    event_id, contestant
                )
            except EventNotFoundError as e:
                raise HTTPNotFound(reason=str(e)) from e
            except IllegalValueError as e:
                raise HTTPUnprocessableEntity(reason=str(e)) from e
            except (BibAlreadyInUseError, ContestantAllreadyExistError) as e:
                raise HTTPBadRequest(reason=str(e)) from e

            if contestant_id:
                self.logger.debug(
                    f"inserted document with contestant_id {contestant_id}"
                )
                headers = MultiDict(
                    [
                        (
                            hdrs.LOCATION,
                            f"{BASE_URL}/events/{event_id}/contestants/{contestant_id}",
                        )
                    ]
                )
                return Response(status=201, headers=headers)
            raise HTTPBadRequest from None

        if "multipart/form-data" in self.request.headers[hdrs.CONTENT_TYPE]:
            async for part in await self.request.multipart():
                self.logger.debug(f"part.name {part.name}.")  # type: ignore [reportOptionalMemberAccess]
                if "text/csv" in part.headers[hdrs.CONTENT_TYPE]:  # type: ignore [reportOptionalMemberAccess]
                    # process csv:
                    contestants = (await part.read()).decode()  # type: ignore [reportAttributeAccessIssue]
                else:
                    raise HTTPBadRequest(
                        reason=f"File's content-type {part.headers[hdrs.CONTENT_TYPE]} not supported."  # type: ignore [reportAttributeAccessIssue]
                    ) from None
                try:
                    result = await ContestantsService.create_contestants(
                        event_id, contestants
                    )
                except EventNotFoundError as e:
                    raise HTTPNotFound(reason=str(e)) from e
                except IllegalValueError as e:
                    raise HTTPBadRequest(reason=str(e)) from e

                self.logger.debug(f"result:\n {result}")
                body = json.dumps(result)
                return Response(status=200, body=body, content_type="application/json")

        elif "text/csv" in self.request.headers[hdrs.CONTENT_TYPE]:
            content = await self.request.content.read()
            contestants = content.decode()
            try:
                result = await ContestantsService.create_contestants(
                    event_id, contestants
                )
            except EventNotFoundError as e:
                raise HTTPNotFound(reason=str(e)) from e
            self.logger.debug(f"result:\n {result}")
            body = json.dumps(result)
            return Response(status=200, body=body, content_type="application/json")
        else:
            pass

        raise HTTPUnsupportedMediaType(
            reason=f"multipart/* content type expected, got {self.request.headers[hdrs.CONTENT_TYPE]}."
        ) from None

    async def delete(self) -> Response:
        """Delete route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(
                token, roles=["admin", "event-admin", "race-office"]
            )
        except Exception as e:
            raise e from e

        event_id = self.request.match_info["eventId"]
        await ContestantsService.delete_all_contestants(event_id)

        return Response(status=204)


class ContestantView(View):
    """Class representing a single contestant resource."""

    logger = logging.getLogger("event_service.views.contestant")

    async def get(self) -> Response:
        """Get route function."""
        event_id = self.request.match_info["eventId"]
        contestant_id = self.request.match_info["contestantId"]
        self.logger.debug(f"Got get request for contestant {contestant_id}")

        try:
            contestant = await ContestantsService.get_contestant_by_id(
                event_id, contestant_id
            )
        except ContestantNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        self.logger.debug(f"Got contestant: {contestant}")
        body = contestant.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(
                token, roles=["admin", "event-admin", "race-office"]
            )
        except Exception as e:
            raise e from e

        body = await self.request.json()
        event_id = self.request.match_info["eventId"]
        contestant_id = self.request.match_info["contestantId"]
        body = await self.request.json()
        self.logger.debug(
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
                event_id, contestant_id, contestant
            )
        except IllegalValueError as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except ContestantNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        except BibAlreadyInUseError as e:
            raise HTTPBadRequest(reason=str(e)) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete route function."""
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        event_id = self.request.match_info["eventId"]
        contestant_id = self.request.match_info["contestantId"]
        self.logger.debug(
            f"Got delete request for contestant {contestant_id} in event {event_id}"
        )

        try:
            await ContestantsService.delete_contestant(event_id, contestant_id)
        except ContestantNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
