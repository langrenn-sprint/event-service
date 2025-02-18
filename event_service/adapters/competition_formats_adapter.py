"""Module for competition_format adapter."""

import logging
import os
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

from aiohttp import ClientSession

from .adapter import Adapter

COMPETITION_FORMAT_HOST_SERVER = os.getenv("COMPETITION_FORMAT_HOST_SERVER", "competition-format.example.com")
COMPETITION_FORMAT_HOST_PORT = os.getenv("COMPETITION_FORMAT_HOST_PORT", "8080")


class CompetitionFormatsAdapterError(Exception):
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
    ) -> list[dict]:  # pragma: no cover
        """Get competition_format by name function."""
        _ = db
        logging.debug(f"Got request for name {competition_format_name}.")
        competition_formats: list = []

        url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"

        async with ClientSession() as session:
            query_param = f"name={quote(competition_format_name)}"
            async with session.get(f"{url}?{query_param}") as response:
                if response.status == HTTPStatus.OK:
                    competition_formats_response = await response.json()
                else:
                    msg = f"Got unknown status {response.status} from competition_formats service."
                    raise CompetitionFormatsAdapterError(msg)

        for competition_format in competition_formats_response:
            logging.debug(f"cursor - competition_format: {competition_format}")
            competition_formats.append(competition_format)

        return competition_formats
