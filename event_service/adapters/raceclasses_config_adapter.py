"""Module for raceclass adapter."""

import json
from pathlib import Path
from typing import Any

import aiofiles

from .adapter import Adapter


class RaceclassesConfigAdapter(Adapter):
    """Class representing an adapter for raceclasses config."""

    config_file_name = (
        Path(__file__).parent.parent / "config" / "raceclasses_config.json"
    )

    @classmethod
    async def init(cls) -> None:  # pragma: no cover
        """Initialize the class properties."""

    @classmethod
    async def get_default_raceclasses_config(cls: Any) -> dict:  # pragma: no cover
        """Get default raceclasses config."""
        async with aiofiles.open(cls.config_file_name) as file:
            content = await file.read()
        return json.loads(content)
