"""Integration test cases for the competition_formats route."""
from copy import deepcopy
import os
from typing import Any, Dict, Union

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
import jwt
from multidict import MultiDict
import pytest
from pytest_mock import MockFixture


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "user", "roles": ["event-admin"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.fixture
async def competition_format_interval_start() -> Dict[str, Union[int, str]]:
    """An competition_format object for testing."""
    return {
        "name": "Interval Start",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
        "max_no_of_contestants_in_raceclass": 9999,
        "max_no_of_contestants_in_race": 9999,
        "datatype": "interval_start",
    }


@pytest.fixture
async def competition_format_individual_sprint() -> Dict[str, Any]:
    """An competition_format object for testing."""
    return {
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_groups": "00:10:00",
        "time_between_rounds": "00:05:00",
        "time_between_heats": "00:02:30",
        "max_no_of_contestants_in_raceclass": 80,
        "max_no_of_contestants_in_race": 10,
        "datatype": "individual_sprint",
    }


@pytest.mark.integration
async def test_create_competition_format_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return Created, location header."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )

    request_body = competition_format_interval_start

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert f"/competition-formats/{ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_create_competition_format_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_individual_sprint: dict,
) -> None:
    """Should return Created, location header."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )

    request_body = competition_format_individual_sprint

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert f"/competition-formats/{ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_competition_format_interval_start_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return OK, and a body containing one competition_format."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/competition-formats/{ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == ID
        assert body["name"] == competition_format_interval_start["name"]
        assert (
            body["starting_order"]
            == competition_format_interval_start["starting_order"]
        )
        assert (
            body["start_procedure"]
            == competition_format_interval_start["start_procedure"]
        )
        assert body["intervals"] == competition_format_interval_start["intervals"]


@pytest.mark.integration
async def test_get_competition_format_individual_sprint_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_individual_sprint: dict,
) -> None:
    """Should return OK, and a body containing one competition_format."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_individual_sprint,  # type: ignore
    )

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/competition-formats/{ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == ID
        assert body["name"] == competition_format_individual_sprint["name"]
        assert (
            body["starting_order"]
            == competition_format_individual_sprint["starting_order"]
        )
        assert (
            body["start_procedure"]
            == competition_format_individual_sprint["start_procedure"]
        )
        assert (
            body["time_between_rounds"]
            == competition_format_individual_sprint["time_between_rounds"]
        )
        assert (
            body["time_between_heats"]
            == competition_format_individual_sprint["time_between_heats"]
        )
        assert (
            body["max_no_of_contestants_in_raceclass"]
            == competition_format_individual_sprint[
                "max_no_of_contestants_in_raceclass"
            ]
        )
        assert (
            body["max_no_of_contestants_in_race"]
            == competition_format_individual_sprint["max_no_of_contestants_in_race"]
        )


@pytest.mark.integration
async def test_get_competition_formats_by_name(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return OK, and a body containing one competition_format."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    NAME = competition_format_interval_start["name"]
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[{"id": ID} | competition_format_interval_start],  # type: ignore
    )

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/competition-formats?name={NAME}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert body[0]["id"] == ID
        assert body[0]["name"] == competition_format_interval_start["name"]
        assert (
            body[0]["starting_order"]
            == competition_format_interval_start["starting_order"]
        )
        assert (
            body[0]["start_procedure"]
            == competition_format_interval_start["start_procedure"]
        )
        assert body[0]["intervals"] == competition_format_interval_start["intervals"]


@pytest.mark.integration
async def test_get_competition_formats_by_name_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_individual_sprint: dict,
) -> None:
    """Should return OK, and a body containing one competition_format."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    NAME = competition_format_individual_sprint["name"]
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[{"id": ID} | competition_format_individual_sprint],  # type: ignore
    )

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/competition-formats?name={NAME}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert body[0]["id"] == ID
        assert body[0]["name"] == competition_format_individual_sprint["name"]
        assert (
            body[0]["starting_order"]
            == competition_format_individual_sprint["starting_order"]
        )
        assert (
            body[0]["start_procedure"]
            == competition_format_individual_sprint["start_procedure"]
        )
        assert (
            body[0]["time_between_rounds"]
            == competition_format_individual_sprint["time_between_rounds"]
        )
        assert (
            body[0]["time_between_heats"]
            == competition_format_individual_sprint["time_between_heats"]
        )
        assert (
            body[0]["max_no_of_contestants_in_raceclass"]
            == competition_format_individual_sprint[
                "max_no_of_contestants_in_raceclass"
            ]
        )
        assert (
            body[0]["max_no_of_contestants_in_race"]
            == competition_format_individual_sprint["max_no_of_contestants_in_race"]
        )


@pytest.mark.integration
async def test_update_competition_format_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.update_competition_format",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    new_name = "Oslo Skagen competition format"
    request_body = deepcopy(competition_format_interval_start)
    request_body["id"] = ID
    request_body["name"] = new_name

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/competition-formats/{ID}", headers=headers, json=request_body
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_update_competition_format_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_individual_sprint: dict,
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_individual_sprint,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.update_competition_format",  # noqa: B950
        return_value={"id": ID} | competition_format_individual_sprint,  # type: ignore
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    new_name = "Oslo Skagen competition format"
    request_body = deepcopy(competition_format_individual_sprint)
    request_body["id"] = ID
    request_body["name"] = new_name

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/competition-formats/{ID}", headers=headers, json=request_body
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_competition_formats(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
    competition_format_individual_sprint: dict,
) -> None:
    """Should return OK and a valid json body."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_all_competition_formats",  # noqa: B950
        return_value=[
            {"id": ID} | competition_format_interval_start,  # type: ignore
            {"id": ID} | competition_format_individual_sprint,  # type: ignore
        ],
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get("/competition-formats", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) > 0
        assert ID == body[0]["id"]


@pytest.mark.integration
async def test_delete_competition_format_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.delete_competition_format",  # noqa: B950
        return_value=ID,
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.delete(f"/competition-formats/{ID}", headers=headers)
        assert resp.status == 204


# Bad cases


@pytest.mark.integration
async def test_create_competition_format_interval_start_allready_exist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 422 HTTPUnprocessable entity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[{id: ID} | competition_format_interval_start],  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )

    request_body = competition_format_interval_start

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats", headers=headers, json=request_body
        )
        assert resp.status == 422


# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_competition_format_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[{"id": ID} | competition_format_interval_start],  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )
    request_body = {"optional_property": "Optional_property"}
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_competition_format_with_input_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[{"id": ID} | competition_format_interval_start],  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )
    request_body = {"id": ID} | competition_format_interval_start  # type: ignore
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_competition_format_adapter_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=None,
    )
    request_body = competition_format_interval_start
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats", headers=headers, json=request_body
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_update_competition_format_by_id_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.update_competition_format",  # noqa: B950
        return_value=ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {"id": ID, "optional_property": "Optional_property"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/competition-formats/{ID}", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_competition_format_by_id_different_id_in_body(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.update_competition_format",  # noqa: B950
        return_value=ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {"id": "different_id"} | competition_format_interval_start  # type: ignore

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/competition-formats/{ID}", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_competition_format_invalid_intervals(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )

    competition_format_with_invalid_intervals = deepcopy(
        competition_format_interval_start
    )
    competition_format_with_invalid_intervals["intervals"] = "99:99:99"

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats",
            headers=headers,
            json=competition_format_with_invalid_intervals,
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_create_competition_format_invalid_time_between_groups(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )

    competition_format_with_invalid_time_between_groups = deepcopy(
        competition_format_interval_start
    )
    competition_format_with_invalid_time_between_groups[
        "time_between_groups"
    ] = "99:99:99"

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats",
            headers=headers,
            json=competition_format_with_invalid_time_between_groups,
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_create_competition_format_invalid_time_between_rounds(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_individual_sprint: dict,
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )

    competition_format_with_invalid_time_between_rounds = deepcopy(
        competition_format_individual_sprint
    )
    competition_format_with_invalid_time_between_rounds[
        "time_between_rounds"
    ] = "99:99:99"

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats",
            headers=headers,
            json=competition_format_with_invalid_time_between_rounds,
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_create_competition_format_invalid_time_between_heats(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_individual_sprint: dict,
) -> None:
    """Should return 400 Bad request."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )

    competition_format_with_invalid_time_between_heats = deepcopy(
        competition_format_individual_sprint
    )
    competition_format_with_invalid_time_between_heats[
        "time_between_heats"
    ] = "99:99:99"

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/competition-formats",
            headers=headers,
            json=competition_format_with_invalid_time_between_heats,
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_update_competition_format_invalid_interval(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.update_competition_format",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    updated_competition_format = deepcopy(competition_format_interval_start)
    updated_competition_format["id"] = ID
    updated_competition_format["intervals"] = "99:99:99"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/competition-formats/{ID}",
            headers=headers,
            json=updated_competition_format,
        )
        assert resp.status == 400


# Unauthorized cases:


@pytest.mark.integration
async def test_create_competition_format_no_authorization(
    client: _TestClient, mocker: MockFixture, competition_format_interval_start: dict
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[{"id": ID} | competition_format_interval_start],  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )

    request_body = {"name": "Oslo Skagen sprint"}
    headers = MultiDict([(hdrs.CONTENT_TYPE, "application/json")])

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post(
            "/competition-formats", headers=headers, json=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_get_competition_format_by_id_no_authorization(
    client: _TestClient,
    mocker: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.get(f"/competition-formats/{ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_update_competition_format_by_id_no_authorization(
    client: _TestClient,
    mocker: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value={"id": ID} | competition_format_interval_start,  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.update_competition_format",  # noqa: B950
        return_value=ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
    }

    request_body = {"id": ID, "name": "Oslo Skagen sprint Oppdatert"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.put(
            f"/competition-formats/{ID}", headers=headers, json=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_competition_formats_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_all_competition_formats",  # noqa: B950
        return_value=[{"id": ID, "name": "Oslo Skagen Sprint"}],
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get("/competition-formats")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_competition_format_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.delete_competition_format",  # noqa: B950
        return_value=ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.delete(f"/competition-formats/{ID}")
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_competition_format_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 403 Forbidden."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.competition_formats_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[{"id": ID} | competition_format_interval_start],  # type: ignore
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.create_competition_format",  # noqa: B950
        return_value=ID,
    )
    request_body = {"name": "Oslo Skagen sprint"}
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=403)
        resp = await client.post(
            "/competition-formats", headers=headers, json=request_body
        )
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_competition_format_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value=None,
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/competition-formats/{ID}", headers=headers)
        assert resp.status == 404


@pytest.mark.integration
async def test_get_competition_formats_by_name_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 200 OK and empty list."""
    NAME = "does-not-exist"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_formats_by_name",  # noqa: B950
        return_value=[],
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/competition-formats?name={NAME}", headers=headers)
        assert resp.status == 200
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 0


@pytest.mark.integration
async def test_update_competition_format_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    competition_format_interval_start: dict,
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.update_competition_format",  # noqa: B950
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = competition_format_interval_start

    ID = "does-not-exist"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/competition-formats/{ID}", headers=headers, json=request_body
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_competition_format_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.get_competition_format_by_id",  # noqa: B950
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.competition_formats_adapter.CompetitionFormatsAdapter.delete_competition_format",  # noqa: B950
        return_value=None,
    )

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(f"/competition-formats/{ID}", headers=headers)
        assert resp.status == 404
