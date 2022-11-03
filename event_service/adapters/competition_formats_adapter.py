"""Module for competition_format adapter."""
import logging
import os
from typing import Any, List
from urllib.parse import quote

from aiohttp import ClientSession

from .adapter import Adapter


COMPETITION_FORMAT_HOST_SERVER = os.getenv("COMPETITION_FORMAT_HOST_SERVER")
COMPETITION_FORMAT_HOST_PORT = os.getenv("COMPETITION_FORMAT_HOST_PORT")


class CompetitionFormatsAdapter(Adapter):
    """Class representing an adapter for competition_formats."""

    @classmethod
    async def get_competition_formats_by_name(
        cls: Any, db: Any, competition_format_name: str
    ) -> List[dict]:  # pragma: no cover
        """Get competition_format by name function."""
        logging.debug(f"Got request for name {competition_format_name}.")
        competition_formats: List = []

        url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"  # noqa: B950

        async with ClientSession() as session:
            query_param = f"name={quote(competition_format_name)}"
            async with session.get(f"{url}?{query_param}") as response:
                assert str(response.url) == f"{url}?name=Interval%20Start"
                body = await response.json()

        for competition_format in body:
            logging.debug(f"cursor - competition_format: {competition_format}")
            competition_formats.append(competition_format)

        return competition_formats
