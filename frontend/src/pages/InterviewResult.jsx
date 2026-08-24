import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

function InterviewResult() {
  const { sessionId } = useParams();

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function fetchResult() {
      try {
        const response = await fetch(
          `http://localhost:8000/interviews/sessions/${sessionId}/result`,
          {
            credentials: "include",
          },
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Failed to load interview result");
        }

        if (!cancelled) {
          setResult(data);
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

    fetchResult();

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  if (loading) {
    return <p>Loading interview results...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  if (!result) {
    return <p>No interview result available.</p>;
  }

  return (
    <div>
      <h1>Interview Complete</h1>

      <p>Score: {result.overall_score} / 10</p>

      <p>Performance: {result.performance}</p>

      <p>
        Answered: {result.answered_questions} of {result.total_questions}
      </p>

      <hr />

      <h2>Question-by-Question Results</h2>

      {result.results.map((item) => (
        <section key={item.question_number}>
          <h3>Question {item.question_number}</h3>

          <p>
            <strong>Question:</strong> {item.question}
          </p>

          <p>
            <strong>Your Answer:</strong> {item.answer}
          </p>

          <p>
            <strong>Score:</strong> {item.score} / 10
          </p>

          <p>
            <strong>Feedback:</strong> {item.feedback}
          </p>

          <hr />
        </section>
      ))}

      <Link to="/dashboard">Back to Dashboard</Link>
    </div>
  );
}

export default InterviewResult;
