"""Unit test cases for the validate_ageclass function."""

import pytest

from event_service.services.contestants_service import (
    validate_ageclass,
)
from event_service.services.exceptions import IllegalValueError

# Should be valid and not raise exception


# Sportsadmin:
@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "G 15 år"
    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_combined() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "G 15/16 år"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_Para() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Para"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_Felles() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Felles"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_G_10() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "G 10"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


# iSonen:


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Gutter_9() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Gutter 9"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Jenter_9() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Jenter 9"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Gutter_15() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Gutter 15"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Jenter_15() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Jenter 15"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Menn_17() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Menn 17"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Kvinner_17() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Kvinner 17"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Menn_19_20() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Menn 19-20"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Kvinner_19_20() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Kvinner 19-20"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Menn_senior() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Menn senior"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should not raise IllegalValueError")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Kvinner_senior() -> None:
    """Should not raise IllegalValueError."""
    ageclass = "Kvinner senior"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueError:
        pytest.fail(f"{ageclass!r} should should not raise IllegalValueError")


# Is invalid and should raise exception
@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_Kvinner_junior() -> None:
    """Should raise not IllegalValueError."""
    ageclass = "Kvinner junior"

    with pytest.raises(IllegalValueError):
        await validate_ageclass(ageclass)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_Menn_junior() -> None:
    """Should raise not IllegalValueError."""
    ageclass = "Menn junior"

    with pytest.raises(IllegalValueError):
        await validate_ageclass(ageclass)
