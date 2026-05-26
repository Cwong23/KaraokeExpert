import { useNavigate } from "react-router-dom";
import "./Home.css";

export default function Home() {
  const navigate = useNavigate();

  function handleSignOut() {
    localStorage.removeItem("token");
    navigate("/");
  }

  return (
    <div className="home-bg">
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      <button className="back-btn" onClick={handleSignOut}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 12H5M12 5l-7 7 7 7"/>
        </svg>
        Back to Login
      </button>

      <div className="home-content">
        {/* App icon placeholder */}
        <div className="app-icon">
          <svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 3v10.55A4 4 0 1 0 11 17V7h4V3H9z"/>
          </svg>
          <div className="icon-glow" />
        </div>

        <div className="home-text">
          <h1 className="home-title">Karaoke Expert</h1>
          <p className="home-desc">
            Upload any song and get instant karaoke with instrumental track,
            synchronized lyrics, and real-time pitch comparison. Test your singing
            accuracy!
          </p>
        </div>

        <div className="home-actions">
          <button className="home-btn primary">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Upload New Song
          </button>
          <button className="home-btn secondary">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="8" y1="6" x2="21" y2="6"/>
              <line x1="8" y1="12" x2="21" y2="12"/>
              <line x1="8" y1="18" x2="21" y2="18"/>
              <line x1="3" y1="6" x2="3.01" y2="6"/>
              <line x1="3" y1="12" x2="3.01" y2="12"/>
              <line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
            Select Uploaded Song
          </button>
        </div>
      </div>
    </div>
  );
}