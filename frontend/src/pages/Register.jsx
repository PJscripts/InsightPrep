import { useState } from "react";
import { registerUser } from "../services/authService";

function Register() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setMessage("");
    setError("");
    setLoading(true);

    try {
      const user = await registerUser(formData);

      setMessage(`Account created for ${user.name}.`);
      setFormData({
        name: "",
        email: "",
        password: "",
      });
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(detail || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>Create Account</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="name">Name</label>
          <input
            id="name"
            name="name"
            type="text"
            value={formData.name}
            onChange={handleChange}
            required
            minLength={2}
            maxLength={100}
          />
        </div>

        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={8}
            maxLength={128}
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Creating Account..." : "Register"}
        </button>
      </form>

      {message && <p>{message}</p>}
      {error && <p>{error}</p>}
    </div>
  );
}

export default Register;
