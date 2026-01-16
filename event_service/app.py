"""Module for admin of sporting events."""

import logging
import os
from collections.abc import AsyncGenerator

import motor.motor_asyncio
from aiohttp import web
from aiohttp.web_app import Application
from aiohttp_middlewares.cors import cors_middleware
from aiohttp_middlewares.error import error_middleware

from event_service.adapters.raceclasses_config_adapter import RaceclassesConfigAdapter

from .adapters import (
    CompetitionFormatsAdapter,
    ContestantsAdapter,
    EventFormatAdapter,
    EventsAdapter,
    RaceclassesAdapter,
    ResultsAdapter,
    UsersAdapter,
)
from .utils import db_utils
from .views import (
    ContestantsAssignBibsView,
    ContestantsSearchView,
    ContestantsView,
    ContestantView,
    EventFormatView,
    EventGenerateRaceclassesView,
    EventsView,
    EventView,
    Ping,
    RaceclassesView,
    RaceclassResultsView,
    RaceclassResultView,
    RaceclassView,
    Ready,
)

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
DB_HOST = os.getenv("DB_HOST", "mongodb")
DB_PORT = int(os.getenv("DB_PORT", "27017"))
DB_NAME = os.getenv("DB_NAME", "events")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
CONFIG = os.getenv("CONFIG", "production")


async def create_app() -> web.Application:
    """Create an web application."""
    app = web.Application(
        middlewares=[
            cors_middleware(allow_all=True),
            error_middleware(),  # default error handler for whole application
        ]
    )
    # Set up logging
    logger = logging.getLogger("event_service.app")
    logger.setLevel(LOGGING_LEVEL)
    logging.getLogger("chardet.charsetprober").setLevel(LOGGING_LEVEL)

    # Set up routes:
    app.add_routes(
        [
            web.view("/ping", Ping),
            web.view("/ready", Ready),
            web.view("/events", EventsView),
            web.view("/events/{eventId}", EventView),
            web.view(
                "/events/{eventId}/generate-raceclasses", EventGenerateRaceclassesView
            ),
            web.view("/events/{eventId}/format", EventFormatView),
            web.view("/events/{eventId}/raceclasses", RaceclassesView),
            web.view("/events/{eventId}/raceclasses/{raceclassId}", RaceclassView),
            web.view("/events/{eventId}/contestants", ContestantsView),
            web.view(
                "/events/{eventId}/contestants/assign-bibs", ContestantsAssignBibsView
            ),
            web.view("/events/{eventId}/contestants/search", ContestantsSearchView),
            web.view("/events/{eventId}/contestants/{contestantId}", ContestantView),
            web.view("/events/{eventId}/results", RaceclassResultsView),
            web.view("/events/{eventId}/results/{raceclass}", RaceclassResultView),
        ]
    )

    async def mongo_context(app: Application) -> AsyncGenerator[None]:
        # Set up database connection:
        logger.debug(f"Connecting to db at {DB_HOST}:{DB_PORT}")
        mongo = motor.motor_asyncio.AsyncIOMotorClient(
            host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASSWORD
        )
        db = mongo[f"{DB_NAME}"]
        app["db"] = db

        if CONFIG == "production":  # pragma: no cover
            # Create text index for search on contestants:
            try:
                await db_utils.create_indexes(db)
            except Exception:
                logger.exception("Could not create index on contestants.")

            await CompetitionFormatsAdapter.init()
            await ContestantsAdapter.init(db)
            await EventFormatAdapter.init(db)
            await EventsAdapter.init(db)
            await RaceclassesAdapter.init(db)
            await RaceclassesConfigAdapter.init()
            await ResultsAdapter.init(db)
            await UsersAdapter.init(db)

        yield

        mongo.close()

    app.cleanup_ctx.append(mongo_context)

    return app
