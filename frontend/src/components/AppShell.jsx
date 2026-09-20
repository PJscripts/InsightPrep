import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../context/useAuth";
import "../styles/app.css";

const navigation = [
  { to: "/dashboard", label: "Dashboard", icon: "grid" },
  { to: "/resume", label: "Resume", icon: "file" },
  { to: "/interview", label: "Interview", icon: "video" },
  { to: "/history", label: "History", icon: "history" },
  { to: "/performance", label: "Performance", icon: "trend" },
];

function Icon({ type }) {
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    file: <><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/></>,
    video: <><rect x="3" y="5" width="13" height="14" rx="2"/><path d="m16 10 5-3v10l-5-3z"/></>,
    history: <><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/><path d="M12 7v5l3 2"/></>,
    trend: <><path d="M4 17 9 12l4 3 7-8"/><path d="M16 7h4v4"/></>,
  };
  return <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[type]}</svg>;
}

function AppShell() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const current = navigation.find((item) => location.pathname === item.to || location.pathname.startsWith(`${item.to}/`));
  const activePath = location.pathname.startsWith("/interview/") ? (location.pathname.endsWith("/result") ? "/history" : "/interview") : current?.to;

  async function handleLogout() {
    try { await logout(); } catch { /* keep UI stable if logout fails */ }
    window.location.href = "/";
  }

  const initials = (user?.name || "U").split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="app-shell">
      {menuOpen && <button className="mobile-scrim" aria-label="Close menu" onClick={() => setMenuOpen(false)} />}
      <aside className={`sidebar${menuOpen ? " mobile-open" : ""}`}>
        <div>
          <div className="brand-block">
            <div className="brand">
              <span className="brand-mark">AI</span>
              <div><span className="brand-text">InsightPrep</span><span className="brand-sub">/ CONSOLE</span></div>
            </div>
          </div>
          <div className="rail-label">WORKSPACE</div>
          <nav className="sidebar-nav" aria-label="Primary navigation">
            {navigation.map((item) => (
              <NavLink key={item.to} to={item.to} onClick={() => setMenuOpen(false)} className={({ isActive }) => `nav-link${(isActive || activePath === item.to) ? " active" : ""}`}>
                <Icon type={item.icon} />
                <span className="nav-label">{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="account-block">
          <div className="account-row"><div className="avatar">{initials}</div><div className="account-meta"><div className="account-name">{user?.name || "Candidate"}</div><div className="account-email">{user?.email || ""}</div></div></div>
          <button type="button" className="logout-btn" onClick={handleLogout}><span className="logout-text">Logout</span><span aria-hidden="true">↪</span></button>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <button className="mobile-menu" type="button" onClick={() => setMenuOpen((value) => !value)} aria-label="Open navigation">☰</button>
          <div className="topbar-breadcrumb"><span className="topbar-muted">InsightPrep Console</span><span className="topbar-sep">/</span><span>{current?.label || "Workspace"}</span></div>
          <div className="topbar-right"><span className="status-badge status-live"><span className="status-dot" />SYSTEM ONLINE</span><span className="topbar-user">{user?.name || "Candidate"}</span></div>
        </header>
        <main className="content"><Outlet /></main>
      </div>
    </div>
  );
}

export default AppShell;
