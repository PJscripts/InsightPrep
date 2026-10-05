"""Lazy, fail-open local embedding boundary for future RAG retrieval."""

import logging
import math
from collections.abc import Callable
from typing import Any, Protocol

from app.services.rag.types import (
    EmbeddingFailureCode,
    EmbeddingResult,
)

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIMENSIONS = 384


class SentenceTransformerModel(Protocol):
    """Small subset used from sentence-transformers, kept testable."""

    def encode(
        self,
        sentences: list[str],
        *,
        normalize_embeddings: bool,
    ) -> Any: ...


ModelLoader = Callable[[str], SentenceTransformerModel]


def load_sentence_transformer(model_name: str) -> SentenceTransformerModel:
    """Import the optional dependency only when embeddings are requested."""

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class LocalSentenceTransformerEmbeddingProvider:
    """Generate local embeddings without making the application depend on them."""

    def __init__(
        self,
        *,
        enabled: bool,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
        model_loader: ModelLoader = load_sentence_transformer,
    ) -> None:
        self.enabled = enabled
        self.model_name = model_name
        self.dimensions = dimensions
        self._model_loader = model_loader
        self._model: SentenceTransformerModel | None = None

    def embed(self, text: str) -> EmbeddingResult:
        """Return an embedding result; unexpected errors are always fail-open."""

        if not self.enabled:
            return EmbeddingResult.disabled()

        if not isinstance(text, str):
            return EmbeddingResult.unavailable(
                EmbeddingFailureCode.INVALID_INPUT,
                "Embedding input must be text.",
            )

        if not text.strip():
            return EmbeddingResult.unavailable(
                EmbeddingFailureCode.EMPTY_INPUT,
                "Cannot embed empty text.",
            )

        model_result = self._get_model()
        if isinstance(model_result, EmbeddingResult):
            return model_result

        try:
            encoded = model_result.encode(
                [text],
                normalize_embeddings=True,
            )
            vector = self._coerce_vector(encoded)
        except Exception:
            logger.exception(
                "RAG embedding failed: model=%s",
                self.model_name,
            )
            return EmbeddingResult.unavailable(
                EmbeddingFailureCode.EMBEDDING_FAILED,
                "Local embedding inference failed.",
            )

        if vector is None:
            logger.error(
                "RAG embedding returned an invalid vector: model=%s dimensions=%s",
                self.model_name,
                self.dimensions,
            )
            return EmbeddingResult.unavailable(
                EmbeddingFailureCode.INVALID_VECTOR,
                "Local embedding provider returned an invalid vector.",
            )

        return EmbeddingResult.available(vector)

    def _get_model(self) -> SentenceTransformerModel | EmbeddingResult:
        if self._model is not None:
            return self._model

        try:
            self._model = self._model_loader(self.model_name)
        except Exception:
            logger.exception(
                "RAG embedding model load failed: model=%s",
                self.model_name,
            )
            return EmbeddingResult.unavailable(
                EmbeddingFailureCode.MODEL_LOAD_FAILED,
                "Local embedding model could not be loaded.",
            )

        return self._model

    def _coerce_vector(self, encoded: Any) -> tuple[float, ...] | None:
        values = encoded.tolist() if hasattr(encoded, "tolist") else encoded

        if not isinstance(values, (list, tuple)) or len(values) != 1:
            return None

        raw_vector = values[0]
        if not isinstance(raw_vector, (list, tuple)):
            return None

        if len(raw_vector) != self.dimensions:
            return None

        try:
            vector = tuple(float(value) for value in raw_vector)
        except (TypeError, ValueError):
            return None

        if not all(math.isfinite(value) for value in vector):
            return None

        return vector
