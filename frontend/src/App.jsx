import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";

const API_URL = "http://localhost:5000";

export default function App() {
  const [tab, setTab] = useState("login");
  const navigate = useNavigate();

  // If already logged in, go straight to home
  useEffect(() => {
    if (localStorage.getItem("token")) {
      navigate("/home");
    }
  }, [navigate]);

  return (
    <div className="auth-bg">
      {/* Keeping background orbs identical to the Home page */}
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      <div className="auth-card">
        <div className="auth-header">
          {/* Microphone Icon added to mirror Home design language */}
          <div className="app-icon-wrapper">
            <svg className="app-icon" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
              <line x1="12" y1="19" x2="12" y2="22" />
            </svg>
            <div className="icon-glow" />
          </div>
          <h1 className="auth-title">Karaoke Expert</h1>
          <p className="auth-subtitle">Sing your heart out</p>
        </div>

        <div className="auth-tabs">
          <button
            className={`auth-tab ${tab === "login" ? "active" : ""}`}
            onClick={() => setTab("login")}
          >
            Login
          </button>
          <button
            className={`auth-tab ${tab === "signup" ? "active" : ""}`}
            onClick={() => setTab("signup")}
          >
            Sign Up
          </button>
        </div>

        {tab === "login" ? (
          <LoginForm onSwitchTab={() => setTab("signup")} />
        ) : (
          <SignUpForm onSwitchTab={() => setTab("login")} />
        )}
      </div>
    </div>
  );
}

function LoginForm({ onSwitchTab }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem("token", data.token);
        navigate("/home");
      } else {
        setError(data.error || "Login failed. Please try again.");
      }
    } catch (err) {
      setError("Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-form">
      <div className="form-group">
        <label className="form-label">Email</label>
        <input
          type="email"
          className="form-input"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div className="form-group">
        <label className="form-label">Password</label>
        <input
          type="password"
          className="form-input"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      {error && <p className="auth-error">{error}</p>}
      <button className="auth-btn primary" onClick={handleLogin} disabled={loading}>
        {loading ? "Logging in..." : "Login"}
      </button>
      <p className="auth-switch">
        Don't have an account?{" "}
        <span className="auth-link" onClick={onSwitchTab}>Sign up</span>
      </p>
    </div>
  );
}

function SignUpForm({ onSwitchTab }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSignUp() {
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (response.ok) {
        const loginResponse = await fetch(`${API_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const loginData = await loginResponse.json();
        if (loginResponse.ok) {
          localStorage.setItem("token", loginData.token);
          navigate("/home");
        }
      } else {
        setError(data.error || "Sign up failed. Please try again.");
      }
    } catch (err) {
      setError("Sign up failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-form">
      <div className="form-group">
        <label className="form-label">Email</label>
        <input
          type="email"
          className="form-input"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div className="form-group">
        <label className="form-label">Password</label>
        <input
          type="password"
          className="form-input"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      {error && <p className="auth-error">{error}</p>}
      <button className="auth-btn primary" onClick={handleSignUp} disabled={loading}>
        {loading ? "Creating account..." : "Create Account"}
      </button>
      <p className="auth-switch">
        Already have an account?{" "}
        <span className="auth-link" onClick={onSwitchTab}>Login</span>
      </p>
    </div>
  );
}