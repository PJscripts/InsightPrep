import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const API_URL = "http://localhost:8000";

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Invalid email or password.");
      window.location.href = "/dashboard";
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-grid" />
      <section className="auth-panel auth-form-panel">
        <div className="auth-form-brand">
          <span className="brand-mark">AI</span>
          <div>
            <div className="brand-name">InsightPrep</div>
            <div className="brand-sub">AUTHENTICATION</div>
          </div>
        </div>
        <div className="auth-form-heading">
          <span className="status-badge status-live"><span className="status-dot" />SECURE LOGIN</span>
          <h1>Welcome back</h1>
          <p>Resume your personalized interview preparation workspace.</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="input-label">Email<input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required /></label>
          <label className="input-label">Password<input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" autoComplete="current-password" required /></label>
          {error && <div className="alert alert-error">{error}</div>}
          <button className="primary-btn auth-submit" disabled={loading}>{loading ? "Authenticating..." : "Login to InsightPrep"}</button>
        </form>

        <div className="auth-divider"><span />or<span /></div>
        <p className="auth-switch">Don't have an account? <Link to="/register">Create Account</Link></p>
        <Link className="auth-back" to="/">← Back to entry</Link>
      </section>
    </main>
  );
}

export default Login;
