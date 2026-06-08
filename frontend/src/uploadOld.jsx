import { useNavigate } from "react-router-dom";
import "./uploadOld.css";

export default function Songs() {
  const navigate = useNavigate();

  // Mock array simulating your uploaded data
  const songs = [
    {
      id: 1,
      title: "Stray Kids 스트레이 키즈 CEREMONY Official Audio",
      artist: "Unknown Artist",
      duration: "3:00"
    }
  ];

  return (
    <div className="songs-bg">
      {/* Universal Background Orbs */}
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      {/* Styled Back Button matching App/Home navigation */}
      <button className="back-btn" onClick={() => navigate("/home")}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 12H5M12 5l-7 7 7 7"/>
        </svg>
        Back
      </button>

      <div className="songs-card">
        <div className="songs-header">
          <h1 className="songs-title">My Songs</h1>
          <p className="songs-subtitle">Select a song to practice or upload a new one</p>
        </div>

        <div className="songs-list">
          {songs.map((song) => (
            <div key={song.id} className="song-item">

              {/* Left Side: Replaced music note with a glowing microphone/audio badge */}
              <div className="song-icon-wrapper">
                <svg className="song-icon" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                </svg>
                <div className="song-icon-glow" />
              </div>

              {/* Center Side: Metadata */}
              <div className="song-meta">
                <h3 className="song-item-title">{song.title}</h3>
                <p className="song-item-desc">
                  {song.artist} <span className="bullet">•</span> {song.duration}
                </p>
              </div>

              {/* Right Side: Interactive Play Action Button */}
              <button className="play-btn" aria-label="Play song">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
              </button>

            </div>
          ))}
        </div>
      </div>
    </div>
  );
}