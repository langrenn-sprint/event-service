"""Unit test cases for the create_raceclass_name function."""

import pytest
import pytest_asyncio
from pytest_mock import MockFixture

from event_service.commands.events_commands import (
    _assign_default_values_to_raceclasses,
)

from event_service.adapters import RaceclassesConfigAdapter
from event_service.models.raceclass_model import Raceclass
from event_service.models.raceclasses_config_model import RaceclassesConfig


@pytest_asyncio.fixture()
async def default_raceclasses_config() -> RaceclassesConfig:
    """Fixture for default RaceclassesConfig."""
    default_raceclasses_config = (
        await RaceclassesConfigAdapter.get_default_raceclasses_config()
    )
    return RaceclassesConfig(**default_raceclasses_config)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_assign_default_values_to_raceclasses_empty_list(
    default_raceclasses_config,
    mocker: MockFixture,
):
    """Should return empty list when input list is empty."""
    raceclasses = []
    result = _assign_default_values_to_raceclasses(
        default_raceclasses_config, raceclasses
    )
    assert result == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_assign_default_values_to_raceclasses_two_ageclasses(
    default_raceclasses_config,
    mocker: MockFixture,
):
    """Should return list with reverse order when two raceclasses are given."""
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )
    raceclasses = [
        Raceclass(name="J15", ageclasses=["15"], event_id="event1"),
        Raceclass(name="G15", ageclasses=["16"], event_id="event1"),
        Raceclass(name="J16", ageclasses=["16"], event_id="event1"),
        Raceclass(name="G16", ageclasses=["16"], event_id="event1"),
    ]
    result = _assign_default_values_to_raceclasses(
        default_raceclasses_config, raceclasses
    )
    # Check order:
    assert result[0].name == "G16"
    assert result[1].name == "J16"
    assert result[2].name == "G15"
    assert result[3].name == "J15"
    # Check groups:
    assert result[0].group == 1
    assert result[1].group == 1
    assert result[2].group == 2
    assert result[3].group == 2
    # Check order:
    assert result[0].order == 1
    assert result[1].order == 2
    assert result[2].order == 1
    assert result[3].order == 2
    # Check ranking:
    assert result[0].ranking is True
    assert result[1].ranking is True
    assert result[2].ranking is True
    assert result[3].ranking is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_assign_default_values_to_raceclasses_three_ageclasses_and_one_unranked(
    default_raceclasses_config, mocker: MockFixture
):
    """Should return list with reverse order when three raceclasses are given."""
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )
    raceclasses = [
        Raceclass(name="J15", ageclasses=["15"], event_id="event1"),
        Raceclass(name="G15", ageclasses=["16"], event_id="event1"),
        Raceclass(name="J16", ageclasses=["16"], event_id="event1"),
        Raceclass(name="G16", ageclasses=["16"], event_id="event1"),
        Raceclass(name="J8", ageclasses=["8"], event_id="event1"),
        Raceclass(name="G8", ageclasses=["8"], event_id="event1"),
    ]
    result = _assign_default_values_to_raceclasses(
        default_raceclasses_config, raceclasses
    )
    # Check order:
    assert result[0].name == "G16"
    assert result[1].name == "J16"
    assert result[2].name == "G15"
    assert result[3].name == "J15"
    assert result[4].name == "G8"
    assert result[5].name == "J8"
    # Check groups:
    assert result[0].group == 1
    assert result[1].group == 1
    assert result[2].group == 2
    assert result[3].group == 2
    assert result[4].group == 3
    assert result[5].group == 3
    # Check order:
    assert result[0].order == 1
    assert result[1].order == 2
    assert result[2].order == 1
    assert result[3].order == 2
    assert result[4].order == 1
    assert result[5].order == 2
    # Check ranking:
    assert result[0].ranking is True
    assert result[1].ranking is True
    assert result[2].ranking is True
    assert result[3].ranking is True
    assert result[4].ranking is False
    assert result[5].ranking is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_assign_default_values_to_raceclasses_all(
    default_raceclasses_config, mocker: MockFixture
):
    """Should return list with correct order when all raceclasses are given."""
    mocker.patch(
        "event_service.adapters.contestants_adapter.ContestantsAdapter.get_all_contestants",
        return_value=[],
    )
    raceclasses = [
        Raceclass(name="J15", ageclasses=["J 15 år"], event_id="event1"),
        Raceclass(name="G15", ageclasses=["G 16 år"], event_id="event1"),
        Raceclass(name="J16", ageclasses=["J 16 år"], event_id="event1"),
        Raceclass(name="G16", ageclasses=["G 16 år"], event_id="event1"),
        Raceclass(name="J8", ageclasses=["J 8 år"], event_id="event1"),
        Raceclass(name="G8", ageclasses=["G 8 år"], event_id="event1"),
        Raceclass(name="J9", ageclasses=["J 9 år"], event_id="event1"),
        Raceclass(name="G9", ageclasses=["G 9 år"], event_id="event1"),
        Raceclass(name="J10", ageclasses=["J 10 år"], event_id="event1"),
        Raceclass(name="G10", ageclasses=["G 10 år"], event_id="event1"),
        Raceclass(name="J11", ageclasses=["J 11 år"], event_id="event1"),
        Raceclass(name="G11", ageclasses=["G 11 år"], event_id="event1"),
        Raceclass(name="J12", ageclasses=["J 12 år"], event_id="event1"),
        Raceclass(name="G12", ageclasses=["G 12 år"], event_id="event1"),
        Raceclass(name="J13", ageclasses=["J 13 år"], event_id="event1"),
        Raceclass(name="G13", ageclasses=["G 13 år"], event_id="event1"),
        Raceclass(name="J14", ageclasses=["J 14 år"], event_id="event1"),
        Raceclass(name="G14", ageclasses=["G 14 år"], event_id="event1"),
        Raceclass(name="KS", ageclasses=["Kvinner senior"], event_id="event1"),
        Raceclass(name="MS", ageclasses=["Menn senior"], event_id="event_id"),
        Raceclass(name="K19-20", ageclasses=["Kvinner 19-20"], event_id="event1"),
        Raceclass(name="M19-20", ageclasses=["Menn 19-20"], event_id="event1"),
        Raceclass(name="K18", ageclasses=["Kvinner 18"], event_id="event1"),
        Raceclass(name="M18", ageclasses=["Menn 18"], event_id="event1"),
        Raceclass(name="K17", ageclasses=["Kvinner 17"], event_id="event1"),
        Raceclass(name="M17", ageclasses=["Menn 17"], event_id="event1"),
    ]
    result = _assign_default_values_to_raceclasses(
        default_raceclasses_config, raceclasses
    )
    # Check order:
    assert result[0].name == "MS"
    assert result[1].name == "KS"
    assert result[2].name == "M19-20"
    assert result[3].name == "K19-20"
    assert result[4].name == "M18"
    assert result[5].name == "K18"
    assert result[6].name == "M17"
    assert result[7].name == "K17"
    assert result[8].name == "G16"
    assert result[9].name == "J16"
    assert result[10].name == "G15"
    assert result[11].name == "J15"
    assert result[12].name == "G14"
    assert result[13].name == "J14"
    assert result[14].name == "G13"
    assert result[15].name == "J13"
    assert result[16].name == "G12"
    assert result[17].name == "J12"
    assert result[18].name == "G11"
    assert result[19].name == "J11"
    assert result[20].name == "G10"
    assert result[21].name == "J10"
    assert result[22].name == "G9"
    assert result[23].name == "J9"
    assert result[24].name == "G8"
    assert result[25].name == "J8"
    # Check groups, orders and rankings::
    # MS
    assert result[0].group == 1
    assert result[0].order == 1
    assert result[0].ranking is True
    # KS
    assert result[1].group == 1
    assert result[1].order == 2
    assert result[1].ranking is True
    # M19-20
    assert result[2].group == 2
    assert result[2].order == 1
    assert result[2].ranking is True
    # K19-20
    assert result[3].group == 2
    assert result[3].order == 2
    assert result[3].ranking is True
    # M18
    assert result[4].group == 3
    assert result[4].order == 1
    assert result[4].ranking is True
    # K18
    assert result[5].group == 3
    assert result[5].order == 2
    assert result[5].ranking is True
    # M17
    assert result[6].group == 4
    assert result[6].order == 1
    assert result[6].ranking is True
    # K17
    assert result[7].group == 4
    assert result[7].order == 2
    assert result[7].ranking is True
    # G16
    assert result[8].group == 5
    assert result[8].order == 1
    assert result[8].ranking is True
    # J16
    assert result[9].group == 5
    assert result[9].order == 2
    assert result[9].ranking is True
    # G15
    assert result[10].group == 6
    assert result[10].order == 1
    assert result[10].ranking is True
    # J15
    assert result[11].group == 6
    assert result[11].order == 2
    assert result[11].ranking is True
    # G14
    assert result[12].group == 7
    assert result[12].order == 1
    assert result[12].ranking is True
    # J14
    assert result[13].group == 7
    assert result[13].order == 2
    assert result[13].ranking is True
    # G13
    assert result[14].group == 8
    assert result[14].order == 1
    assert result[14].ranking is True
    # J13
    assert result[15].group == 8
    assert result[15].order == 2
    assert result[15].ranking is True
    # G12
    assert result[16].group == 9
    assert result[16].order == 1
    assert result[16].ranking is True
    # J12
    assert result[17].group == 9
    assert result[17].order == 2
    assert result[17].ranking is True
    # G11
    assert result[18].group == 10
    assert result[18].order == 1
    assert result[18].ranking is True
    # J11
    assert result[19].group == 10
    assert result[19].order == 2
    assert result[19].ranking is True
    # G10
    assert result[20].group == 11
    assert result[20].order == 1
    assert result[20].ranking is False
    # J10
    assert result[21].group == 11
    assert result[21].order == 2
    assert result[21].ranking is False
    # G9
    assert result[22].group == 12
    assert result[22].order == 1
    assert result[22].ranking is False
    # J9
    assert result[23].group == 12
    assert result[23].order == 2
    assert result[23].ranking is False
    # G8
    assert result[24].group == 13
    assert result[24].order == 1
    assert result[24].ranking is False
    # J8
    assert result[25].group == 13
    assert result[25].order == 2
    assert result[25].ranking is False
