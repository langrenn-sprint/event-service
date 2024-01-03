"""Unit test cases for the create_raceclass_name function."""
import pytest

from event_service.commands.events_commands import (
    _create_raceclass_name,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_empty_string() -> None:
    """Should return empty string."""
    raceclass_name = _create_raceclass_name("")

    assert raceclass_name == ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_G_10_år() -> None:
    """Should return "G10"."""
    raceclass_name = _create_raceclass_name("G 10 år")

    assert raceclass_name == "G10"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_J_10_år() -> None:
    """Should return "J10"."""
    raceclass_name = _create_raceclass_name("J 10 år")

    assert raceclass_name == "J10"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Para() -> None:
    """Should return "P"."""
    raceclass_name = _create_raceclass_name("Para")

    assert raceclass_name == "P"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Felles() -> None:
    """Should return "P"."""
    raceclass_name = _create_raceclass_name("Felles")

    assert raceclass_name == "F"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Jenter_10_år() -> None:
    """Should return "J10"."""
    raceclass_name = _create_raceclass_name("Jenter 10 år")

    assert raceclass_name == "J10"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Gutter_9_år() -> None:
    """Should return "G9"."""
    raceclass_name = _create_raceclass_name("Gutter 9 år")

    assert raceclass_name == "G9"


# iSonen:
@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Menn_17() -> None:
    """Should return "G9"."""
    raceclass_name = _create_raceclass_name("Menn 17")

    assert raceclass_name == "M17"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Kvinner_17() -> None:
    """Should return "G9"."""
    raceclass_name = _create_raceclass_name("Kvinner 17")

    assert raceclass_name == "K17"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Menn_19_20() -> None:
    """Should return "G9"."""
    raceclass_name = _create_raceclass_name("Menn 19-20")

    assert raceclass_name == "M19-20"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Kvinner_19_20() -> None:
    """Should return "G9"."""
    raceclass_name = _create_raceclass_name("Kvinner 19-20")

    assert raceclass_name == "K19-20"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Menn_senior() -> None:
    """Should return "G9"."""
    raceclass_name = _create_raceclass_name("Menn senior")

    assert raceclass_name == "MS"


@pytest.mark.unit
@pytest.mark.asyncio
async def test__create_raceclass_name_Kvinner_senior() -> None:
    """Should return "G9"."""
    raceclass_name = _create_raceclass_name("Kvinner senior")
    assert raceclass_name == "KS"
