"""Module for competition_format adapter."""
import logging
from typing import Any, List, Optional

from .adapter import Adapter


class CompetitionFormatsAdapter(Adapter):
    """Class representing an adapter for competition_formats."""

    @classmethod
    async def get_all_competition_formats(
        cls: Any, db: Any
    ) -> List:  # pragma: no cover
        """Get all competition_formats function."""
        competition_formats: List = []
        cursor = db.competition_formats_collection.find()
        for competition_format in await cursor.to_list(None):
            competition_formats.append(competition_format)
        return competition_formats

    @classmethod
    async def create_competition_format(
        cls: Any, db: Any, competition_format: dict
    ) -> str:  # pragma: no cover
        """Create competition_format function."""
        result = await db.competition_formats_collection.insert_one(competition_format)
        return result

    @classmethod
    async def get_competition_format_by_id(
        cls: Any, db: Any, id: str
    ) -> dict:  # pragma: no cover
        """Get competition_format by idfunction."""
        result = await db.competition_formats_collection.find_one({"id": id})
        return result

    @classmethod
    async def get_competition_formats_by_name(
        cls: Any, db: Any, competition_format_name: str
    ) -> List[dict]:  # pragma: no cover
        """Get competition_format by name function."""
        logging.debug(f"Got request for name {competition_format_name}.")
        competition_formats: List = []
        query = {"$regex": f".*{competition_format_name}.*", "$options": "i"}
        logging.debug(f"Query: {query}.")
        cursor = db.competition_formats_collection.find({"name": query})
        for competition_format in await cursor.to_list(None):
            logging.debug(f"cursor - competition_format: {competition_format}")
            competition_formats.append(competition_format)
        return competition_formats

    @classmethod
    async def update_competition_format(
        cls: Any, db: Any, id: str, competition_format: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get competition_format function."""
        result = await db.competition_formats_collection.replace_one(
            {"id": id}, competition_format
        )
        return result

    @classmethod
    async def delete_competition_format(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get competition_format function."""
        result = await db.competition_formats_collection.delete_one({"id": id})
        return result
