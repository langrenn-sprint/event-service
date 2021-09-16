"""Module for event adapter."""
from abc import ABC, abstractmethod
from typing import Any, List, Optional


class Adapter(ABC):
    """Class representing an adapter interface."""

    @classmethod
    @abstractmethod
    async def get_all_events(cls: Any, db: Any) -> List:  # pragma: no cover
        """Get all events function."""
        raise NotImplementedError() from None

    @classmethod
    @abstractmethod
    async def create_event(cls: Any, db: Any, event: dict) -> str:  # pragma: no cover
        """Create event function."""
        raise NotImplementedError() from None

    @classmethod
    @abstractmethod
    async def get_event_by_id(cls: Any, db: Any, id: str) -> dict:  # pragma: no cover
        """Get event by id function."""
        raise NotImplementedError() from None

    @classmethod
    @abstractmethod
    async def get_event_by_name(
        cls: Any, db: Any, name: str
    ) -> dict:  # pragma: no cover
        """Get event function."""
        raise NotImplementedError() from None

    @classmethod
    @abstractmethod
    async def update_event(
        cls: Any, db: Any, id: str, event: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get event function."""
        raise NotImplementedError() from None

    @classmethod
    @abstractmethod
    async def delete_event(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get event function."""
        raise NotImplementedError() from None
