"""Module util validate ageclass."""

import re

from event_service.services.exceptions import (
    IllegalValueError,
)


async def validate_ageclass(ageclass: str) -> None:
    """Validator function for raceclasses."""
    # Check that ageclass is valid against following regexes:
    global_flags = r"(?i)"
    regex_JGMK = r"([JGMK]\s\d*\/?\d+?\s?(år)?)"  # noqa: N806
    regex_Gutter = r"(\bGutter\b\s\d*\/?\d+?\s?(år)?)"  # noqa: N806
    regex_Jenter = r"(\bJenter\b\s\d*\/?\d+?\s?(år)?)"  # noqa: N806
    regex_junior = r"((\bKvinner\b|\bMenn\b)\s\d*\/?\d+?\s?(år)?)"
    regex_senior = r"((\bKvinner\b|\bMenn\b) \bsenior\b)"
    regex_Felles = r"((\bFelles\b))"  # noqa: N806
    regex_Para = r"((\bPara\b))"  # noqa: N806
    pattern = re.compile(
        global_flags
        + regex_JGMK
        + "|"
        + regex_Gutter
        + "|"
        + regex_Jenter
        + "|"
        + regex_junior
        + "|"
        + regex_senior
        + "|"
        + regex_Felles
        + "|"
        + regex_Para
    )
    if not pattern.match(ageclass):
        msg = f"Ageclass {ageclass!r} is not valid. Must be of the form 'Jenter 12 år' 'J 12 år', 'J 12/13 år', 'Kvinner 18-19', 'Kvinner senior', 'Felles' or 'Para'."
        raise IllegalValueError(msg)
