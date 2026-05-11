import { useState } from "react";
import { useSignIn, useSignUp, useUser } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState("login");
  const { isSignedIn } = useUser();
  const navigate = useNavigate();

  // If already signed in, go straight to home
  if (isSignedIn) {
    navigate("/home");
    return null;
  }

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

function GoogleButton({ mode }) {
  const { signIn } = useSignIn();
  const { signUp } = useSignUp();

  async function handleGoogleAuth() {
    const clerk = mode === "login" ? signIn : signUp;
    await clerk.authenticateWithRedirect({
      strategy: "oauth_google",
      redirectUrl: "/sso-callback",
      redirectUrlComplete: "/home",
    });
  }

  return (
    <button className="google-btn" onClick={handleGoogleAuth}>
      <svg className="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
      </svg>
      Continue with Google
    </button>
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
  const { signIn, setActive } = useSignIn();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    setError("");
    setLoading(true);
    try {
      const result = await signIn.create({ identifier: email, password });
      if (result.status === "complete") {
        await setActive({ session: result.createdSessionId });
        navigate("/home");
      }
    } catch (err) {
      setError(err.errors?.[0]?.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-form">
      <GoogleButton mode="login" />
      <Divider />
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
  const { signUp, setActive } = useSignUp();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [code, setCode] = useState("");

  async function handleSignUp() {
    setError("");
    setLoading(true);
    try {
      await signUp.create({ emailAddress: email, password });
      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
      setVerifying(true);
    } catch (err) {
      setError(err.errors?.[0]?.message || "Sign up failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify() {
    setError("");
    setLoading(true);
    try {
      const result = await signUp.attemptEmailAddressVerification({ code });
      if (result.status === "complete") {
        await setActive({ session: result.createdSessionId });
        navigate("/home");
      }
    } catch (err) {
      setError(err.errors?.[0]?.message || "Invalid code. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (verifying) {
    return (
      <div className="auth-form">
        <p className="verify-info">
          We sent a verification code to <strong>{email}</strong>. Enter it below to confirm your account.
        </p>
        <div className="form-group">
          <label className="form-label">Verification Code</label>
          <input
            type="text"
            className="form-input"
            placeholder="Enter code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
        </div>
        {error && <p className="auth-error">{error}</p>}
        <button className="auth-btn" onClick={handleVerify} disabled={loading}>
          {loading ? "Verifying..." : "Verify Email"}
        </button>
      </div>
    );
  }

  return (
    <div className="auth-form">
      <GoogleButton mode="signup" />
      <Divider />
      <div id="clerk-captcha" />
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