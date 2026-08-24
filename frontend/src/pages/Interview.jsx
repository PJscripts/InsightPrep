import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

function Interview() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [evaluation, setEvaluation] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchQuestion() {
      try {
        const response = await fetch(
          `http://localhost:8000/interviews/sessions/${sessionId}/current`,
          {
            credentials: "include",
          },
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Failed to load question");
        }

        if (!cancelled) {
          setQuestion(data);
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchQuestion();

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!answer.trim()) {
      setError("Please enter an answer before submitting.");
      return;
    }

    setSubmitting(true);
    setError("");
    setEvaluation(null);

    try {
      const response = await fetch(
        `http://localhost:8000/interviews/sessions/${sessionId}/answer`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            answer_text: answer,
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to submit answer");
      }

      setEvaluation(data.evaluation);
      setAnswer("");

      if (data.status === "completed") {
        navigate(`/interview/${sessionId}/result`);
        return;
      }

      setQuestion({
        session_id: data.session_id,
        question_number: data.current_question,
        total_questions: data.total_questions,
        question_text: data.question.question_text,
        question_type: data.question.question_type,
        status: data.status,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <p>Loading interview...</p>;
  }

  if (!question) {
    return <p>{error || "No question available."}</p>;
  }

  const progress = (question.question_number / question.total_questions) * 100;

  return (
    <div>
      <h1>AI Interview</h1>

      <p>
        Question {question.question_number} of {question.total_questions}
      </p>

      <progress value={progress} max="100" />

      <h2>{question.question_text}</h2>

      <form onSubmit={handleSubmit}>
        <textarea
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Type your answer..."
          rows={10}
          disabled={submitting}
        />

        <br />

        <button type="submit" disabled={submitting}>
          {submitting ? "Evaluating..." : "Submit Answer"}
        </button>
      </form>

      {evaluation && (
        <section>
          <h3>Feedback</h3>
          <p>Score: {evaluation.score}</p>
          <p>{evaluation.feedback}</p>
        </section>
      )}

      {error && <p>{error}</p>}
    </div>
  );
}

export default Interview;
