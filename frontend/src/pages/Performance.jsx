import { useEffect, useMemo, useState } from "react";

const SKILLS = [
  ["technical_knowledge", "Technical Knowledge"],
  ["problem_solving", "Problem Solving"],
  ["communication", "Communication"],
  ["clarity", "Clarity"],
];

function Performance() {
  const [progress, setProgress] = useState([]);
  const [selectedSkill, setSelectedSkill] = useState(SKILLS[0][0]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await fetch("http://localhost:8000/interviews/progress", { credentials: "include" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to load performance data.");
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

  const skillData = useMemo(() => progress.filter((item) => item.skill_scores && item.skill_scores[selectedSkill] != null), [progress, selectedSkill]);
  const improvements = useMemo(() => calculateImprovements(progress), [progress]);

  return (
    <div>
      <div className="page-header"><div><p className="eyebrow">Performance</p><h1 className="page-title">Performance</h1><p className="page-subtitle">Track overall results and see how individual skills change over multiple interview sessions.</p></div></div>
      {loading && <p className="muted">Loading performance...</p>}
      {error && <div className="alert alert-error">{error}</div>}
      {!loading && !error && <>
        <section className="card card-pad" style={{ marginBottom: 16 }}>
          <div className="card-header"><div><h2 className="section-title">Overall Score Progress</h2><p className="section-description">The line shows your actual completed-session scores. It may rise or fall between interviews.</p></div></div>
          {progress.length ? <LineChart data={progress} valueKey="overall_score" label="Overall interview score over time" /> : <div className="empty-state"><p>Complete interviews to see your overall progress.</p></div>}
        </section>

        <section className="card card-pad" style={{ marginBottom: 16 }}>
          <div className="card-header"><div><h2 className="section-title">Skill Analysis</h2><p className="section-description">Select one skill to see its progression across completed sessions.</p></div><label className="input-label" style={{ minWidth: 210 }}>Skill<select className="select" value={selectedSkill} onChange={(e) => setSelectedSkill(e.target.value)}>{SKILLS.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label></div>
          {skillData.length ? <LineChart data={skillData} valueKey="skill_scores" skillKey={selectedSkill} label={`${labelFor(selectedSkill)} over time`} /> : <div className="empty-state"><p>Skill trend data will appear once completed interviews include skill analysis.</p></div>}
        </section>

        <section className="grid-3">
          <Improvement title="Most Improved" value={improvements.mostImproved?.label || "—"} delta={improvements.mostImproved?.delta} />
          <Improvement title="Strongest Skill" value={improvements.strongest?.label || "—"} />
          <Improvement title="Needs Attention" value={improvements.needsAttention?.label || "—"} />
        </section>
      </>}
    </div>
  );
}

function Improvement({ title, value, delta }) {
  const positive = delta == null || delta >= 0;
  return <section className="card improvement-card"><div className="metric-label">{title}</div><div className="improvement-value">{value}</div>{delta != null && <div className={`improvement-change ${positive ? "text-success" : "text-danger"}`}>{delta >= 0 ? "↑" : "↓"} {Math.abs(delta).toFixed(1)} points from first available session</div>}</section>;
}

function LineChart({ data, valueKey, skillKey, label }) {
  const width = 920;
  const height = 300;
  const pad = { top: 26, right: 24, bottom: 50, left: 48 };
  const cw = width - pad.left - pad.right;
  const ch = height - pad.top - pad.bottom;
  const points = data.map((item, index) => {
    const value = valueKey === "skill_scores" ? Number(item.skill_scores?.[skillKey]) : Number(item[valueKey]);
    const x = pad.left + (data.length === 1 ? cw / 2 : index / (data.length - 1) * cw);
    const y = pad.top + ((10 - value) / 10) * ch;
    return { ...item, value, x, y };
  });
  const poly = points.map((p) => `${p.x},${p.y}`).join(" ");
  return <div className="chart-wrap" style={{ marginTop: 18 }}><svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>
    {[0,2,4,6,8,10].map((tick) => { const y = pad.top + ((10 - tick) / 10) * ch; return <g key={tick}><line x1={pad.left} y1={y} x2={width-pad.right} y2={y} stroke="var(--chart-grid)"/><text x="10" y={y+4} fontSize="11" fill="var(--chart-label)">{tick}</text></g>; })}
    <polyline fill="none" stroke="var(--accent-cyan)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" points={poly}/>
    {points.map((p, index) => <g key={`${p.session_id}-${index}`}><circle cx={p.x} cy={p.y} r="5" fill="var(--accent-indigo)" stroke="var(--surface-2)" strokeWidth="2"/><text x={p.x} y={height-19} textAnchor="middle" fontSize="11" fill="var(--chart-label)">#{index+1}</text><title>{`${new Date(p.created_at).toLocaleDateString()} · ${p.value.toFixed(1)}/10`}</title></g>)}
  </svg></div>;
}

function calculateImprovements(progress) {
  const first = {}; const latest = {};
  progress.forEach((item) => { for (const [key] of SKILLS) { const value = item.skill_scores?.[key]; if (value == null) continue; if (first[key] == null) first[key] = Number(value); latest[key] = Number(value); } });
  const deltas = SKILLS.filter(([key]) => first[key] != null && latest[key] != null).map(([key, label]) => ({ key, label, delta: latest[key] - first[key], latest: latest[key] }));
  return {
    mostImproved: deltas.length ? [...deltas].sort((a,b) => b.delta-a.delta)[0] : null,
    strongest: deltas.length ? [...deltas].sort((a,b) => b.latest-a.latest)[0] : null,
    needsAttention: deltas.length ? [...deltas].sort((a,b) => a.latest-b.latest)[0] : null,
  };
}
function labelFor(key) { return SKILLS.find(([skillKey]) => skillKey === key)?.[1] || key; }
export default Performance;
