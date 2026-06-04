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
  }, []);

  return (
    <div className="auth-bg">
      <div className="auth-card">
        <div className="auth-header">
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

function Divider() {
  return (
    <div className="divider">
      <span className="divider-line" />
      <span className="divider-text">or</span>
      <span className="divider-line" />
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
      <button className="auth-btn" onClick={handleLogin} disabled={loading}>
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
        // auto login after signup
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
      <button className="auth-btn" onClick={handleSignUp} disabled={loading}>
        {loading ? "Creating account..." : "Create Account"}
      </button>
      <p className="auth-switch">
        Already have an account?{" "}
        <span className="auth-link" onClick={onSwitchTab}>Login</span>
      </p>
    </div>
  );
}