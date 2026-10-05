"""Typed domain objects and utilities for RAG-grounded question generation."""

from dataclasses import dataclass, field

from app.services.rag.retrieval_types import RetrievedChunk


@dataclass(frozen=True, slots=True)
class QuestionRAGContext:
    """Prepared retrieval context for technical question generation.

    Decouples the LLM question generators from database or vector retrieval details.
    """

    query: str
    topic: str | None = None
    chunks: list[RetrievedChunk] = field(default_factory=list)

    @property
    def has_context(self) -> bool:
        """True if any retrieved chunks are present."""
        return len(self.chunks) > 0

    def format_for_prompt(
        self, max_chunks: int = 3, max_chars_per_chunk: int = 700
    ) -> str:
        """Format retrieved knowledge chunks into concise grounding material.

        Formats clean reference material without internal system leakage.
        """
        if not self.chunks:
            return ""

        selected = self.chunks[:max_chunks]
        lines = [
            "Reference Technical Material (for factual grounding and topic accuracy):",
        ]
        for idx, chunk in enumerate(selected, 1):
            text = chunk.chunk_text.strip()
            if len(text) > max_chars_per_chunk:
                text = text[:max_chars_per_chunk].rstrip() + "..."
            lines.append(f"[{idx}] Topic: {chunk.topic} | Source: {chunk.title}")
            lines.append(f"{text}\n")

        lines.extend(
            [
                "Instructions for using reference material:",
                "- Use the concepts above to factually ground your interview question.",
                "- Do NOT copy the reference material verbatim.",
                "- Do NOT mention 'reference material', 'retrieval', or 'RAG'.",
                "- Maintain the requested difficulty and question strategy.",
            ]
        )

        return "\n".join(lines)
