"""Module for admin of sporting events."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pymongo import AsyncMongoClient

from app.adapters import (
    CompetitionFormatsAdapter,
    ContestantsAdapter,
    EventsAdapter,
    LivenessAdapter,
    RaceclassesAdapter,
    ResultsAdapter,
)
from app.adapters.raceclasses_config_adapter import RaceclassesConfigAdapter
from app.authorization import (
    TokenError,
    TokenMissingError,
    TokenValidationError,
    document_roles,
)
from app.routers import (
    contestants,
    contestants_commands,
    contestants_search,
    events,
    events_commands,
    ping,
    raceclasses,
    ready,
    results,
)
from app.utils import db_utils

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "27017"))
DB_NAME = os.getenv("DB_NAME", "events")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
CONFIG = os.getenv("CONFIG", "production")


class EndpointFilter(logging.Filter):
    """Logging filter to exclude specific endpoints from access logs."""

    def __init__(self, excluded_endpoints: list[str]) -> None:
        """Initialize the filter with a list of endpoints to exclude."""
        super().__init__()
        self.excluded_endpoints = excluded_endpoints

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover
        """Filter log records to exclude specified endpoints."""
        # Assuming the endpoint path is available in record.args[2]
        # for Uvicorn access logs
        if (  # noqa: SIM103
            record.args
            and len(record.args) >= 3  # noqa: PLR2004
            and record.args[2] in self.excluded_endpoints  # ty: ignore[invalid-argument-type]
        ):
            return False  # Exclude this log record
        return True  # Include this log record


class LevelPrefixFormatter(logging.Formatter):
    """Formatter that pads the level like uvicorn does, so log lines align."""

    def format(self, record: logging.LogRecord) -> str:
        """Add a padded level prefix ("INFO:     ") to the record and format it."""
        record.levelprefix = f"{record.levelname}:".ljust(9)
        return super().format(record)


def configure_logging(level: str) -> None:
    """Configure the application logger.

    Every module logs through logging.getLogger(__name__), so all application
    loggers are children of the "app" logger, which is configured here. This
    works the same however the app is started (uvicorn, fastapi dev, tests).
    Uvicorn's own loggers are configured by uvicorn (logging.yaml in Docker).

    An empty level means INFO: docker-compose passes LOGGING_LEVEL as an empty
    string when it is not set on the host.
    """
    app_logger = logging.getLogger("app")
    app_logger.setLevel(level.upper() or "INFO")
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            LevelPrefixFormatter(
                "%(levelprefix)s [%(asctime)s] %(name)s - %(message)s",
                datefmt="%d-%m-%Y %H:%M:%S",
            )
        )
        app_logger.addHandler(handler)
    # Do not also pass records on to the root logger, which would log them twice:
    app_logger.propagate = False


configure_logging(LOGGING_LEVEL)
logger = logging.getLogger(__name__)

# Exclude the liveness and readiness probes from the access log:
logging.getLogger("uvicorn.access").addFilter(EndpointFilter(["/ping", "/ready"]))


@asynccontextmanager
async def lifespan(api: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001  # pragma: no cover
    """Start adapters and internal message consumer on app startup."""
    # Initialize database:
    msg = f"Connecting to db at {DB_HOST}:{DB_PORT}"
    logger.debug(msg)
    mongo = AsyncMongoClient(
        host=DB_HOST,
        port=DB_PORT,
        username=DB_USER,
        password=DB_PASSWORD,
        uuidRepresentation="standard",
    )
    db = mongo[f"{DB_NAME}"]

    await CompetitionFormatsAdapter.init()
    await ContestantsAdapter.init(db)
    await EventsAdapter.init(db)
    await LivenessAdapter.init(db)
    await RaceclassesAdapter.init(db)
    await RaceclassesConfigAdapter.init()
    await ResultsAdapter.init(db)

    if CONFIG in ["production", "dev"]:  # pragma: no cover
        # Create text index for search on contestants:
        try:
            await db_utils.create_indexes(db)
        except Exception:
            logger.exception("Could not create indexs.")

    yield

    # Cleanup resources if needed
    await mongo.close()


tags_metadata = [
    {
        "name": "events",
        "description": "Operations on events.",
    },
    {
        "name": "contestants",
        "description": "Manage contestants.",
    },
    {
        "name": "raceclasses",
        "description": "Manage raceclasses.",
    },
    {
        "name": "results",
        "description": "Manage results.",
    },
    {
        "name": "liveness",
        "description": "Liveness and readiness endpoints.",
    },
]
api = FastAPI(
    lifespan=lifespan,
    title="Event Service",
    version="1.0.0",
    separate_input_output_schemas=False,
    openapi_tags=tags_metadata,
)


@api.exception_handler(TokenError)
async def token_exception_handler(request: Request, exc: TokenError) -> JSONResponse:
    """Handle token errors.

    Users without the required role get 403 from RoleChecker, not from here.
    """
    _ = request  # Unused variable
    if isinstance(exc, (TokenMissingError, TokenValidationError)):
        # Missing, expired, wrongly signed or undecodable token:
        # the client is not authenticated.
        return JSONResponse(
            status_code=401,
            content={"detail": "Not authenticated"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Any other token error is a server problem, e.g. APIConfigurationError when
    # JWT_SECRET is missing. The details are logged where the error is raised,
    # not returned to the client.
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


# Set up routes:
api.include_router(ping.router)
api.include_router(ready.router)
api.include_router(events.router)
api.include_router(events_commands.router)
api.include_router(raceclasses.router)
api.include_router(contestants.router)
api.include_router(contestants_commands.router)
api.include_router(contestants_search.router)
api.include_router(results.router)
document_roles(api)
