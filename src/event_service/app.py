"""Module for admin of sporting events."""
import logging
import os

from aiohttp import web
import motor.motor_asyncio

from .views import (
    Ping,
    Ready,
)

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 27017))
DB_NAME = os.getenv("DB_NAME", "test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


async def create_app() -> web.Application:
    """Create an web application."""
    app = web.Application()
    # Set up logging
    logging.basicConfig(level=LOGGING_LEVEL)

    # Set up database connection:
    logging.debug(f"Connecting to db at {DB_HOST}:{DB_PORT}")
    client = motor.motor_asyncio.AsyncIOMotorClient(DB_HOST, DB_PORT)
    db = client.DB_NAME
    app["db"] = db
    app.add_routes(
        [
            web.view("/ping", Ping),
            web.view("/ready", Ready),
        ]
    )
    return app
