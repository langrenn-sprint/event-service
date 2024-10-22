"""Resource module for events resources."""

import json
import os

from aiohttp.web import (
    HTTPBadRequest,
    Response,
    View,
)
from dotenv import load_dotenv

from event_service.adapters import ContestantsAdapter

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class ContestantsSearchView(View):
    """Class representing the search resources."""

    async def post(self) -> Response:
        """Post search function."""
        db = self.request.app["db"]

        query = None
        try:
            event_id = self.request.match_info["eventId"]
            query = await self.request.json()

            name = query["name"]
            _result = await ContestantsAdapter.search_contestants_in_event_by_name(
                db, event_id, name
            )
        except json.JSONDecodeError as e:  # pragma: no cover
            raise HTTPBadRequest(reason="Query is invalid json.") from e
        except ValueError as e:  # pragma: no cover
            raise HTTPBadRequest(reason=f"Invalid query: {query}.") from e

        body = json.dumps(_result, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")
