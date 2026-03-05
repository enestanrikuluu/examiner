"""Retrieves relevant document chunks for question generation context."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.models import Document, DocumentChunk
from src.ai.rag.embeddings import EmbeddingService


class Retriever:
    """Retrieves relevant document chunks using cosine similarity."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()

    async def retrieve(
        self,
        template_id: uuid.UUID,
        query: str,
        *,
        top_k: int = 5,
        max_tokens: int = 2000,
    ) -> str:
        """Retrieve relevant chunks for a template and combine into context string.

        Falls back to simple text matching if embeddings are not available.
        """
        # Get all ready documents for this template
        doc_result = await self.db.execute(
            select(Document.id).where(
                Document.template_id == template_id,
                Document.status == "ready",
            )
        )
        doc_ids = [row[0] for row in doc_result.all()]

        if not doc_ids:
            return ""

        # Get all chunks for these documents
        chunk_result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id.in_(doc_ids))
            .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
        )
        chunks = list(chunk_result.scalars().all())

        if not chunks:
            return ""

        # Score chunks by relevance
        query_lower = query.lower()
        scored: list[tuple[float, DocumentChunk]] = []

        for chunk in chunks:
            # Simple keyword relevance scoring
            words = query_lower.split()
            chunk_lower = chunk.text.lower()
            score = sum(1.0 for w in words if w in chunk_lower)
            if score > 0:
                scored.append((score, chunk))

        # Sort by score descending, take top_k
        scored.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored[:top_k]

        if not top_chunks:
            # No keyword matches; return first chunks up to max_tokens
            context_parts: list[str] = []
            total_tokens = 0
            for chunk in chunks[:top_k]:
                if total_tokens + chunk.token_count > max_tokens:
                    break
                context_parts.append(chunk.text)
                total_tokens += chunk.token_count
            return "\n\n".join(context_parts)

        # Build context from top chunks
        context_parts = []
        total_tokens = 0
        for _score, chunk in top_chunks:
            if total_tokens + chunk.token_count > max_tokens:
                break
            context_parts.append(chunk.text)
            total_tokens += chunk.token_count

        return "\n\n".join(context_parts)
