import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/useAuth";
import { uploadResume } from "../services/resumeService";

function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState(null);

  const [interviewType, setInterviewType] = useState("technical");
  const [difficulty, setDifficulty] = useState("medium");
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [startingInterview, setStartingInterview] = useState(false);
  const [interviewError, setInterviewError] = useState("");

  async function handleLogout() {
    try {
      await logout();
      navigate("/login");
    } catch {
      // Keep the user on the page if logout fails.
    }
  }

  function handleFileChange(event) {
    const file = event.target.files?.[0] || null;

    setSelectedFile(file);
    setSuccessMessage("");
    setError("");
    setAnalysis(null);
  }

  async function handleUpload(event) {
    event.preventDefault();

    if (!selectedFile) {
      setError("Please select a PDF or DOCX file.");
      return;
    }

    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      setError("Only PDF and DOCX files are supported.");
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setError("File size must be 5 MB or less.");
      return;
    }

    setUploading(true);
    setSuccessMessage("");
    setError("");
    setAnalysis(null);

    try {
      const result = await uploadResume(selectedFile);

      setSuccessMessage("Resume uploaded and analyzed successfully.");
      setAnalysis(result.analysis);
      setSelectedFile(null);
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(detail || "Resume upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  async function handleStartInterview() {
    setStartingInterview(true);
    setInterviewError("");

    try {
      const response = await fetch("http://localhost:8000/interviews/sessions", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          interview_type: interviewType,
          difficulty,
          total_questions: totalQuestions,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to start interview.");
      }

      navigate(`/interview/${data.id}`);
    } catch (err) {
      setInterviewError(err.message);
    } finally {
      setStartingInterview(false);
    }
  }

  if (!user) {
    return <p>Loading...</p>;
  }

  return (
    <div>
      <h1>Dashboard</h1>

      <p>Welcome, {user.name}!</p>
      <p>Email: {user.email}</p>

      <hr />

      <h2>Upload Resume</h2>

      <form onSubmit={handleUpload}>
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          disabled={uploading}
        />

        {selectedFile && <p>Selected: {selectedFile.name}</p>}

        <button type="submit" disabled={uploading}>
          {uploading ? "Analyzing Resume..." : "Upload Resume"}
        </button>
      </form>

      {successMessage && <p>{successMessage}</p>}
      {error && <p>{error}</p>}

      {analysis && (
        <section>
          <h2>Resume Analysis</h2>

          <AnalysisList title="Skills" items={analysis.skills} />
          <AnalysisList title="Experience" items={analysis.experience} />
          <AnalysisList title="Education" items={analysis.education} />
          <AnalysisList title="Projects" items={analysis.projects} />
          <AnalysisList title="Strengths" items={analysis.strengths} />
          <AnalysisList title="Skill Gaps" items={analysis.skill_gaps} />
          <AnalysisList
            title="Recommended Topics"
            items={analysis.recommended_topics}
          />
        </section>
      )}

      <hr />

      <section>
        <h2>Start Interview</h2>

        <div>
          <label htmlFor="interview-type">Interview Type:</label>
          <select
            id="interview-type"
            value={interviewType}
            onChange={(event) => setInterviewType(event.target.value)}
            disabled={startingInterview}
          >
            <option value="technical">Technical</option>
            <option value="hr">HR</option>
            <option value="mixed">Mixed</option>
          </select>
        </div>

        <br />

        <div>
          <label htmlFor="difficulty">Difficulty:</label>
          <select
            id="difficulty"
            value={difficulty}
            onChange={(event) => setDifficulty(event.target.value)}
            disabled={startingInterview}
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>

        <br />

        <div>
          <label htmlFor="total-questions">Number of Questions:</label>
          <select
            id="total-questions"
            value={totalQuestions}
            onChange={(event) => setTotalQuestions(Number(event.target.value))}
            disabled={startingInterview}
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
          </select>
        </div>

        <br />

        <button
          type="button"
          onClick={handleStartInterview}
          disabled={startingInterview}
        >
          {startingInterview ? "Starting..." : "Start Interview"}
        </button>

        {interviewError && <p>{interviewError}</p>}
      </section>

      <hr />

      <button type="button" onClick={handleLogout}>
        Logout
      </button>
    </div>
  );
}

function AnalysisList({ title, items = [] }) {
  return (
    <div>
      <h3>{title}</h3>

      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>No information available.</p>
      )}
    </div>
  );
}

export default Dashboard;
