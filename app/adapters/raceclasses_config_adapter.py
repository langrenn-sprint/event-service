"""Module for raceclass adapter."""

import json
import logging
from pathlib import Path
from typing import Any

import aiofiles

from app.models import RaceclassesConfig


class RaceclassesConfigAdapter:
    """Class representing an adapter for raceclasses config."""

    config_file_name = (
        Path(__file__).parent.parent / "config" / "raceclasses_config.json"
    )
    logger: logging.Logger

    @classmethod
    async def init(cls) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.logger = logging.getLogger("uvicorn.error")

    @classmethod
    async def get_default_raceclasses_config(
        cls: Any,
    ) -> RaceclassesConfig:  # pragma: no cover
        """Get default raceclasses config."""
        async with aiofiles.open(cls.config_file_name) as file:
            content = await file.read()
        return RaceclassesConfig.model_validate(json.loads(content))
