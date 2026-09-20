import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const API_URL = "http://localhost:8000";

function Register() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), email: email.trim(), password }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Registration failed.");
      navigate("/login", { replace: true, state: { registered: true } });
    } catch (err) {
      setError(err.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-grid" />
      <section className="auth-panel auth-form-panel register-panel">
        <div className="auth-form-brand">
          <span className="brand-mark">AI</span>
          <div>
            <div className="brand-name">InsightPrep</div>
            <div className="brand-sub">CANDIDATE ONBOARDING</div>
          </div>
        </div>
        <div className="auth-form-heading">
          <span className="status-badge status-cyan"><span className="status-dot" />CREATE PROFILE</span>
          <h1>Create your account</h1>
          <p>Set up your profile to unlock personalized resume-aware interview practice.</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="input-label">Full Name<input className="input" type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your full name" autoComplete="name" required /></label>
          <label className="input-label">Email<input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required /></label>
          <label className="input-label">Password<input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Create a secure password" autoComplete="new-password" required /></label>
          {error && <div className="alert alert-error">{error}</div>}
          <button className="primary-btn auth-submit" disabled={loading}>{loading ? "Creating..." : "Create Account"}</button>
        </form>

        <p className="auth-switch">Already have an account? <Link to="/login">Login</Link></p>
        <Link className="auth-back" to="/">← Back to entry</Link>
      </section>
    </main>
  );
}

export default Register;
