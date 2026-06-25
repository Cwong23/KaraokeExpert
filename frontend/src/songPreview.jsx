import { useLocation, useNavigate } from "react-router-dom";
import "./SongPreview.css";

export default function SongPreview() {
  const location = useLocation();
  const navigate = useNavigate();
  const songId = location.state?.song_id;
  const songName = location.state?.song_name || "Your song";
  const isReady = Boolean(songId);

  return (
    <div className="sp-bg">
      <div className="sp-orb sp-orb-1" />
      <div className="sp-orb sp-orb-2" />

      <button className="sp-back-btn" onClick={() => navigate("/home")}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 12H5M12 5l-7 7 7 7"/>
        </svg>
        Back to Home
      </button>

      <div className="sp-stage">
        {/* Signature element: vinyl record */}
        <div className={`sp-vinyl ${isReady ? "sp-vinyl-ready" : "sp-vinyl-stopped"}`}>
          <div className="sp-vinyl-grooves" />
          <div className="sp-vinyl-label">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 18V5l12-2v13"/>
              <circle cx="6" cy="18" r="3"/>
              <circle cx="18" cy="16" r="3"/>
            </svg>
          </div>
          {isReady && <div className="sp-vinyl-pulse" />}
        </div>

        <p className="sp-eyebrow">{songName}</p>
        <h1 className={`sp-status ${isReady ? "sp-status-ready" : "sp-status-failed"}`}>
          {isReady ? "Ready to sing" : "Song not found"}
        </h1>

        {!isReady && (
          <p className="sp-subtext">
            We couldn't find this song. Try uploading it again from the home page.
          </p>
        )}

        {isReady ? (
          <button className="sp-cta" onClick={() => navigate(`/sing/${songId}`)}>
            Start Singing
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M13 5l7 7-7 7"/>
            </svg>
          </button>
        ) : (
          <button className="sp-cta sp-cta-secondary" onClick={() => navigate("/home")}>
            Back to Home
          </button>
        )}
      </div>
    </div>
  );
}