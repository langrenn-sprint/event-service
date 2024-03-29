"""Module for service exceptions."""


class IllegalValueException(Exception):
    """Class representing custom exception for create method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InvalidDateFormatException(Exception):
    """Class representing custom exception for date time methods."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InvalidTimezoneException(Exception):
    """Class representing custom exception for date time methods."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceclassNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class CompetitionFormatNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class BibAlreadyInUseException(Exception):
    """Class representing custom exception for create method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor
