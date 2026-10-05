"""Milestone 7: Quantitative RAG Evaluation Runner.

Executes a paired evaluation experiment across 24 fixed technical interview questions:
Condition A: Baseline WITHOUT RAG
Condition B: Grounded WITH RAG (using isolated pgvector on port 5434)

Computes overall, domain-wise, and dimension-wise metrics, paired t-tests,
and outputs both a raw JSON results file and a detailed CSV file.
"""

import csv
import json
import logging
import os
import sys
import time
from pathlib import Path

# Ensure sys.path includes backend root
backend_root = str(Path(__file__).resolve().parents[2])
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.services.gemini_answer_evaluator import GeminiAnswerEvaluator  # noqa: E402
from app.services.groq_answer_evaluator import GroqAnswerEvaluator  # noqa: E402
from app.services.mock_answer_evaluator import MockAnswerEvaluator  # noqa: E402
from app.services.rag.answer_context_builder import (  # noqa: E402
    AnswerRAGContextBuilder,
)
from app.services.rag.embeddings import (  # noqa: E402
    LocalSentenceTransformerEmbeddingProvider,
)
from app.services.rag.retrieval_service import VectorRetrievalService  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("rag_evaluation")

ISOLATED_DB_URL = os.getenv(
    "ISOLATED_RAG_DATABASE_URL",
    "postgresql+psycopg://rag_user:rag_password@localhost:5434/rag_test_db",
)

DATASET_PATH = Path(__file__).parent / "rag_evaluation_dataset.json"
RESULTS_JSON_PATH = Path(__file__).parent / "rag_evaluation_results.json"
RESULTS_CSV_PATH = Path(__file__).parent / "rag_evaluation_results.csv"


def evaluate_with_provider_fallback(
    question: str,
    answer: str,
    resume_analysis: dict,
    rag_context=None,
    primary_provider: str = "groq",
    fallback_provider: str = "gemini",
    final_fallback: str = "mock",
):
    """Executes evaluation following the exact InsightPrep provider fallback chain."""
    providers = [
        (primary_provider, lambda: GroqAnswerEvaluator()),
        (fallback_provider, lambda: GeminiAnswerEvaluator()),
        (final_fallback, lambda: MockAnswerEvaluator()),
    ]

    last_error = None
    for prov_name, factory in providers:
        try:
            evaluator = factory()
            res = evaluator.evaluate(
                question=question,
                answer=answer,
                resume_analysis=resume_analysis,
                rag_context=rag_context,
            )
            return res, prov_name, None
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Provider %s failed: %s", prov_name, exc)
            time.sleep(1.0)  # Gentle backoff

    # Fallback to mock if all else fails
    mock_eval = MockAnswerEvaluator()
    res = mock_eval.evaluate(
        question=question,
        answer=answer,
        resume_analysis=resume_analysis,
        rag_context=rag_context,
    )
    return res, "mock", f"All primary and secondary providers failed: {last_error}"


def run_experiment():
    with open(DATASET_PATH, encoding="utf-8") as f:
        questions = json.load(f)

    logger.info("Loaded %d questions from %s", len(questions), DATASET_PATH)

    # Initialize RAG retrieval against isolated database on localhost:5434
    engine = create_engine(ISOLATED_DB_URL, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    embedder = LocalSentenceTransformerEmbeddingProvider(enabled=True, dimensions=384)
    retriever = VectorRetrievalService(
        session_factory=session_factory,
        embedding_provider=embedder,
        default_top_k=3,
    )
    rag_builder = AnswerRAGContextBuilder(retrieval_service=retriever)

    records = []

    for idx, item in enumerate(questions, 1):
        qid = item["question_id"]
        domain = item["domain"]
        q_text = item["question"]
        ans_text = item["candidate_answer"]
        topic = item.get("topic", domain)
        resume_analysis = {"skills": [domain, topic]}

        logger.info("[%d/%d] Evaluating %s (%s)...", idx, len(questions), qid, domain)

        # Condition A: BASELINE (WITHOUT RAG)
        b_res, b_prov, b_err = evaluate_with_provider_fallback(
            question=q_text,
            answer=ans_text,
            resume_analysis=resume_analysis,
            rag_context=None,
        )
        time.sleep(0.5)

        # Condition B: RAG ENABLED
        rag_ctx = rag_builder.build_context(
            interview_type="technical",
            question=q_text,
            answer=ans_text,
            current_topic=topic,
            resume_analysis=resume_analysis,
        )

        r_res, r_prov, r_err = evaluate_with_provider_fallback(
            question=q_text,
            answer=ans_text,
            resume_analysis=resume_analysis,
            rag_context=rag_ctx,
        )
        time.sleep(0.5)

        # Retrieval metrics
        retrieved_chunk_count = len(rag_ctx.chunks) if rag_ctx else 0
        similarities = [c.similarity_score for c in rag_ctx.chunks] if rag_ctx else []
        avg_similarity = round(float(np.mean(similarities)), 4) if similarities else 0.0

        b_score = float(b_res.get("score", 0.0))
        r_score = float(r_res.get("score", 0.0))
        diff = round(r_score - b_score, 4)

        b_dims = b_res.get("dimensions", {})
        r_dims = r_res.get("dimensions", {})

        record = {
            "question_id": qid,
            "domain": domain,
            "topic": topic,
            "question": q_text,
            "baseline_score": b_score,
            "rag_score": r_score,
            "score_difference": diff,
            "baseline_technical_knowledge": float(
                b_dims.get("technical_knowledge", 0.0)
            ),
            "rag_technical_knowledge": float(
                r_dims.get("technical_knowledge", 0.0)
            ),
            "baseline_problem_solving": float(b_dims.get("problem_solving", 0.0)),
            "rag_problem_solving": float(r_dims.get("problem_solving", 0.0)),
            "baseline_communication": float(b_dims.get("communication", 0.0)),
            "rag_communication": float(r_dims.get("communication", 0.0)),
            "baseline_clarity": float(b_dims.get("clarity", 0.0)),
            "rag_clarity": float(r_dims.get("clarity", 0.0)),
            "retrieved_chunk_count": retrieved_chunk_count,
            "average_similarity": avg_similarity,
            "baseline_provider": b_prov,
            "rag_provider": r_prov,
            "errors_or_fallbacks": b_err or r_err or "None",
            "baseline_feedback": b_res.get("feedback", ""),
            "rag_feedback": r_res.get("feedback", ""),
        }
        records.append(record)
        logger.info(
            "--> %s: Baseline=%.1f | RAG=%.1f | Diff=%+.1f (Chunks=%d, Sim=%.2f)",
            qid,
            b_score,
            r_score,
            diff,
            retrieved_chunk_count,
            avg_similarity,
        )

    # Save raw results JSON
    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    # Save raw results CSV
    fieldnames = [
        "question_id",
        "domain",
        "question",
        "baseline_score",
        "rag_score",
        "score_difference",
        "baseline_technical_knowledge",
        "rag_technical_knowledge",
        "baseline_problem_solving",
        "rag_problem_solving",
        "baseline_communication",
        "rag_communication",
        "baseline_clarity",
        "rag_clarity",
        "retrieved_chunk_count",
        "average_similarity",
        "baseline_provider",
        "rag_provider",
        "errors_or_fallbacks",
    ]
    with open(RESULTS_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    logger.info("Saved raw results to %s and %s", RESULTS_JSON_PATH, RESULTS_CSV_PATH)

    # Perform statistical and aggregate calculations
    analyze_results(records)


def analyze_results(records):
    b_scores = np.array([r["baseline_score"] for r in records])
    r_scores = np.array([r["rag_score"] for r in records])

    b_mean = float(np.mean(b_scores))
    r_mean = float(np.mean(r_scores))
    abs_imp = r_mean - b_mean
    pct_imp = (abs_imp / b_mean) * 100 if b_mean > 0 else 0.0

    # Paired t-test
    t_stat, p_val = stats.ttest_rel(r_scores, b_scores)

    print("\n" + "=" * 60)
    print("           INSIGHTPREP RAG QUANTITATIVE EVALUATION           ")
    print("=" * 60)
    print(f"Total Questions Evaluated: {len(records)}")
    print(f"Baseline Score (Mean):     {b_mean:.3f}")
    print(f"RAG-Grounded Score (Mean): {r_mean:.3f}")
    print(f"Absolute Score Delta:      {abs_imp:+.3f}")
    print(f"Percentage Improvement:    {pct_imp:+.2f}%")
    print(f"Paired t-statistic:        {t_stat:.4f} (p-value = {p_val:.4e})")
    print("-" * 60)

    # Domain breakdown
    print("DOMAIN-WISE COMPARISON:")
    domains = sorted(list({r["domain"] for r in records}))
    for d in domains:
        d_b = [r["baseline_score"] for r in records if r["domain"] == d]
        d_r = [r["rag_score"] for r in records if r["domain"] == d]
        d_b_m = np.mean(d_b)
        d_r_m = np.mean(d_r)
        d_diff = d_r_m - d_b_m
        d_pct = (d_diff / d_b_m) * 100 if d_b_m > 0 else 0.0
        print(
            f"  * {d:<20} Baseline: {d_b_m:.2f} | RAG: {d_r_m:.2f} | "
            f"Delta: {d_diff:+.2f} ({d_pct:+.2f}%)"
        )

    # Dimension breakdown
    print("\nDIMENSION-WISE COMPARISON:")
    dims = ["technical_knowledge", "problem_solving", "communication", "clarity"]
    for dim in dims:
        dim_b = [r[f"baseline_{dim}"] for r in records]
        dim_r = [r[f"rag_{dim}"] for r in records]
        db_m = np.mean(dim_b)
        dr_m = np.mean(dim_r)
        d_diff = dr_m - db_m
        d_pct = (d_diff / db_m) * 100 if db_m > 0 else 0.0
        print(
            f"  * {dim:<20} Baseline: {db_m:.2f} | RAG: {dr_m:.2f} | "
            f"Delta: {d_diff:+.2f} ({d_pct:+.2f}%)"
        )

    # Retrieval stats
    chunks = [r["retrieved_chunk_count"] for r in records]
    sims = [r["average_similarity"] for r in records if r["retrieved_chunk_count"] > 0]
    relevant_found = sum(1 for c in chunks if c > 0)
    print("\nRETRIEVAL STATISTICS:")
    print(
        f"  * Questions with Retrieved Chunks: {relevant_found}/{len(records)} "
        f"({relevant_found/len(records)*100:.1f}%)"
    )
    print(f"  * Average Chunks per Query:       {np.mean(chunks):.2f}")
    if sims:
        print(f"  * Average Cosine Similarity:      {np.mean(sims):.4f}")
        print(
            f"  * Min / Max Similarity:           {np.min(sims):.4f} / "
            f"{np.max(sims):.4f}"
        )
    print("=" * 60)


if __name__ == "__main__":
    run_experiment()
