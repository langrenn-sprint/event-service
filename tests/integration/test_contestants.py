"""Integration test cases for the contestant route."""

import os
from copy import deepcopy
from datetime import UTC, date, datetime
from http import HTTPStatus
from uuid import uuid4

import aiofiles
import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app import api
from app.models import Contestant, Event, Raceclass


@pytest.fixture
def client() -> TestClient:
    """Fixture to create a test client for the FastAPI application."""
    return TestClient(api)


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {
        "username": os.getenv("ADMIN_USERNAME"),
        "exp": 9999999999,
        "role": "admin",
    }
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
async def event() -> Event:
    """Create a mock event object."""
    return Event.model_validate(
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "A test event",
            "date_of_event": "2024-06-01",
            "time_of_event": "12:00:00",
        }
    )


@pytest.fixture
async def contestant(event: Event) -> Contestant:
    """Create a mock contestant object."""
    return Contestant.model_validate(
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "first_name": "Cont E.",
            "last_name": "Stant",
            "birth_date": date(1970, 1, 1).isoformat(),
            "gender": "M",
            "ageclass": "G 12 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event.id,
            "registration_date_time": "2021-08-31T12:00:00",
        }
    )


@pytest.fixture
async def contestant_with_bib(event: Event) -> Contestant:
    """Create a mock contestant object."""
    return Contestant.model_validate(
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "first_name": "Cont E.",
            "last_name": "Stant",
            "birth_date": date(1970, 1, 1).isoformat(),
            "gender": "M",
            "ageclass": "G 12 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event.id,
            "registration_date_time": "2021-08-31T12:00:00",
            "bib": 1,
        }
    )


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "user", "roles": ["user"]}
    return jwt.encode(payload, secret, algorithm)


@pytest.mark.integration
async def test_create_contestant_good_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return Created, location header."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=None,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )

    request_body = contestant.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants", headers=headers, json=request_body
    )
    assert resp.status_code == 201, resp.json()
    assert f"/events/{event.id}/contestants/{contestant.id}" in resp.headers["Location"]


@pytest.mark.integration
async def test_create_contestants_csv_good_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 200 OK and simple result report in body."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )

    async with aiofiles.open("tests/files/contestants_G11.csv", "rb") as file:
        file_content = await file.read()

    files = {"file": ("contestants_G11.csv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == 200

    body = resp.json()
    assert type(body) is dict

    assert body["total"] > 0
    assert body["created"] > 0
    assert len(body["updated"]) == 0
    assert len(body["failures"]) == 0
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.integration
async def test_create_contestants_csv_i_sonen_good_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 200 OK and simple result report in body."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=None,
    )

    async with aiofiles.open("tests/files/contestants_iSonen.csv", "rb") as file:
        file_content = await file.read()

    files = {"file": ("contestants_iSonen.csv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )

    assert resp.status_code == 200

    body = resp.json()
    assert type(body) is dict

    assert body["total"] > 0
    assert body["created"] > 0
    assert len(body["updated"]) == 0
    assert len(body["failures"]) == 0
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.integration
async def test_create_contestants_csv_sportsadmin_good_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 200 OK and simple result report in body."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=None,
    )

    async with aiofiles.open("tests/files/contestants_Sportsadmin.csv", "rb") as file:
        file_content = await file.read()

    files = {"file": ("contestants_Sportsadmin.csv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == 200

    body = resp.json()
    assert type(body) is dict

    assert body["total"] > 0
    assert body["created"] > 0
    assert len(body["updated"]) == 0
    assert len(body["failures"]) == 0
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.integration
async def test_create_contestants_csv_unsupported_format(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=None,
    )

    async with aiofiles.open(
        "tests/files/contestants_unsupported_format.csv", "rb"
    ) as file:
        file_content = await file.read()

    files = {"file": ("contestants_unsupported_format.csv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == 400


@pytest.mark.integration
async def test_create_contestants_csv_no_minidrett_id_existing_good_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 200 OK and simple result report in body."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant.id,
    )

    async with aiofiles.open(
        "tests/files/contestants_G11_no_minidrett_id.csv", "rb"
    ) as file:
        file_content = await file.read()

        files = {"file": ("contestants_G11_no_minidrett_id.csv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == 200

    body = resp.json()
    assert type(body) is dict

    assert body["total"] > 0
    assert body["created"] == 0
    assert len(body["updated"]) > 0
    assert len(body["failures"]) == 0
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.integration
async def test_create_contestants_csv_minidrett_id_existing_good_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 200 OK and simple result report in body."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant.id,
    )

    async with aiofiles.open("tests/files/contestants_G11.csv", "rb") as file:
        file_content = await file.read()

    files = {"file": ("contestants_G11.csv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }
    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == 200

    body = resp.json()
    assert type(body) is dict

    assert body["total"] > 0
    assert body["created"] == 0
    assert len(body["updated"]) > 0
    assert len(body["failures"]) == 0
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.integration
async def test_create_contestants_csv_invalid_registration_date_good_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 200 OK and simple result report in body."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant.id,
    )

    async with aiofiles.open(
        "tests/files/contestants_G11_invalid_registration_date_time.csv", "rb"
    ) as file:
        file_content = await file.read()

    files = {
        "file": ("contestants_G11_invalid_registration_date_time.csv", file_content)
    }

    headers = {
        "Authorization": f"Bearer {token}",
    }
    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == HTTPStatus.OK

    body = resp.json()
    assert type(body) is dict

    assert body["total"] == 3
    assert body["created"] == 0
    assert len(body["updated"]) == 2
    assert len(body["failures"]) == 1
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.integration
async def test_create_contestants_csv_create_failures_good_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
) -> None:
    """Should return 200 OK and simple result report in body."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=None,
    )

    async with aiofiles.open(
        "tests/files/contestants_G11_with_failures.csv", "rb"
    ) as file:
        file_content = await file.read()

    files = {"file": ("contestants_G11_with_failures.csv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == 200

    body = resp.json()
    assert type(body) is dict

    assert body["total"] > 0
    assert body["created"] == 0
    assert len(body["updated"]) == 0
    assert len(body["failures"]) == 3
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.integration
async def test_create_contestants_csv_update_failures_good_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 200 OK and simple result report in body."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=contestant,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )

    async with aiofiles.open(
        "tests/files/contestants_G11_with_failures.csv", "rb"
    ) as file:
        file_content = await file.read()

    files = {"file": ("contestants_G11_with_failures.csv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }
    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == 200

    body = resp.json()
    assert type(body) is dict

    assert body["total"] > 0
    assert body["created"] == 0
    assert len(body["updated"]) == 0
    assert len(body["failures"]) > 0
    assert body["total"] == body["created"] + len(body["updated"]) + len(
        body["failures"]
    )


@pytest.mark.integration
async def test_create_contestants_csv_bad_case(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=contestant,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )

    async with aiofiles.open("tests/files/contestants.notcsv", "rb") as file:
        file_content = await file.read()

    files = {"file": ("contestants.notcsv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }
    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE


@pytest.mark.integration
async def test_create_contestants_csv_not_supported_content_type(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 415 Unsupported Media Type."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=contestant,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant.id,
    )

    async with aiofiles.open("tests/files/contestants_G11.csv", "rb") as file:
        file_content = await file.read()

    files = {"file": ("contestants_G11.asdf", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == 415


@pytest.mark.integration
async def test_get_contestant_by_id(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return OK, and a body containing one contestant."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=contestant,
    )

    resp = client.get(f"/events/{event.id}/contestants/{contestant.id}")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(contestant.id)
    assert body["first_name"] == contestant.first_name
    assert body["last_name"] == contestant.last_name
    assert body["birth_date"] == contestant.birth_date.isoformat()
    assert body["gender"] == contestant.gender
    assert body["ageclass"] == contestant.ageclass
    assert body["region"] == contestant.region
    assert body["club"] == contestant.club
    assert body["team"] == contestant.team
    assert body["email"] == contestant.email
    assert body["event_id"] == str(contestant.event_id)
    assert (
        body["registration_date_time"] == contestant.registration_date_time.isoformat()
    )


@pytest.mark.integration
async def test_update_contestant_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return No Content."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        side_effect=[
            [
                Raceclass.model_validate(
                    {
                        "id": "11111111-1111-4111-8111-111111111111",
                        "name": "G12",
                        "gender": "M",
                        "ageclasses": ["G 12 år"],
                        "event_id": event.id,
                    }
                )
            ],
            [
                Raceclass.model_validate(
                    {
                        "id": "22222222-2222-4222-8222-222222222222",
                        "name": "G13",
                        "gender": "M",
                        "ageclasses": ["G 13 år"],
                        "event_id": event.id,
                    }
                )
            ],
        ],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_id",
        side_effect=[
            {
                "id": "11111111-1111-4111-8111-111111111111",
                "name": "G12",
                "gender": "M",
                "ageclasses": ["G 12 år"],
                "event_id": event.id,
            },
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "name": "G13",
                "gender": "M",
                "ageclasses": ["G 13 år"],
                "event_id": event.id,
            },
        ],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.update_raceclass",
        side_effect=["1", "2"],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = deepcopy(contestant)
    request_body.last_name = "New_Last_Name"
    request_body.ageclass = "Gutter 13 år"

    resp = client.put(
        f"/events/{event.id}/contestants/{contestant.id}",
        headers=headers,
        json=request_body.model_dump(mode="json"),
    )
    assert resp.status_code == 204


@pytest.mark.integration
async def test_update_contestant_by_id_existing_bib(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant_with_bib: Contestant,
) -> None:
    """Should return No Content."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=contestant_with_bib,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant_with_bib.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=contestant_with_bib,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = deepcopy(contestant_with_bib)
    request_body.last_name = "New_Last_Name"

    resp = client.put(
        f"/events/{event.id}/contestants/{contestant_with_bib.id}",
        headers=headers,
        json=request_body.model_dump(mode="json"),
    )
    assert resp.status_code == 204


@pytest.mark.integration
async def test_get_all_contestants(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return OK and a valid json body."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )

    resp = client.get(f"/events/{event.id}/contestants")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    contestants = resp.json()
    assert type(contestants) is list
    assert len(contestants) == 1
    assert str(contestant.id) == contestants[0]["id"]


@pytest.mark.integration
async def test_get_all_contestants_by_raceclass(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return OK and a valid json body."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_name",
        return_value=[
            Raceclass.model_validate(
                {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "name": "G13",
                    "gender": "M",
                    "ageclasses": ["G 12 år"],
                    "event_id": event.id,
                }
            )
        ],
    )

    raceclass = "G12"
    resp = client.get(f"/events/{event.id}/contestants?raceclass-name={raceclass}")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    contestants = resp.json()
    assert type(contestants) is list
    assert len(contestants) == 1
    assert str(contestant.id) == contestants[0]["id"]
    assert contestant.ageclass == contestants[0]["ageclass"]


@pytest.mark.integration
async def test_get_all_contestants_by_ageclass(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return OK and a valid json body."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )

    ageclass = "G 12 år"
    resp = client.get(f"/events/{event.id}/contestants?ageclass-name={ageclass}")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    contestants = resp.json()
    assert type(contestants) is list
    assert len(contestants) == 1
    assert str(contestant.id) == contestants[0]["id"]
    assert contestant.ageclass == contestants[0]["ageclass"]


@pytest.mark.integration
async def test_get_all_contestants_by_bib(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return OK and a valid json body."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=contestant,
    )

    bib = 1
    resp = client.get(f"/events/{event.id}/contestants?bib={bib}")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    contestants = resp.json()
    assert type(contestants) is list
    assert len(contestants) == 1
    assert str(contestant.id) == contestants[0]["id"]
    assert contestant.bib == contestants[0]["bib"]


@pytest.mark.integration
async def test_delete_contestant_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return No Content."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.delete_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_all_raceclasses",
        return_value=[],
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.delete(
        f"/events/{event.id}/contestants/{contestant.id}", headers=headers
    )
    assert resp.status_code == 204


@pytest.mark.integration
async def test_delete_all_contestants_in_event(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
) -> None:
    """Should return 204 No content."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.delete_all_contestants",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )
    headers = {
        "Authorization": f"Bearer {token}",
    }
    resp = client.delete(f"/events/{event.id}/contestants", headers=headers)
    assert resp.status_code == 204
    resp = client.get(f"/events/{event.id}/contestants")
    assert resp.status_code == 200
    contestants = resp.json()
    assert len(contestants) == 0


@pytest.mark.integration
async def test_search_contestant_by_name(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 200."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.search_contestants_in_event_by_name",
        return_value=[contestant],
    )

    search_params = {"name": "Stant"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants/search", headers=headers, json=search_params
    )
    assert resp.status_code == 200
    result = resp.json()
    assert type(result) is list
    assert len(result) == 1


# Bad cases
# Event not found:
@pytest.mark.integration
async def test_create_contestant_event_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=None,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )

    request_body = contestant.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants", headers=headers, json=request_body
    )
    assert resp.status_code == 404


@pytest.mark.integration
async def test_create_contestants_csv_event_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=None,
    )

    async with aiofiles.open("tests/files/contestants_G11.csv", "rb") as file:
        file_content = await file.read()

    files = {"file": ("contestants_G11.csv", file_content)}

    headers = {
        "Authorization": f"Bearer {token}",
    }
    resp = client.post(
        f"/events/{event.id}/contestants/file", headers=headers, files=files
    )
    assert resp.status_code == 404


# Contestant allready exist:
@pytest.mark.integration
async def test_create_contestant_allready_exist(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=contestant,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )

    request_body = contestant.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants", headers=headers, json=request_body
    )
    assert resp.status_code == 400


@pytest.mark.integration
async def test_create_contestant_bib_already_exist(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 400 Bad request."""
    contestant.bib = 1
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",
        return_value=None,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=Contestant(
            id=uuid4(),
            event_id=event.id,
            bib=1,
            first_name="Bib_Existing_Contestant",
            last_name="Bib_Existing_Contestant",
            birth_date=date(2000, 1, 1),
            gender="M",
            ageclass="G 12 år",
            region="Region",
            club="Club",
            team="Team",
            email="bib_existing_contestant@example.com",
            registration_date_time=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        ),
    )

    request_body = contestant.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants", headers=headers, json=request_body
    )
    assert resp.status_code == 400


# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_contestant_missing_mandatory_property(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    request_body = {"optional_property": "Optional_property"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants", headers=headers, json=request_body
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_get_all_contestants_by_id_when_bib_has_been_set_to_noninteger(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return OK and a valid json body."""
    contestant_2 = deepcopy(contestant)
    contestant_2.bib = None
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant, contestant_2],
    )

    resp = client.get(f"/events/{event.id}/contestants")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["Content-Type"]
    contestants = resp.json()
    assert type(contestants) is list
    assert len(contestants) == 2
    assert contestant.bib == contestants[1]["bib"]
    assert contestant_2.bib == contestants[0]["bib"]


@pytest.mark.integration
async def test_get_all_contestants_by_raceclass_raceclass_does_not_exist(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[contestant],
    )
    mocker.patch(
        "app.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_name",
        return_value=[],
    )

    raceclass = "G12"
    resp = client.get(f"/events/{event.id}/contestants?raceclass-name={raceclass}")
    assert resp.status_code == 400


@pytest.mark.integration
async def test_get_all_contestants_by_bib_wrong_paramter_type(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 422 Unprocessable entity."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=contestant,
    )

    bib = "one"
    resp = client.get(f"/events/{event.id}/contestants?bib={bib}")
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
async def test_create_contestant_with_input_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 201 Created."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )
    request_body = contestant.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants", headers=headers, json=request_body
    )
    assert resp.status_code == HTTPStatus.CREATED


@pytest.mark.integration
async def test_create_contestant_adapter_fails(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 500 Internal server error."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",
        return_value=None,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    request_body = contestant.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants", headers=headers, json=request_body
    )
    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.integration
async def test_update_contestant_by_id_missing_mandatory_property(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = {"id": str(contestant.id), "optional_property": "Optional_property"}

    resp = client.put(
        f"/events/{event.id}/contestants/{contestant.id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_update_contestant_by_id_different_id_in_body(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = deepcopy(contestant)
    request_body.id = uuid4()

    resp = client.put(
        f"/events/{event.id}/contestants/{contestant.id}",
        headers=headers,
        json=request_body.model_dump(mode="json"),
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_update_contestant_by_id_existing_bib_different_contestant(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant_with_bib: Contestant,
) -> None:
    """Should return 400 Bad request."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=contestant_with_bib,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant_with_bib.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=Contestant(
            id=uuid4(),
            event_id=event.id,
            bib=1,
            first_name="Bib_Existing_Contestant",
            last_name="Bib_Existing_Contestant",
            birth_date=date(2000, 1, 1),
            gender="M",
            ageclass="G 12 år",
            region="Region",
            club="Club",
            team="Team",
            email="a@example.com",
            registration_date_time=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        ),
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = deepcopy(contestant_with_bib)
    request_body.last_name = "New_Last_Name"

    resp = client.put(
        f"/events/{event.id}/contestants/{contestant_with_bib.id}",
        headers=headers,
        json=request_body.model_dump(mode="json"),
    )
    assert resp.status_code == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_create_contestant_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event, contestant: Contestant
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )

    request_body = contestant.model_dump(mode="json")

    headers = {"Content-Type": "application/json"}

    resp = client.post(
        f"/events/{event.id}/contestants", headers=headers, json=request_body
    )
    assert resp.status_code == 401


@pytest.mark.integration
async def test_update_contestant_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event, contestant: Contestant
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=contestant,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant.id,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
    }

    request_body = contestant.model_dump(mode="json")

    resp = client.put(
        f"/events/{event.id}/contestants/{contestant.id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == 401


@pytest.mark.integration
async def test_delete_contestant_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, event: Event, contestant: Contestant
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.delete_contestant",
        return_value=contestant.id,
    )

    resp = client.delete(f"/events/{event.id}/contestants/{contestant.id}")
    assert resp.status_code == 401


@pytest.mark.integration
async def test_delete_all_contestants_no_authorization(
    client: TestClient,
    mocker: MockFixture,
    event: Event,
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.delete_all_contestants",
        return_value=None,
    )

    resp = client.delete(f"/events/{event.id}/contestants")
    assert resp.status_code == 401


# Forbidden:
@pytest.mark.integration
async def test_create_contestant_insufficient_role(
    client: TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 403 Forbidden."""
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=contestant.id,
    )
    request_body = contestant.model_dump(mode="json")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token_unsufficient_role}",
    }

    resp = client.post(
        f"/events/{event.id}/contestants", headers=headers, json=request_body
    )
    assert resp.status_code == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_contestant_not_found(
    client: TestClient, mocker: MockFixture, event: Event
) -> None:
    """Should return 404 Not found."""
    contestant_id = uuid4()
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=None,
    )
    resp = client.get(f"/events/{event.id}/contestants/{contestant_id}")
    assert resp.status_code == 404


@pytest.mark.integration
async def test_update_contestant_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: Event,
    contestant: Contestant,
) -> None:
    """Should return 404 Not found."""
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = contestant.model_dump(mode="json")

    resp = client.put(
        f"/events/{event.id}/contestants/{contestant.id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == 404


@pytest.mark.integration
async def test_delete_contestant_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture, event: Event
) -> None:
    """Should return 404 Not found."""
    contestant_id = uuid4()
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.contestants_adapter.ContestantsAdapter.delete_contestant",
        return_value=None,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = client.delete(
        f"/events/{event.id}/contestants/{contestant_id}", headers=headers
    )
    assert resp.status_code == 404
