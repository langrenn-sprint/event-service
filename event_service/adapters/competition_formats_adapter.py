"""Module for competition_format adapter."""

import logging
import os
from typing import Any, List
from urllib.parse import quote

from aiohttp import ClientSession

from .adapter import Adapter


COMPETITION_FORMAT_HOST_SERVER = os.getenv("COMPETITION_FORMAT_HOST_SERVER")
COMPETITION_FORMAT_HOST_PORT = os.getenv("COMPETITION_FORMAT_HOST_PORT")


class CompetitionFormatsAdapterException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


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
                if response.status == 200:
                    competition_formats_response = await response.json()
                else:
                    raise CompetitionFormatsAdapterException(
                        f"Got unknown status {response.status} from competition_formats service."  # noqa: B950
                    )  # noqa: B950

        for competition_format in competition_formats_response:
            logging.debug(f"cursor - competition_format: {competition_format}")
            competition_formats.append(competition_format)

        return competition_formats
