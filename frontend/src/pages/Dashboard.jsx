import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  async function handleLogout() {
    try {
      await logout();
      navigate("/login");
    } catch {
      // Keep the user on the page if logout fails.
    }
  }

  if (!user) {
    return <p>Loading...</p>;
  }

  return (
    <div>
      <h1>Dashboard</h1>

      <p>Welcome, {user.name}!</p>
      <p>Email: {user.email}</p>

      <button type="button" onClick={handleLogout}>
        Logout
      </button>
    </div>
  );
}

export default Dashboard;
