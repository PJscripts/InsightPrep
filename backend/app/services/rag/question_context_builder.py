"""Context builder and retrieval orchestrator for interview question generation."""

import logging
from typing import Any

from app.services.rag.question_context import QuestionRAGContext
from app.services.rag.retrieval_service import VectorRetrievalService

logger = logging.getLogger(__name__)

# Known topic keywords in the curated technical knowledge corpus
CORPUS_TOPIC_MAP = {
    "dsa": "dsa",
    "data structures": "dsa",
    "algorithms": "dsa",
    "arrays": "dsa",
    "hash tables": "dsa",
    "hashing": "dsa",
    "trees": "dsa",
    "graphs": "dsa",
    "dbms": "dbms",
    "database": "dbms",
    "databases": "dbms",
    "sql": "dbms",
    "indexing": "dbms",
    "b-trees": "dbms",
    "transactions": "dbms",
    "acid": "dbms",
    "os": "operating_systems",
    "operating systems": "operating_systems",
    "operating system": "operating_systems",
    "virtual memory": "operating_systems",
    "paging": "operating_systems",
    "concurrency": "operating_systems",
    "threads": "operating_systems",
    "deadlock": "operating_systems",
    "networks": "computer_networks",
    "computer networks": "computer_networks",
    "networking": "computer_networks",
    "tcp": "computer_networks",
    "udp": "computer_networks",
    "http": "computer_networks",
    "dns": "computer_networks",
    "osi": "computer_networks",
}


def map_topic_to_corpus(topic: str | None) -> str | None:
    """Map a topic string to a corpus domain ('dsa', 'dbms', etc.).

    Returns None if the topic does not match any technical corpus domain.
    """
    if not topic:
        return None
    cleaned = topic.strip().lower()
    if cleaned in CORPUS_TOPIC_MAP:
        return CORPUS_TOPIC_MAP[cleaned]
    for key, mapped in CORPUS_TOPIC_MAP.items():
        if key in cleaned:
            return mapped
    return None


def construct_retrieval_query(
    current_topic: str | None,
    difficulty: str,
    question_strategy: str,
    previous_questions: list[str] | None = None,
) -> str:
    """Construct a clean, deterministic retrieval query without extra LLM overhead."""
    parts = []
    if current_topic and current_topic.strip():
        parts.append(current_topic.strip())
    if (
        question_strategy == "follow_up"
        and previous_questions
        and len(previous_questions) > 0
    ):
        last_q = previous_questions[-1].strip()
        if len(last_q) > 100:
            last_q = last_q[:100]
        parts.append(f"concepts related to: {last_q}")
    elif difficulty:
        parts.append(f"{difficulty} technical concepts and principles")

    query = (
        " - ".join(parts)
        if parts
        else (current_topic or "core computer science fundamentals")
    )
    return query


class QuestionRAGContextBuilder:
    """Orchestrates retrieval for technical interview questions fail-open."""

    def __init__(
        self,
        retrieval_service: VectorRetrievalService | None = None,
        top_k: int = 3,
        distance_threshold: float = 0.85,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.top_k = top_k
        self.distance_threshold = distance_threshold

    def build_context(
        self,
        *,
        interview_type: str,
        current_topic: str | None,
        difficulty: str,
        question_strategy: str = "fixed_independent",
        previous_questions: list[str] | None = None,
        resume_analysis: dict[str, Any] | None = None,
    ) -> QuestionRAGContext | None:
        """Retrieve relevant knowledge chunks if applicable.

        Returns None if:
        - interview_type is not technical
        - retrieval_service is not configured
        - retrieval fails or returns 0 chunks

        Never raises exceptions (fail-open).
        """
        # Strict rule: Only technical interviews use the technical RAG knowledge corpus
        if (interview_type or "").strip().lower() != "technical":
            return None

        if self.retrieval_service is None:
            return None

        query = construct_retrieval_query(
            current_topic=current_topic,
            difficulty=difficulty,
            question_strategy=question_strategy,
            previous_questions=previous_questions,
        )

        corpus_topic = map_topic_to_corpus(current_topic)

        try:
            result = self.retrieval_service.retrieve(
                query=query,
                top_k=self.top_k,
                distance_threshold=self.distance_threshold,
                topic=corpus_topic,
            )

            if not result.is_success or not result.chunks:
                logger.info(
                    "RAG retrieval returned no usable chunks for query: %s "
                    "(status=%s, code=%s)",
                    query,
                    result.status,
                    result.failure_code,
                )
                return None

            return QuestionRAGContext(
                query=query,
                topic=corpus_topic,
                chunks=result.chunks,
            )

        except Exception as exc:
            logger.warning(
                "RAG question context builder encountered unexpected error: %s", exc
            )
            return None
