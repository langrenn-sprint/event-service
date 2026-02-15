"""Module for competition_format adapter."""

import logging
import os
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

from httpx import AsyncClient
from pydantic import TypeAdapter

from app.models import CompetitionFormatUnion

COMPETITION_FORMAT_HOST_SERVER = os.getenv(
    "COMPETITION_FORMAT_HOST_SERVER", "competition-format.example.com"
)
COMPETITION_FORMAT_HOST_PORT = os.getenv("COMPETITION_FORMAT_HOST_PORT", "8080")


class CompetitionFormatsAdapterError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class CompetitionFormatsAdapter:
    """Class representing an adapter for competition_formats."""

    logger: logging.Logger

    @classmethod
    async def init(cls) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.logger = logging.getLogger("uvicorn.error")

    @classmethod
    async def get_competition_formats_by_name(
        cls: Any, competition_format_name: str
    ) -> list[CompetitionFormatUnion]:  # pragma: no cover
        """Get competition_format by name function."""
        url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"

        async with AsyncClient() as client:
            query_param = f"name={quote(competition_format_name)}"
            response = await client.get(f"{url}?{query_param}")
            if response.status_code == HTTPStatus.OK:
                competition_formats_response = response.json()
            else:
                msg = f"Got unknown status {response.status_code} from competition_formats service."
                raise CompetitionFormatsAdapterError(msg)

        return [
            TypeAdapter(CompetitionFormatUnion).validate_python(competition_format)
            for competition_format in competition_formats_response
        ]
