"""Context builder and retrieval orchestrator for interview answer evaluation."""

import logging
from typing import Any

from app.services.rag.answer_context import AnswerRAGContext
from app.services.rag.question_context_builder import map_topic_to_corpus
from app.services.rag.retrieval_service import VectorRetrievalService

logger = logging.getLogger(__name__)


def construct_evaluation_retrieval_query(
    question: str,
    topic: str | None = None,
    answer: str | None = None,
) -> str:
    """Construct a clean, deterministic retrieval query for answer evaluation.

    Candidate-answer independence strategy:
    The retrieved context MUST be primarily anchored to the interview question and
    technical topic to prevent an incorrect or hallucinatory answer from distorting
    the reference benchmark. If a candidate answer is present, we only incorporate
    its high-level focus keywords if concise, but primarily rely on the question.
    """
    parts = []
    clean_q = (question or "").strip()
    if clean_q:
        # Keep concise question focus
        parts.append(clean_q[:200])

    if topic and topic.strip():
        clean_topic = topic.strip()
        if clean_topic.lower() not in clean_q.lower():
            parts.append(f"topic: {clean_topic}")

    return " - ".join(parts) if parts else (topic or "technical interview concepts")


class AnswerRAGContextBuilder:
    """Orchestrates retrieval for technical answer evaluation fail-open."""

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
        question: str,
        answer: str,
        current_topic: str | None = None,
        resume_analysis: dict[str, Any] | None = None,
    ) -> AnswerRAGContext | None:
        """Retrieve relevant reference knowledge chunks if applicable.

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

        query = construct_evaluation_retrieval_query(
            question=question,
            topic=current_topic,
            answer=answer,
        )

        corpus_topic = map_topic_to_corpus(current_topic)
        if not corpus_topic:
            # Attempt to infer corpus topic from question text if topic is generic
            corpus_topic = map_topic_to_corpus(question)

        try:
            result = self.retrieval_service.retrieve(
                query=query,
                top_k=self.top_k,
                distance_threshold=self.distance_threshold,
                topic=corpus_topic,
            )

            if not result.is_success or not result.chunks:
                logger.info(
                    "RAG retrieval returned no usable evaluation chunks for query: %s "
                    "(status=%s, code=%s)",
                    query,
                    result.status,
                    result.failure_code,
                )
                return None

            return AnswerRAGContext(
                query=query,
                topic=corpus_topic,
                chunks=result.chunks,
            )

        except Exception as exc:
            logger.warning(
                "RAG answer context builder encountered unexpected error: %s",
                exc,
            )
            return None
