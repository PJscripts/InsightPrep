import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/useAuth";
import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await fetch("http://localhost:8000/interviews/progress", { credentials: "include" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to load progress.");
        if (!cancelled) setProgress(data.progress || []);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const latest = progress.at(-1)?.overall_score;
  const best = useMemo(() => progress.length ? Math.max(...progress.map((item) => Number(item.overall_score))) : null, [progress]);
  const first = progress[0]?.overall_score;
  const delta = latest != null && first != null ? Number(latest) - Number(first) : null;

  return (
    <div>
      <section className="dashboard-hero">
        <div>
          <span className="eyebrow">INTERVIEW INTELLIGENCE / DASHBOARD</span>
          <h1 className="page-title">Welcome back, {user?.name || "Candidate"}</h1>
          <p className="page-subtitle">Your preparation console for resume intelligence, mock interviews, and measurable progress.</p>
          <div className="hero-actions"><button className="primary-btn" onClick={() => navigate("/interview")}>Start Interview →</button><button className="secondary-btn" onClick={() => navigate("/resume")}>Review Resume</button></div>
        </div>
        <div className="hero-status-panel"><span className="metric-label">CURRENT SYSTEM STATE</span><strong>READY FOR MOCK SESSION</strong><span className="muted">Latest analyzed resume powers new personalized interviews.</span></div>
      </section>

      <div className="stats-grid">
        <Metric label="Completed Interviews" value={progress.length} note="Sessions completed" tone="indigo" />
        <Metric label="Best Score" value={best != null ? `${Number(best).toFixed(1)}/10` : "—"} note="Highest completed score" tone="cyan" />
        <Metric label="Latest Score" value={latest != null ? `${Number(latest).toFixed(1)}/10` : "—"} note={delta == null ? "No comparison yet" : `${delta >= 0 ? "↑" : "↓"} ${Math.abs(delta).toFixed(1)} from first`} tone={delta == null ? "indigo" : delta >= 0 ? "green" : "amber"} />
      </div>

      <section className="card card-pad" style={{ marginBottom: 16 }}>
        <div className="card-header"><div><h2 className="section-title">Overall Progress</h2><p className="section-description">Your actual session scores. The trend can move upward or downward as you practice.</p></div><button className="ghost-btn" onClick={() => navigate("/performance")}>Open Performance →</button></div>
        {loading && <p className="muted">Loading progress...</p>}
        {error && <div className="alert alert-error">{error}</div>}
        {!loading && !error && progress.length === 0 && <div className="empty-state"><div><h3>No session history yet</h3><p>Complete your first interview to start building a performance baseline.</p><button className="primary-btn" onClick={() => navigate("/interview")}>Take First Interview</button></div></div>}
        {!loading && !error && progress.length > 0 && <LineChart data={progress} valueKey="overall_score" label="Overall interview score" />}
      </section>

      <div className="dashboard-grid-2">
        <section className="card card-pad"><div className="card-section-kicker">RESUME STATUS</div><h2 className="section-title">Personalization source</h2><p className="section-description">Your latest analyzed resume is used for new personalized interviews.</p><div className="resume-mini"><div className="file-icon">CV</div><div><strong>Latest analyzed resume</strong><span>Ready for mock synthesis</span></div><button className="secondary-btn" onClick={() => navigate("/resume")}>Manage</button></div></section>
        <section className="card card-pad"><div className="card-section-kicker">NEXT ACTION</div><h2 className="section-title">Continue practice</h2><p className="section-description">Choose a fixed session for structured practice or an adaptive session for answer-based follow-ups.</p><button className="primary-btn" onClick={() => navigate("/interview")}>Configure Interview →</button></section>
      </div>
    </div>
  );
}

function Metric({ label, value, note, tone }) { return <div className={`card metric-card metric-${tone}`}><div className="metric-label">{label}</div><strong className="metric-value">{value}</strong><span className="metric-note">{note}</span></div>; }

function LineChart({ data, valueKey, label }) {
  const width = 920, height = 280, pad = { top: 24, right: 22, bottom: 48, left: 46 }, cw = width - pad.left - pad.right, ch = height - pad.top - pad.bottom;
  const points = data.map((item, index) => { const value = Number(item[valueKey]); const x = pad.left + (data.length === 1 ? cw / 2 : index / (data.length - 1) * cw); const y = pad.top + ((10 - value) / 10) * ch; return { ...item, value, x, y }; });
  const poly = points.map((point) => `${point.x},${point.y}`).join(" ");
  return <div className="chart-wrap"><svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>{[0,2,4,6,8,10].map((tick) => { const y = pad.top + ((10 - tick) / 10) * ch; return <g key={tick}><line x1={pad.left} y1={y} x2={width-pad.right} y2={y} stroke="var(--chart-grid)"/><text x="10" y={y+4} fontSize="11" fill="var(--chart-label)">{tick}</text></g>; })}<polyline fill="none" stroke="var(--accent-cyan)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" points={poly}/>{points.map((point,index) => <g key={`${point.session_id}-${index}`}><circle cx={point.x} cy={point.y} r="5" fill="var(--accent-indigo)" stroke="var(--surface-2)" strokeWidth="2"/><text x={point.x} y={height-18} textAnchor="middle" fontSize="11" fill="var(--chart-label)">#{index+1}</text><title>{`${new Date(point.created_at).toLocaleDateString()} · ${point.value.toFixed(1)}/10`}</title></g>)}</svg></div>;
}
export default Dashboard;
