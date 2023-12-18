"""Integration test cases for the contestant route."""
from copy import deepcopy
from datetime import date
import os
from typing import Dict

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
import jwt
import pytest
from pytest_mock import MockFixture


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME")}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.fixture
async def event() -> Dict[str, str]:
    """An event object for testing."""
    return {
        "id": "ref_to_event",
        "name": "Oslo Skagen sprint",
        "competition_format": "Individual sprint",
        "date_of_event": "2021-08-31",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def new_contestant() -> dict:
    """Create a mock contestant object."""
    return {
        "first_name": "Cont E.",
        "last_name": "Stant",
        "birth_date": date(1970, 1, 1).isoformat(),
        "gender": "M",
        "ageclass": "G 12 år",
        "region": "Oslo Skikrets",
        "club": "Lyn Ski",
        "team": "Team Kollen",
        "email": "post@example.com",
        "event_id": "ref_to_event",
        "registration_time": "2021-08-31T12:00:00",
    }


@pytest.fixture
async def contestant() -> dict:
    """Create a mock contestant object."""
    return {
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
        "event_id": "ref_to_event",
        "bib": 1,
        "registration_time": "2021-08-31T12:00:00",
    }


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "user", "roles": ["user"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.mark.integration
async def test_create_contestant_good_case(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return Created, location header."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    request_body = new_contestant

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert (
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}"
            in resp.headers[hdrs.LOCATION]
        )


@pytest.mark.integration
async def test_create_contestants_csv_good_case(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 200 OK and simple result report in body."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value=None,
    )

    files = {"file": open("tests/files/contestants_G11.csv", "rb")}

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, data=files
        )
        assert resp.status == 200

        body = await resp.json()
        print(f"body: {body}")
        assert type(body) is dict

        assert body["total"] > 0
        assert body["created"] > 0
        assert len(body["updated"]) == 0
        assert len(body["failures"]) == 0
        assert body["total"] == body["created"] + len(body["updated"]) + len(
            body["failures"]
        )


@pytest.mark.integration
async def test_create_contestants_csv_no_minidrett_id_existing_good_case(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 200 OK and simple result report in body."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    files = {"file": open("tests/files/contestants_G11_no_minidrett_id.csv", "rb")}

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, data=files
        )
        assert resp.status == 200

        body = await resp.json()
        print(f"body: {body}")
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
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 200 OK and simple result report in body."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    files = {"file": open("tests/files/contestants_G11.csv", "rb")}

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, data=files
        )
        assert resp.status == 200

        body = await resp.json()
        print(f"body: {body}")
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
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 200 OK and simple result report in body."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    files = {
        "file": open("tests/files/contestants_G11_invalid_registration_time.csv", "rb")
    }

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, data=files
        )
        assert resp.status == 200

        body = await resp.json()
        print(f"body: {body}")
        assert type(body) is dict

        assert body["total"] > 0
        assert body["created"] == 0
        assert len(body["updated"]) > 0
        assert len(body["failures"]) == 1
        assert body["total"] == body["created"] + len(body["updated"]) + len(
            body["failures"]
        )


@pytest.mark.integration
async def test_create_contestants_csv_create_failures_good_case(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 200 OK and simple result report in body."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",  # noqa: B950
        return_value=None,
    )

    files = {"file": open("tests/files/contestants_G11_with_failures.csv", "rb")}

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, data=files
        )
        assert resp.status == 200

        body = await resp.json()
        print(f"body: {body}")
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
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 200 OK and simple result report in body."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",  # noqa: B950
        return_value=None,
    )

    files = {"file": open("tests/files/contestants_G11_with_failures.csv", "rb")}

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, data=files
        )
        assert resp.status == 200

        body = await resp.json()
        print(f"body: {body}")
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
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 400 Bad request."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    files = {"file": open("tests/files/contestants.notcsv", "rb")}

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, data=files
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_create_contestants_csv_not_supported_content_type(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 415 Unsupported Media Type."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value={"id": CONTESTANT_ID},
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    files = {"file": open("tests/files/contestants_G11.csv", "rb")}

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
        hdrs.CONTENT_TYPE: "unsupportedMediaType",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, data=files
        )
        assert resp.status == 415


@pytest.mark.integration
async def test_create_contestants_csv_good_case_octet_stream(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 200 OK and simple result report in body."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value=None,
    )

    with open("tests/files/contestants_G11.csv", "rb") as f:
        headers = {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }

        with aioresponses(passthrough=["http://127.0.0.1"]) as m:
            m.post("http://example.com:8081/authorize", status=204)
            resp = await client.post(
                f"/events/{EVENT_ID}/contestants", headers=headers, data=f
            )
            assert resp.status == 200

            body = await resp.json()
            print(f"body: {body}")
            assert type(body) is dict

            assert body["total"] > 0
            assert body["created"] > 0
            assert len(body["updated"]) == 0
            assert len(body["failures"]) == 0
            assert body["total"] == body["created"] + len(body["updated"]) + len(
                body["failures"]
            )


@pytest.mark.integration
async def test_get_contestant_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return OK, and a body containing one contestant."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == CONTESTANT_ID
        assert body["first_name"] == contestant["first_name"]
        assert body["last_name"] == contestant["last_name"]
        assert body["birth_date"] == contestant["birth_date"]
        assert body["gender"] == contestant["gender"]
        assert body["ageclass"] == contestant["ageclass"]
        assert body["region"] == contestant["region"]
        assert body["club"] == contestant["club"]
        assert body["team"] == contestant["team"]
        assert body["email"] == contestant["email"]
        assert body["event_id"] == contestant["event_id"]
        assert body["registration_time"] == contestant["registration_time"]


@pytest.mark.integration
async def test_update_contestant_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = deepcopy(contestant)
    request_body["last_name"] = "New_Last_Name"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_update_contestant_by_id_existing_bib(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=contestant,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = deepcopy(contestant)
    request_body["last_name"] = "New_Last_Name"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_contestants(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return OK and a valid json body."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",  # noqa: B950
        return_value=[contestant],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/contestants")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        contestants = await resp.json()
        assert type(contestants) is list
        assert len(contestants) == 1
        assert contestant["id"] == contestants[0]["id"]


@pytest.mark.integration
async def test_get_all_contestants_by_raceclass(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return OK and a valid json body."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",  # noqa: B950
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_name",  # noqa: B950
        return_value=[{"id": "1", "name": "G12", "ageclasses": ["G 12 år"]}],
    )

    raceclass = "G12"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/contestants?raceclass={raceclass}")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        contestants = await resp.json()
        assert type(contestants) is list
        assert len(contestants) == 1
        assert contestant["id"] == contestants[0]["id"]
        assert contestant["ageclass"] == contestants[0]["ageclass"]


@pytest.mark.integration
async def test_get_all_contestants_by_ageclass(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return OK and a valid json body."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",  # noqa: B950
        return_value=[contestant],
    )

    ageclass = "G 12 år"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/contestants?ageclass={ageclass}")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        contestants = await resp.json()
        assert type(contestants) is list
        assert len(contestants) == 1
        assert contestant["id"] == contestants[0]["id"]
        assert contestant["ageclass"] == contestants[0]["ageclass"]


@pytest.mark.integration
async def test_get_all_contestants_by_bib(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return OK and a valid json body."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",  # noqa: B950
        return_value=contestant,
    )

    bib = 1
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/contestants?bib={bib}")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        contestants = await resp.json()
        assert type(contestants) is list
        assert len(contestants) == 1
        assert contestant["id"] == contestants[0]["id"]
        assert contestant["bib"] == contestants[0]["bib"]


@pytest.mark.integration
async def test_delete_contestant_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return No Content."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.delete_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.delete(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}", headers=headers
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_delete_all_contestants_in_event(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return 204 No content."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.delete_all_contestants",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",  # noqa: B950
        return_value=[],
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(f"/events/{EVENT_ID}/contestants", headers=headers)
        assert resp.status == 204
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/contestants")
        assert resp.status == 200
        contestants = await resp.json()
        assert len(contestants) == 0


@pytest.mark.integration
async def test_search_contestant_by_name(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 200."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.search_contestants_in_event_by_name",  # noqa: B950
        return_value=[new_contestant],
    )

    search_params = {"name": "Stant"}

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    resp = await client.post(
        f"/events/{EVENT_ID}/contestants/search", headers=headers, json=search_params
    )
    assert resp.status == 200
    result = await resp.json()
    assert type(result) is list
    assert len(result) == 1


# Bad cases
# Event not found:
@pytest.mark.integration
async def test_create_contestant_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_contestant: dict,
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    request_body = new_contestant

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_create_contestants_csv_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value=None,
    )

    files = {"file": open("tests/files/contestants_G11.csv", "rb")}

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, data=files
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_create_contestants_csv_octet_stream_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value=None,
    )

    with open("tests/files/contestants_G11.csv", "rb") as f:
        headers = {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }

        with aioresponses(passthrough=["http://127.0.0.1"]) as m:
            m.post("http://example.com:8081/authorize", status=204)
            resp = await client.post(
                f"/events/{EVENT_ID}/contestants", headers=headers, data=f
            )
            assert resp.status == 404


# Contestant allready exist:
@pytest.mark.integration
async def test_create_contestant_allready_exist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 400 Bad request."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=new_contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value=new_contestant,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    request_body = new_contestant

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_create_contestant_bib_already_exist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 400 Bad request."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    new_contestant["bib"] = 1
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_minidrett_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value={"id": "different_id", "bib": new_contestant["bib"]},
    )

    request_body = new_contestant

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 400


# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_contestant_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    request_body = {"optional_property": "Optional_property"}

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_get_all_contestants_by_id_when_bib_has_been_set_to_noninteger(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return OK and a valid json body."""
    EVENT_ID = "event_id_1"
    contestant_2 = deepcopy(contestant)
    contestant_2["bib"] = None
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",  # noqa: B950
        return_value=[contestant, contestant_2],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/contestants")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        contestants = await resp.json()
        assert type(contestants) is list
        assert len(contestants) == 2
        assert contestant["bib"] == contestants[1]["bib"]
        assert contestant_2["bib"] == contestants[0]["bib"]


@pytest.mark.integration
async def test_get_all_contestants_by_raceclass_raceclass_does_not_exist(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return 400 Bad request."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",  # noqa: B950
        return_value=[contestant],
    )
    mocker.patch(
        "event_service.adapters.raceclasses_adapter.RaceclassesAdapter.get_raceclass_by_name",  # noqa: B950
        return_value=[],
    )

    raceclass = "G12"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/contestants?raceclass={raceclass}")
        assert resp.status == 400


@pytest.mark.integration
async def test_get_all_contestants_by_bib_wrong_paramter_type(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return 400 Bad request."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",  # noqa: B950
        return_value=contestant,
    )

    bib = "one"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get(f"/events/{EVENT_ID}/contestants?bib={bib}")
        assert resp.status == 400


@pytest.mark.integration
async def test_create_contestant_with_input_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    contestant: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    request_body = contestant

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_contestant_adapter_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 400 HTTPBadRequest."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_name",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    request_body = new_contestant

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_update_contestant_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value={"id": CONTESTANT_ID, "first_name": "Missing LastName"},
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {"id": CONTESTANT_ID, "optional_property": "Optional_property"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_contestant_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=contestant["id"],
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = deepcopy(contestant)
    request_body["id"] = "different_id"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_contestant_by_id_existing_bib_different_contestant(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return 400 Bad request."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value={"id": "different_id", "bib": contestant["bib"]},
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = deepcopy(contestant)
    request_body["last_name"] = "New_Last_Name"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_create_contestant_no_authorization(
    client: _TestClient, mocker: MockFixture, event: dict, new_contestant: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",  # noqa: B950
        return_value=CONTESTANT_ID,
    )

    request_body = new_contestant

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_update_contestant_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, contestant: dict
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=contestant,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
    }

    request_body = contestant

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_contestant_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.delete_contestant",
        return_value=CONTESTANT_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.delete(f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_all_contestants_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    EVENT_ID = "event_id_1"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.delete_all_contestants",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.delete(f"/events/{EVENT_ID}/contestants")
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_contestant_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    event: dict,
    new_contestant: dict,
) -> None:
    """Should return 403 Forbidden."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",  # noqa: B950
        return_value=event,
    )
    mocker.patch(
        "event_service.services.contestants_service.create_id",
        return_value=CONTESTANT_ID,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.create_contestant",
        return_value=CONTESTANT_ID,
    )
    request_body = new_contestant

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=403)
        resp = await client.post(
            f"/events/{EVENT_ID}/contestants", headers=headers, json=request_body
        )
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_contestant_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=None,
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}")
        assert resp.status == 404


@pytest.mark.integration
async def test_update_contestant_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, contestant: dict
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.update_contestant",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_bib",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = contestant

    CONTESTANT_ID = "does-not-exist"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_contestant_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    EVENT_ID = "event_id_1"
    CONTESTANT_ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_contestant_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.delete_contestant",
        return_value=None,
    )

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(
            f"/events/{EVENT_ID}/contestants/{CONTESTANT_ID}", headers=headers
        )
        assert resp.status == 404
