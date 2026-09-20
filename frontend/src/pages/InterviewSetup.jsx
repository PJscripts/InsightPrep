import { useState } from "react";
import { useNavigate } from "react-router-dom";

function InterviewSetup() {
  const navigate = useNavigate();
  const [interviewType, setInterviewType] = useState("technical");
  const [difficulty, setDifficulty] = useState("medium");
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [starting, setStarting] = useState(false);
  const [selectedMode, setSelectedMode] = useState("fixed");
  const [error, setError] = useState("");

  async function startInterview(mode) {
    setStarting(true); setError("");
    try {
      const response = await fetch("http://localhost:8000/interviews/sessions", { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ interview_mode: mode, interview_type: interviewType, difficulty, total_questions: mode === "fixed" ? totalQuestions : null }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to start interview.");
      navigate(`/interview/${data.id}`);
    } catch (err) { setError(err.message); } finally { setStarting(false); }
  }

  return <div>
    <div className="page-header"><div><p className="eyebrow">Interview</p><h1 className="page-title">Practice Interview</h1><p className="page-subtitle">Configure your next interview session before entering the live interview room.</p></div></div>

    <section className="card card-pad" style={{ marginBottom: 16 }}>
      <div className="grid-2">
        <label className="input-label">Interview Type<select className="select" value={interviewType} onChange={(e)=>setInterviewType(e.target.value)} disabled={starting}><option value="technical">Technical</option><option value="hr">HR</option><option value="mixed">Mixed</option></select></label>
        <label className="input-label">Difficulty<select className="select" value={difficulty} onChange={(e)=>setDifficulty(e.target.value)} disabled={starting}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
      </div>
    </section>

    <div className="mode-grid">
      <section className={`card mode-card${selectedMode === "fixed" ? " selected" : ""}`}>
        <div className="mode-top"><div><h2 className="mode-title">Fixed Interview</h2><p className="mode-desc">Focused practice with a defined question count.</p></div>{selectedMode === "fixed" && <span className="badge badge-primary">Selected</span>}</div>
        <ul className="mode-bullets"><li>Choose 3, 5, or 10 questions</li><li>Short formats stay independent</li><li>10-question mode may use follow-ups</li></ul>
        <div className="mode-footer"><label className="input-label">Number of Questions<select className="select" value={totalQuestions} onChange={(e)=>setTotalQuestions(Number(e.target.value))} disabled={starting}><option value={3}>3</option><option value={5}>5</option><option value={10}>10</option></select></label><button className="primary-btn" style={{ marginTop: 12, width: "100%" }} type="button" onClick={()=>{setSelectedMode("fixed"); startInterview("fixed");}} disabled={starting}>{starting && selectedMode === "fixed" ? "Starting..." : "Start Fixed Interview"}</button></div>
      </section>

      <section className={`card mode-card${selectedMode === "adaptive" ? " selected" : ""}`}>
        <div className="mode-top"><div><h2 className="mode-title">Adaptive Interview</h2><p className="mode-desc">Resume-aware questions with answer-based follow-ups and topic rotation.</p></div>{selectedMode === "adaptive" && <span className="badge badge-primary">Selected</span>}</div>
        <ul className="mode-bullets"><li>Uses your latest analyzed resume</li><li>Follow-ups adapt to your answers</li><li>Variable interview length within bounds</li></ul>
        <div className="mode-footer"><button className="primary-btn" style={{ width: "100%" }} type="button" onClick={()=>{setSelectedMode("adaptive"); startInterview("adaptive");}} disabled={starting}>{starting && selectedMode === "adaptive" ? "Starting..." : "Start Adaptive Interview"}</button></div>
      </section>
    </div>
    {error && <div className="alert alert-error">{error}</div>}
  </div>;
}
export default InterviewSetup;
