"""Contract test cases for competition-formats."""
import asyncio
from json import load
import logging
import os

from aiohttp import ClientSession, hdrs
from dotenv import load_dotenv

load_dotenv()
USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")
EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT")


async def login(session: ClientSession) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {hdrs.CONTENT_TYPE: "application/json"}
    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    async with session.post(url, headers=headers, json=request_body) as response:
        body = await response.json()
    if response.status != 200:
        logging.error(f"Got unexpected status {response.status} from {url}.")
    return body["token"]


async def create_competition_format(
    session: ClientSession,
    token: str,
    competition_format: dict,
) -> str:
    """Should return Created, location header and no body."""
    url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = competition_format

    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    return status


async def get_competition_format_by_name(
    session: ClientSession, token: str, name: str
) -> str:
    """Should return OK and an competition_format as json."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats?name={name}"
    async with session.get(url, headers=headers) as response:
        status = response.status
        if status == 200:
            body = await response.json()

    if response.status == 200 and len(body) > 0:
        return body[0]["id"]
    else:
        return None


async def update_competition_format(
    session: ClientSession, token: str, id: str, competition_format: dict
) -> str:
    """Should return No Content."""
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    competition_format["id"] = id
    url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats/{id}"
    async with session.put(url, headers=headers, json=competition_format) as response:
        pass
    return response.status


async def load_competition_formats() -> None:
    """Load the competition_formats from file."""
    logging.basicConfig(level=logging.DEBUG)

    with open("files/competition_formats.json", "r") as file:
        competition_formats = load(file)
        async with ClientSession() as session:
            token = await login(session)
            for competition_format in competition_formats:
                # Check if it exists:
                id = await get_competition_format_by_name(
                    session, token, competition_format["name"]
                )
                # If it exist, update:
                if id:
                    update_result = await update_competition_format(
                        session, token, id, competition_format
                    )
                    if update_result == 204:
                        logging.info(
                            f'Update competition_format "{competition_format["name"]}"'
                        )
                    else:
                        logging.error(
                            f"Failed to update competition_format. Got status {update_result}"
                        )
                # Otherwise create:
                else:
                    create_result = await create_competition_format(
                        session, token, competition_format
                    )
                    if create_result == 201:
                        logging.info(
                            f'Update competition_format "{competition_format["name"]}"'
                        )
                    else:
                        logging.error(
                            f"Failed to create competition_format. Got status {create_result}"
                        )


loop = asyncio.get_event_loop()
tasks = [
    loop.create_task(load_competition_formats()),
]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
