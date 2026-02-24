"""Module for liveness adapter."""

import logging
from typing import Any


class LivenessAdapter:
    """Class representing an adapter for the liveness connection."""

    database: Any
    logger: logging.Logger

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize class properties."""
        cls.database = database
        cls.logger = logging.getLogger("uvicorn.error")

    @classmethod
    async def database_is_ready(cls) -> bool:  # pragma: no cover
        """Check if the database connection is ready."""
        try:
            result = await cls.database.command("ping")
        except Exception:
            cls.logger.exception("Error pinging database")
            return False
        cls.logger.debug(f"result of db-ping: {result}")
        return result["ok"] == 1
