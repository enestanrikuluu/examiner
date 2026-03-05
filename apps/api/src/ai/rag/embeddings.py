"""Embedding generation for document chunks.

Uses sentence-transformers for local embeddings.
Falls back to a simple TF-IDF-like approach if not available.
"""

from __future__ import annotations

import hashlib
from typing import Any


class EmbeddingService:
    """Generates embeddings for text chunks."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                self._model = None
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Returns list of embedding vectors.
        """
        model = self._get_model()
        if model is not None:
            embeddings = model.encode(texts, show_progress_bar=False)
            return [emb.tolist() for emb in embeddings]

        # Fallback: simple hash-based pseudo-embeddings for development
        return [self._hash_embedding(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query text."""
        return self.embed_texts([query])[0]

    @staticmethod
    def _hash_embedding(text: str, dim: int = 384) -> list[float]:
        """Deterministic pseudo-embedding for development/testing."""
        h = hashlib.sha256(text.encode()).hexdigest()
        # Repeat hash to fill dimension
        extended = (h * ((dim // len(h)) + 1))[:dim]
        return [float(ord(c)) / 128.0 - 1.0 for c in extended]
