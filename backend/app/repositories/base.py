"""
Generic repository base class.

API routes and business logic should depend on a repository,
never on a raw AsyncIOMotorCollection.

The repository is responsible for:
- inserting Pydantic models into MongoDB
- retrieving documents
- validating MongoDB documents back into Pydantic models
- updating documents
- deleting documents
- counting documents
"""

from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel


ModelT = TypeVar(
    "ModelT",
    bound=BaseModel,
)


class BaseRepository(Generic[ModelT]):
    """
    Thin, typed CRUD wrapper around a MongoDB collection.

    Every repository created from this class works with a specific
    Pydantic domain model.
    """

    def __init__(
        self,
        collection: AsyncIOMotorCollection,
        model: Type[ModelT],
    ) -> None:
        self._collection = collection
        self._model = model

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    @staticmethod
    def _clean_document(
        document: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Remove MongoDB's internal `_id` field before validating
        the document with the Pydantic domain model.

        RecoverAI uses its own string `id` field as the business ID.
        """

        if document is None:
            return None

        document.pop("_id", None)

        return document

    def _validate(
        self,
        document: Optional[Dict[str, Any]],
    ) -> Optional[ModelT]:
        """
        Convert a MongoDB document into the configured Pydantic model.
        """

        cleaned = self._clean_document(document)

        if cleaned is None:
            return None

        return self._model.model_validate(cleaned)

    # =========================================================
    # CREATE
    # =========================================================

    async def insert(
        self,
        item: ModelT,
    ) -> ModelT:
        """
        Insert a new Pydantic model into MongoDB.

        Returns the same validated model after insertion.
        """

        document = item.model_dump(
            mode="python",
        )

        await self._collection.insert_one(
            document,
        )

        return item

    # =========================================================
    # READ - SINGLE
    # =========================================================

    async def find_by_id(
        self,
        item_id: str,
    ) -> Optional[ModelT]:
        """
        Find one document using RecoverAI's business `id`.
        """

        document = await self._collection.find_one(
            {
                "id": item_id,
            }
        )

        return self._validate(document)

    async def find_one(
        self,
        filter_query: Dict[str, Any],
    ) -> Optional[ModelT]:
        """
        Find one document using an arbitrary MongoDB filter.
        """

        document = await self._collection.find_one(
            filter_query,
        )

        return self._validate(document)

    # =========================================================
    # READ - MANY
    # =========================================================

    async def find_many(
        self,
        filter_query: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[ModelT]:
        """
        Return documents matching the supplied filter.

        Args:
            filter_query:
                MongoDB filter. Defaults to all documents.

            limit:
                Maximum number of documents returned.
        """

        if limit < 1:
            return []

        cursor = (
            self._collection
            .find(filter_query or {})
            .limit(limit)
        )

        results: List[ModelT] = []

        async for document in cursor:
            validated = self._validate(document)

            if validated is not None:
                results.append(validated)

        return results

    # =========================================================
    # COUNT
    # =========================================================

    async def count(
        self,
        filter_query: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count documents matching the supplied filter.
        """

        return await self._collection.count_documents(
            filter_query or {},
        )

    # =========================================================
    # UPDATE
    # =========================================================

    async def update_by_id(
        self,
        item_id: str,
        updates: Dict[str, Any],
    ) -> Optional[ModelT]:
        """
        Update fields of a document identified by its business ID.

        Returns the updated Pydantic model.

        Returns None when no document with the supplied ID exists.
        """

        if not updates:
            return await self.find_by_id(item_id)

        # Never allow callers to accidentally replace the business ID.
        updates = dict(updates)
        updates.pop("id", None)
        updates.pop("_id", None)

        result = await self._collection.update_one(
            {
                "id": item_id,
            },
            {
                "$set": updates,
            },
        )

        if result.matched_count == 0:
            return None

        return await self.find_by_id(item_id)

    # =========================================================
    # DELETE
    # =========================================================

    async def delete_by_id(
        self,
        item_id: str,
    ) -> bool:
        """
        Delete a document using RecoverAI's business ID.

        Returns:
            True  -> document was deleted
            False -> document was not found
        """

        result = await self._collection.delete_one(
            {
                "id": item_id,
            }
        )

        return result.deleted_count > 0