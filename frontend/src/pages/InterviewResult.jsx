import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

const SKILLS = [
  ["technical_knowledge", "Technical Knowledge"],
  ["problem_solving", "Problem Solving"],
  ["communication", "Communication"],
  ["clarity", "Clarity"],
];

function InterviewResult() {
  const { sessionId } = useParams();
  const [result, setResult] = useState(null);
  const [activeSection, setActiveSection] = useState("overall");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await fetch(`http://localhost:8000/interviews/sessions/${sessionId}/result`, { credentials: "include" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to load interview result.");
        if (!cancelled) setResult(data);
      } catch (err) { if (!cancelled) setError(err.message); }
      finally { if (!cancelled) setLoading(false); }
    }
    load(); return () => { cancelled = true; };
  }, [sessionId]);

  const scores = useMemo(() => (result?.results || []).map((item) => Number(item.score || 0)), [result]);

  if (loading) return <div className="card empty-state">Loading interview result...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!result) return <div className="card empty-state">No interview result available.</div>;

  return <div>
    <section className="card result-hero">
      <div className="result-hero-grid">
        <div>
          <p className="eyebrow">Interview Result</p>
          <h1 className="result-title">Interview Complete</h1>
          <p className="page-subtitle">Detailed evaluation for this completed session.</p>
          <div className="result-meta">
            <span className="badge badge-neutral">{result.answered_questions} / {result.total_questions ?? ""} Questions Answered</span>
            <span className="badge badge-primary">{label(result.interview_type)} Interview</span>
            <span className="badge badge-neutral">{label(result.interview_mode)} Mode</span>
            <span className="badge badge-neutral">{label(result.difficulty)} Difficulty</span>
          </div>
        </div>
        <div className="result-score-box"><div className="result-score-label">Overall Score</div><div className="result-score">{result.overall_score}<small> /10</small></div><div className="result-performance">● Performance: {result.performance}</div></div>
      </div>
    </section>

    <div className="tabs" role="tablist" aria-label="Interview result sections">
      <button className={`tab${activeSection === "overall" ? " active" : ""}`} type="button" onClick={()=>setActiveSection("overall")}>Overall Feedback</button>
      <button className={`tab${activeSection === "questions" ? " active" : ""}`} type="button" onClick={()=>setActiveSection("questions")}>Question-wise Results <span className="badge badge-primary" style={{ marginLeft: 5 }}>{result.results.length}</span></button>
    </div>

    {activeSection === "overall" && <section>
      <div className="grid-2">
        <section className="card card-pad"><div className="card-header"><div><h2 className="section-title">Skill Profile</h2><p className="section-description">How this specific interview performed across the four evaluation dimensions.</p></div></div>{result.skill_profile ? <RadarChart profile={result.skill_profile} /> : <div className="empty-state">Skill profile is unavailable for this session.</div>}</section>
        <section className="card card-pad"><h2 className="section-title">Overall Feedback</h2><p className="section-description">Session-level feedback and the main takeaways from the completed interview.</p><div className="result-feedback-list">{(result.final_feedback || []).map((point, index) => <div className="result-feedback-item" key={`${index}-${point}`}>{point}</div>)}</div></section>
      </div>
    </section>}

    {activeSection === "questions" && <section>
      <section className="card card-pad" style={{ marginBottom: 16 }}><div className="card-header"><div><h2 className="section-title">Question Performance</h2><p className="section-description">Score distribution across the questions in this session.</p></div></div><QuestionBarChart scores={scores} /></section>
      <div>{result.results.map((item, index) => <details className="card question-card" open={index === 0} key={item.question_number}><summary className="question-summary"><span className="question-number">{item.question_number}</span><div><p className="question-summary-title">Question {item.question_number}</p><p className="question-summary-text">{item.question}</p></div><span className="badge badge-success question-score-badge">{item.score} / 10</span></summary><div className="question-content"><div className="metric-label" style={{ marginTop: 16 }}>Interview Prompt</div><p>{item.question}</p><div className="metric-label">Your Answer</div><p>{item.answer || "No answer recorded."}</p><div className="metric-label">Feedback</div><p>{item.feedback}</p></div></details>)}</div>
    </section>}

    <div style={{ marginTop: 18 }}><Link to="/history" style={{ color: "#4f46e5", textDecoration: "none", fontWeight: 800 }}>← Back to History</Link></div>
  </div>;
}

function RadarChart({ profile }) {
  const size = 380; const center = size/2; const radius = 118;
  const coords = SKILLS.map(([key, label], index) => { const angle = -Math.PI/2 + index*2*Math.PI/SKILLS.length; const value = Number(profile[key] ?? 0); return { key, label, value, angle, point: { x: center + Math.cos(angle)*radius*(value/10), y: center + Math.sin(angle)*radius*(value/10) }, labelPoint: { x: center + Math.cos(angle)*(radius+42), y: center + Math.sin(angle)*(radius+42) } }; });
  const polygon = coords.map((c)=>`${c.point.x},${c.point.y}`).join(" ");
  return <div className="radar-wrap"><svg viewBox={`0 0 ${size} ${size}`} width="100%" role="img" aria-label="Skill profile radar chart">
    {[2.5,5,7.5,10].map((value)=><polygon key={value} points={coords.map(c=>`${center+Math.cos(c.angle)*radius*(value/10)},${center+Math.sin(c.angle)*radius*(value/10)}`).join(" ")} fill="none" stroke="var(--chart-grid)" strokeWidth="1"/>)}
    {coords.map(c=><g key={c.key}><line x1={center} y1={center} x2={center+Math.cos(c.angle)*radius} y2={center+Math.sin(c.angle)*radius} stroke="var(--chart-grid)"/><text x={c.labelPoint.x} y={c.labelPoint.y} textAnchor="middle" fontSize="12" fill="var(--chart-label)">{c.label}</text></g>)}
    <polygon points={polygon} fill="var(--accent-indigo)" fillOpacity=".14" stroke="var(--accent-indigo)" strokeWidth="2.5"/>
    {coords.map(c=><circle key={c.key} cx={c.point.x} cy={c.point.y} r="4" fill="var(--accent-indigo)"><title>{`${c.label}: ${c.value.toFixed(1)}/10`}</title></circle>)}
  </svg></div>;
}

function QuestionBarChart({ scores }) { return <div style={{ height: 220, display: "flex", alignItems: "flex-end", gap: 12, padding: "24px 10px 0" }}>{scores.map((score,index)=><div key={index} style={{ flex: 1, height: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}><div style={{ flex: 1, width: "100%", display: "flex", alignItems: "flex-end", justifyContent: "center" }}><div style={{ width: "58%", minHeight: 7, height: `${Math.max(score/10*100, 3)}%`, background: "#4f46e5", borderRadius: "7px 7px 0 0", position: "relative" }}><span style={{ position: "absolute", top: -20, left: "50%", transform: "translateX(-50%)", fontSize: 11, fontWeight: 800 }}>{score}</span></div></div><span style={{ marginTop: 8, color: "#64748b", fontSize: 12 }}>Q{index+1}</span></div>)}</div>; }
function label(value="") { return value ? value.charAt(0).toUpperCase()+value.slice(1) : ""; }
export default InterviewResult;
