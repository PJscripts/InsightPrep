"""Typed domain objects and utilities for RAG-grounded answer evaluation."""

from dataclasses import dataclass, field

from app.services.rag.retrieval_types import RetrievedChunk


@dataclass(frozen=True, slots=True)
class AnswerRAGContext:
    """Prepared retrieval context for technical answer evaluation.

    Decouples LLM answer evaluators from database and vector retrieval details.
    """

    query: str
    topic: str | None = None
    chunks: list[RetrievedChunk] = field(default_factory=list)

    @property
    def has_context(self) -> bool:
        """True if any retrieved knowledge chunks are present."""
        return len(self.chunks) > 0

    def format_for_prompt(
        self, max_chunks: int = 3, max_chars_per_chunk: int = 700
    ) -> str:
        """Format retrieved knowledge chunks into concise reference material.

        Formats clean reference material without internal system leakage.
        """
        if not self.chunks:
            return ""

        selected = self.chunks[:max_chunks]
        lines = [
            "Reference Technical Material (for factual correctness and evaluation "
            "grounding):",
        ]
        for idx, chunk in enumerate(selected, 1):
            text = chunk.chunk_text.strip()
            if len(text) > max_chars_per_chunk:
                text = text[:max_chars_per_chunk].rstrip() + "..."
            lines.append(f"[{idx}] Topic: {chunk.topic} | Source: {chunk.title}")
            lines.append(f"{text}\n")

        lines.extend(
            [
                "Evaluation guidance regarding reference material:",
                "- Use the reference material above as the factual benchmark.",
                "- Reward statements demonstrating understanding of these concepts.",
                "- Note any significant omissions or technical errors.",
                "- Do NOT penalize for phrasing differently or missing exact words.",
                "- Do NOT mention reference material, retrieval, or RAG in feedback.",
            ]
        )

        return "\n".join(lines)
