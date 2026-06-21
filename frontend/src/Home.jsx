import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Home.css";

export default function Home() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [email, setEmail] = useState("Account");
  const [songs, setSongs] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const menuRef = useRef(null);
  const fileInputRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleSignOut() {
    localStorage.removeItem("token");
    navigate("/");
  }

  function handleSwitchAccount() {
    localStorage.removeItem("token");
    navigate("/?mode=login");
  }

  // Trigger the hidden file input when "Upload New Song" is clicked
  function handleUploadClick() {
    fileInputRef.current.click();
  }

  // Store the selected file and show the confirm step
  function handleFileSelected(e) {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedFile(file);
  }

  function handleCancelSelection() {
    setSelectedFile(null);
    fileInputRef.current.value = "";
  }

  function handleConfirmUpload() {
    // TODO: connect to backend upload flow, then navigate with song data
    navigate("/songPreview", { state: { file: selectedFile } });
  }

  return (
    <div className="home-bg">
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      {/* Hidden file input — triggered by the Upload New Song button */}
      <input
        ref={fileInputRef}
        type="file"
        accept="audio/*"
        style={{ display: "none" }}
        onChange={handleFileSelected}
      />

      {/* Profile menu — top right */}
      <div className="profile-menu" ref={menuRef}>
        <button className="profile-btn" onClick={() => setMenuOpen((v) => !v)}>
          <div className="profile-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
        </button>

        {menuOpen && (
          <div className="profile-dropdown">
            <div className="profile-dropdown-header">
              <div className="profile-avatar large">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <p className="profile-email">{email}</p>
            </div>

            <div className="profile-dropdown-divider" />

            <button className="profile-dropdown-item" onClick={handleSwitchAccount}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 1l4 4-4 4"/>
                <path d="M3 11V9a4 4 0 0 1 4-4h14"/>
                <path d="M7 23l-4-4 4-4"/>
                <path d="M21 13v2a4 4 0 0 1-4 4H3"/>
              </svg>
              Switch account
            </button>

            <button className="profile-dropdown-item danger" onClick={handleSignOut}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              Sign out
            </button>
          </div>
        )}
      </div>

      <div className="home-content">
        <div className="app-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
            <line x1="12" y1="19" x2="12" y2="22" />
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

        {selectedFile ? (
          /* Confirm step — shown after a file has been picked */
          <div className="file-confirm">
            <div className="file-confirm-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 18V5l12-2v13"/>
                <circle cx="6" cy="18" r="3"/>
                <circle cx="18" cy="16" r="3"/>
              </svg>
            </div>
            <div className="file-confirm-info">
              <p className="file-confirm-name">{selectedFile.name}</p>
              <p className="file-confirm-size">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            <div className="file-confirm-actions">
              <button className="home-btn secondary small" onClick={handleCancelSelection}>
                Cancel
              </button>
              <button className="home-btn primary small" onClick={handleConfirmUpload}>
                Continue
              </button>
            </div>
          </div>
        ) : (
          <div className="home-actions">
            <button className="home-btn primary" onClick={handleUploadClick}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              Upload New Song
            </button>
          </div>
        )}

        {/* Uploaded songs list */}
        <div className="songs-section">
          <h2 className="songs-heading">Your Songs</h2>

          {songs.length === 0 ? (
            <p className="songs-empty">No songs uploaded yet.</p>
          ) : (
            <div className="songs-list">
              {songs.map((song) => (
                <button
                  key={song._id}
                  className="song-item"
                  onClick={() => navigate(`/songs/${song._id}`)}
                >
                  <div className="song-item-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 18V5l12-2v13"/>
                      <circle cx="6" cy="18" r="3"/>
                      <circle cx="18" cy="16" r="3"/>
                    </svg>
                  </div>
                  <div className="song-item-info">
                    <p className="song-item-title">{song.title}</p>
                    <p className="song-item-status">{song.status}</p>
                  </div>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}