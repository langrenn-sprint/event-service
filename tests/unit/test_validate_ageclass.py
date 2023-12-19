"""Unit test cases for the validate_ageclass function."""
import pytest

from event_service.services.contestants_service import (
    validate_ageclass,
)
from event_service.services.exceptions import IllegalValueException


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass() -> None:
    """Should not raise exception."""
    ageclass = "G 15 år"
    try:
        await validate_ageclass(ageclass)
    except IllegalValueException:
        pytest.fail("Should not raise IllegalValueException")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_combined() -> None:
    """Should not raise exception."""
    ageclass = "G 15/16 år"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueException:
        pytest.fail("Should not raise IllegalValueException")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Gutter() -> None:
    """Should not raise exception."""
    ageclass = "Gutter 15 år"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueException:
        pytest.fail("Should not raise IllegalValueException")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_Jenter() -> None:
    """Should not raise exception."""
    ageclass = "Jenter 15 år"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueException:
        pytest.fail("Should not raise IllegalValueException")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_Kvinner_junior() -> None:
    """Should raise not IllegalValueException."""
    ageclass = "Kvinner junior"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueException:
        pytest.fail("Should not raise IllegalValueException")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_Menn_junior() -> None:
    """Should raise not IllegalValueException."""
    ageclass = "Menn junior"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueException:
        pytest.fail("Should not raise IllegalValueException")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_Para() -> None:
    """Should raise not IllegalValueException."""
    ageclass = "Para"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueException:
        pytest.fail("Should not raise IllegalValueException")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_Felles() -> None:
    """Should raise not IllegalValueException."""
    ageclass = "Felles"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueException:
        pytest.fail("Should not raise IllegalValueException")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_ageclass_ageclass_G_10() -> None:
    """Should raise not IllegalValueException."""
    ageclass = "G 10"

    try:
        await validate_ageclass(ageclass)
    except IllegalValueException:
        pytest.fail("Should not raise IllegalValueException")
