import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

function Home() {
  const navigate = useNavigate();
  const { user } = useAuth();

  if (user) {
    navigate("/dashboard", { replace: true });
    return null;
  }

  return (
    <main className="auth-page auth-landing">
      <div className="auth-grid" />
      <section className="auth-landing-panel">
        <div className="brand-lockup">
          <span className="brand-mark">AI</span>
          <div>
            <div className="brand-name">InsightPrep</div>
            <div className="brand-sub">INTERVIEW INTELLIGENCE PLATFORM</div>
          </div>
        </div>

        <div className="auth-landing-copy">
          <span className="status-badge status-live"><span className="status-dot" />AI INTERVIEW SYSTEM</span>
          <h1>Practice smarter.<br /><span>Interview better.</span></h1>
          <p>Personalized interview preparation, resume intelligence, adaptive practice, and performance analytics in one focused workspace.</p>
        </div>

        <div className="auth-choice-grid">
          <button type="button" className="auth-choice primary-choice" onClick={() => navigate("/register")}>
            <span className="choice-kicker">NEW CANDIDATE</span>
            <strong>Create Account</strong>
            <span>Start building your interview profile and personalized practice history.</span>
            <span className="choice-arrow">→</span>
          </button>
          <button type="button" className="auth-choice secondary-choice" onClick={() => navigate("/login")}>
            <span className="choice-kicker">RETURNING USER</span>
            <strong>Login</strong>
            <span>Continue from your existing dashboard, resume, and interview history.</span>
            <span className="choice-arrow">→</span>
          </button>
        </div>

        <div className="auth-trust-row">
          <span>Resume-aware interviews</span><span>•</span><span>Adaptive questioning</span><span>•</span><span>Performance trends</span>
        </div>
      </section>
    </main>
  );
}

export default Home;
