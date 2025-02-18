"""Module for service exceptions."""


class IllegalValueError(Exception):
    """Class representing custom exception for create method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InvalidDateFormatError(Exception):
    """Class representing custom exception for date time methods."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InvalidTimezoneError(Exception):
    """Class representing custom exception for date time methods."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceclassNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class CompetitionFormatNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class BibAlreadyInUseError(Exception):
    """Class representing custom exception for create method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor
