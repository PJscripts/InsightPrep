import { useRef, useState } from "react";
import { useAuth } from "../context/useAuth";
import { uploadResume } from "../services/resumeService";

function Resume() {
  const { user } = useAuth();
  const inputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  function chooseFile(file) {
    if (!file) return;
    setSelectedFile(file);
    setError("");
    setSuccess("");
  }

  function validate(file) {
    const allowed = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
    if (!allowed.includes(file.type)) return "Only PDF and DOCX files are supported.";
    if (file.size > 5 * 1024 * 1024) return "File size must be 5 MB or less.";
    return "";
  }

  function handleInputChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const problem = validate(file);
    if (problem) { setError(problem); return; }
    chooseFile(file);
  }

  async function handleUpload(event) {
    event.preventDefault();
    if (!selectedFile) return setError("Choose a PDF or DOCX resume first.");
    const problem = validate(selectedFile);
    if (problem) return setError(problem);
    setUploading(true); setError(""); setSuccess("");
    try {
      const result = await uploadResume(selectedFile);
      setAnalysis(result.analysis || null);
      setSelectedFile(null);
      setSuccess("Resume processed successfully. New personalized interviews will use this latest analyzed resume.");
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Resume upload failed.");
    } finally { setUploading(false); }
  }

  const skillGroups = groupSkills(analysis?.skills || []);

  return (
    <div>
      <div className="page-header"><div><span className="eyebrow">RESUME INTELLIGENCE</span><h1 className="page-title">Your Resume</h1><p className="page-subtitle">Upload, replace, and review the resume used for personalized interviews.</p></div></div>

      <section className="card upload-shell" style={{ marginBottom: 16 }}>
        <div className="upload-topline"><span className="status-badge status-cyan"><span className="status-dot" />DOCUMENT PIPELINE READY</span><span className="mono">PDF / DOCX · MAX 5 MB</span></div>
        <form onSubmit={handleUpload}>
          <button type="button" className={`drop-zone${dragOver ? " drag-over" : ""}`} onClick={() => inputRef.current?.click()} onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={(e) => { e.preventDefault(); setDragOver(false); const file = e.dataTransfer.files?.[0]; const problem = file && validate(file); if (problem) setError(problem); else chooseFile(file); }} disabled={uploading}>
            <div className="drop-icon">↥</div><strong>{selectedFile ? selectedFile.name : "Drop your resume here"}</strong><span>{selectedFile ? "Ready to analyze" : "or click to browse files"}</span><small>We support PDF and DOCX documents.</small>
          </button>
          <input ref={inputRef} className="file-input-hidden" type="file" accept=".pdf,.docx" onChange={handleInputChange} disabled={uploading} />
          <div className="upload-actions"><span className="muted">Signed in as {user?.name || "candidate"}</span><button className="primary-btn" disabled={uploading || !selectedFile}>{uploading ? "Analyzing Resume..." : "Upload / Replace Resume"}</button></div>
        </form>
      </section>

      {success && <div className="alert alert-success" style={{ marginBottom: 16 }}>{success}</div>}
      {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}

      {analysis ? <>
        <div className="stats-grid"><Metric label="Skills Identified" value={(analysis.skills || []).length} /><Metric label="Projects" value={(analysis.projects || []).length} /><Metric label="Experience Entries" value={(analysis.experience || []).length} /></div>
        <section className="card card-pad" style={{ marginBottom: 16 }}><div className="card-header"><div><div className="card-section-kicker">EXTRACTED SKILLS</div><h2 className="section-title">Capability map</h2><p className="section-description">Grouped skills extracted directly from the processed resume.</p></div><span className="status-badge status-success">ANALYZED</span></div>{Object.keys(skillGroups).length ? Object.entries(skillGroups).map(([group, values]) => <div className="skill-group" key={group}><h3 className="skill-group-title">{group}</h3><div className="chips">{values.map((skill) => <span className="chip" key={skill}>{skill}</span>)}</div></div>) : <p className="muted">No skills were identified.</p>}</section>
        <div className="grid-2" style={{ marginBottom: 16 }}><InsightCard title="Strengths" items={analysis.strengths} tone="success" empty="No strengths were identified." /><InsightCard title="Areas to Improve" items={analysis.skill_gaps} tone="warning" empty="No major gaps were identified." /></div>
        <section className="card card-pad" style={{ marginBottom: 16 }}><div className="card-section-kicker">PREPARATION MAP</div><h2 className="section-title">Recommended topics</h2><p className="section-description">Suggested preparation topics based on the current analyzed resume.</p><div className="topic-grid" style={{ marginTop: 14 }}>{(analysis.recommended_topics || []).map((topic) => <div className="topic-card" key={topic}>{topic}</div>)}</div></section>
        <section className="card card-pad"><div className="card-section-kicker">SOURCE DETAILS</div><h2 className="section-title">Experience, education & projects</h2><div className="grid-2" style={{ marginTop: 16 }}><InfoBlock title="Experience" items={analysis.experience} /><InfoBlock title="Education" items={analysis.education} /></div><div style={{ marginTop: 16 }}><InfoBlock title="Projects" items={analysis.projects} /></div></section>
      </> : <section className="card empty-state"><div><div className="empty-icon">CV</div><h2 className="section-title">No processed resume yet</h2><p>Upload a PDF or DOCX to generate the structured resume analysis used by personalized interviews.</p></div></section>}
    </div>
  );
}

function Metric({ label, value }) { return <div className="card metric-card metric-indigo"><div className="metric-label">{label}</div><strong className="metric-value">{value}</strong></div>; }
function InsightCard({ title, items = [], tone, empty }) { return <section className="card card-pad"><div className="card-section-kicker">AI SIGNAL</div><h2 className="section-title">{title}</h2><div className="list" style={{ marginTop: 14 }}>{items.length ? items.map((item) => <div className="item-card" key={formatItem(item)}><span className={`badge badge-${tone === "success" ? "success" : "warning"}`}>{tone === "success" ? "Strength" : "Focus"}</span><div style={{ marginTop: 7, lineHeight: 1.55 }}>{formatItem(item)}</div></div>) : <p className="muted">{empty}</p>}</div></section>; }
function InfoBlock({ title, items = [] }) { return <div><h3 className="info-block-title">{title}</h3><div className="list" style={{ marginTop: 10 }}>{items.length ? items.map((item, index) => <div className="item-card" key={`${title}-${index}`}>{formatItem(item)}</div>) : <p className="muted">No information available.</p>}</div></div>; }
function formatItem(item) { if (typeof item === "string") return item; if (!item || typeof item !== "object") return String(item); return item.title || item.name || item.description || JSON.stringify(item); }
function groupSkills(skills) { const groups = { Programming: [], Web: [], Databases: [], Tools: [], Other: [] }; for (const item of skills) { const skill = formatItem(item); const lower = skill.toLowerCase(); if (["python","java","c++","c","javascript","typescript","go","rust"].some((x) => lower.includes(x))) groups.Programming.push(skill); else if (["react","html","css","node","fastapi","django","express"].some((x) => lower.includes(x))) groups.Web.push(skill); else if (["sql","postgres","mysql","mongodb","redis"].some((x) => lower.includes(x))) groups.Databases.push(skill); else if (["git","docker","aws","linux","azure","gcp","postman"].some((x) => lower.includes(x))) groups.Tools.push(skill); else groups.Other.push(skill); } return Object.fromEntries(Object.entries(groups).filter(([, values]) => values.length)); }
export default Resume;
