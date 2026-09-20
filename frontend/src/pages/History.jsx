import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function History() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try { const response = await fetch("http://localhost:8000/interviews/history", { credentials: "include" }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Failed to load interview history."); if (!cancelled) setHistory(data.history || []); }
      catch (err) { if (!cancelled) setError(err.message); }
      finally { if (!cancelled) setLoading(false); }
    }
    load(); return () => { cancelled = true; };
  }, []);
  return <div>
    <div className="page-header"><div><p className="eyebrow">History</p><h1 className="page-title">Interview History</h1><p className="page-subtitle">Review completed sessions and open their full result pages.</p></div></div>
    {loading && <p className="muted">Loading history...</p>}
    {error && <div className="alert alert-error">{error}</div>}
    {!loading && !error && history.length === 0 && <section className="card empty-state"><div><h2 className="section-title">No completed interviews yet</h2><p>Complete a mock interview to start building your history.</p><button className="primary-btn" onClick={()=>navigate("/interview")}>Start Interview</button></div></section>}
    {!loading && !error && history.length > 0 && <div className="list">{history.map((item) => <section className="card history-card" key={item.session_id}><div className="history-main"><h2 className="history-title">{label(item.interview_type)} Interview</h2><p className="history-meta">{label(item.interview_mode)} · {label(item.difficulty)}</p><p className="history-meta">{formatDate(item.created_at)} · {item.answered_questions} questions answered</p></div><div className="history-actions"><div><div className="history-score">{item.overall_score ?? "—"} / 10</div><span className="badge badge-neutral">{item.performance}</span></div><button className="secondary-btn" onClick={()=>navigate(`/interview/${item.session_id}/result`)}>View Results</button></div></section>)}</div>}
  </div>;
}
function label(value="") { return value ? value.charAt(0).toUpperCase()+value.slice(1) : ""; }
function formatDate(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? "" : date.toLocaleString(); }
export default History;
