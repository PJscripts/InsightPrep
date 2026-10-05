# Milestone 7: Quantitative RAG Evaluation Report

## 1. Executive Summary

This report documents the empirical evaluation of the **InsightPrep Retrieval-Augmented Generation (RAG)** system implemented across Milestones 3 through 6. 

We performed a paired, controlled quantitative experiment comparing the system's evaluation performance across 24 fixed technical interview questions under two conditions:
1. **Condition A (Baseline)**: Evaluation pipeline executed without RAG context.
2. **Condition B (RAG-Enabled)**: Evaluation pipeline executed with pgvector vector retrieval from the isolated knowledge base (`localhost:5434`).

### Key Findings
- **Baseline Average Score**: `8.058 / 10.0`
- **RAG-Grounded Average Score**: `8.238 / 10.0`
- **Absolute Improvement**: `+0.179 points`
- **Percentage Improvement**: `+2.22%`
- **Paired t-statistic**: `1.9628` ($p = 0.0619$)
- **Corpus Retrieval Coverage**: `24/24 (100.0%)` queries successfully retrieved top-3 relevant chunks.
- **Average Cosine Similarity**: `0.5220` (Min: `0.2918`, Max: `0.6720`).
- **Provider Fallback**: 100% evaluated via Groq (`openai/gpt-oss-120b`) with 0 unhandled failures.

---

## 2. Evaluation Methodology & Fairness Safeguards

1. **Paired Benchmark**: Exactly the same 24 questions and candidate answers were fed through the evaluation pipeline in both conditions.
2. **Candidate-Answer Independence**: In accordance with the Milestone 6 architecture, retrieval queries were deterministically anchored to the question and domain topic, ensuring erroneous or varying answers did not distort the reference material.
3. **Provider Fallback Consistency**: The evaluation pipeline preserved the standard InsightPrep fallback chain (`Groq` $\rightarrow$ `Gemini` $\rightarrow$ `Mock`).
4. **Isolated Environment**: Database queries targeted exclusively the isolated pgvector test container (`localhost:5434`, `rag_test_db`). The production container (`localhost:5433`) remained completely untouched.
5. **No Code Modification**: No scoring weights, prompts, or model parameters were tuned or modified to manipulate experimental outcomes.

---

## 3. Dataset Composition

The benchmark dataset consists of 24 deterministic technical interview questions saved in [`backend/tests/evaluation/rag_evaluation_dataset.json`](file:///c:/Users/hp/Documents/LLM-Interview-Preparation/backend/tests/evaluation/rag_evaluation_dataset.json):
- **DSA (6 questions)**: Hash table complexities, array memory addressing, hash collisions (chaining vs open addressing), BFS vs DFS traversals, BST balancing, and graph cycle detection.
- **DBMS (6 questions)**: ACID properties and durability, transaction isolation levels, B-tree indexing mechanics, clustered vs secondary indexes, Write-Ahead Logging (WAL) crash recovery, and transaction deadlocks.
- **Operating Systems (6 questions)**: Virtual memory paging and page faults, TLB hit/miss mechanics, processes vs threads, mutexes vs counting semaphores, Coffman deadlock conditions, and page replacement (LRU vs FIFO / Belady's Anomaly).
- **Computer Networks (6 questions)**: TCP 3-way handshake, TCP vs UDP comparison, OSI vs TCP/IP model layers, TCP congestion control phases, TCP 4-way termination and TIME_WAIT, and DNS hierarchical resolution flow.

---

## 4. Overall Results Comparison

| Metric | Baseline (No RAG) | RAG-Grounded | Difference | % Change |
|---|---|---|---|---|
| **Overall Score** | **8.058** | **8.238** | **+0.179** | **+2.22%** |
| **Technical Knowledge** | 8.354 | 8.350 | -0.004 | -0.05% |
| **Problem Solving** | 7.146 | 7.492 | +0.346 | +4.84% |
| **Communication** | 8.396 | 8.521 | +0.125 | +1.49% |
| **Clarity** | 8.438 | 8.596 | +0.158 | +1.88% |

---

## 5. Domain-Wise Breakdown

| Domain | Questions | Baseline Average | RAG Average | Absolute Delta | % Improvement |
|---|---|---|---|---|---|
| **DSA** | 6 | 7.817 | 8.300 | **+0.483** | **+6.18%** |
| **DBMS** | 6 | 7.917 | 8.233 | **+0.317** | **+4.00%** |
| **Operating Systems** | 6 | 8.283 | 8.150 | -0.133 | -1.61% |
| **Computer Networks** | 6 | 8.217 | 8.267 | +0.050 | +0.61% |

### Observations on Domain Variations
1. **DSA (+6.18%) and DBMS (+4.00%)**: Benefited the most from RAG reference material. The ground truth enabled the evaluator to credit subtle technical nuances (e.g. 3-color cycle detection, open addressing primary clustering, WAL redo/undo passes, and isolation phenomena prevention) that baseline parametric evaluation treated more generically.
2. **Operating Systems (-1.61%)**: The slight decrease in OS scores stems from higher evaluator stringency. When provided with exact kernel sequence details (e.g., exact page replacement interrupt handling steps and mutex ownership semantics), the evaluator penalized omissions that were previously overlooked.
3. **Computer Networks (+0.61%)**: Standard protocol questions (TCP handshake, OSI layers) have high parametric representation in LLM pretraining, resulting in marginal score delta while refining feedback specificity.

---

## 6. Dimension-Wise Analysis

- **Problem Solving (+4.84%)**: Saw the largest gain. Evaluator prompts grounded in reference concepts were better able to evaluate the candidate's architectural reasoning and algorithmic steps.
- **Clarity (+1.88%) & Communication (+1.49%)**: Showed modest improvements as feedback rewarded structured alignment with domain definitions.
- **Technical Knowledge (-0.05%)**: Remained steady, showing that baseline LLMs already possess broad high-level technical recognition, but RAG tightens the criteria for completeness and reasoning.

---

## 7. Retrieval Quality Statistics

- **Total Queries Evaluated**: 24
- **Queries with Relevant Chunks**: 24 / 24 (100%)
- **Average Chunks Retrieved per Query**: 3.00
- **Average Cosine Similarity**: `0.5220`
- **Max Cosine Similarity**: `0.6720` (DBMS Transaction Isolation Levels)
- **Min Cosine Similarity**: `0.2918` (Hierarchical DNS Lookup Flow)

---

## 8. Statistical Analysis

A two-tailed paired t-test was conducted on the 24 paired observations ($N = 24$):
- **Mean Difference**: $+0.1792$
- **Standard Deviation of Differences**: $0.4475$
- **t-statistic**: $1.9628$
- **p-value**: $0.0619$

At a standard significance threshold of $\alpha = 0.05$, the paired difference approaches significance ($p \approx 0.06$), reflecting a consistent upward shift in scores, particularly concentrated in DSA and DBMS domains.

---

## 9. Artifacts & Reproducibility

- **Evaluation Dataset**: [`backend/tests/evaluation/rag_evaluation_dataset.json`](file:///c:/Users/hp/Documents/LLM-Interview-Preparation/backend/tests/evaluation/rag_evaluation_dataset.json)
- **Evaluation Runner**: [`backend/tests/evaluation/run_rag_evaluation.py`](file:///c:/Users/hp/Documents/LLM-Interview-Preparation/backend/tests/evaluation/run_rag_evaluation.py)
- **Raw Results (JSON)**: [`backend/tests/evaluation/rag_evaluation_results.json`](file:///c:/Users/hp/Documents/LLM-Interview-Preparation/backend/tests/evaluation/rag_evaluation_results.json)
- **Raw Results (CSV)**: [`backend/tests/evaluation/rag_evaluation_results.csv`](file:///c:/Users/hp/Documents/LLM-Interview-Preparation/backend/tests/evaluation/rag_evaluation_results.csv)

### Reproduction Command
```powershell
cd backend
.\.venv\Scripts\python.exe tests/evaluation/run_rag_evaluation.py
```
