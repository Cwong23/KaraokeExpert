import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Home.css";

const API_URL = "http://localhost:5000";

export default function Home() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [email, setEmail] = useState("Account");
  const [songs, setSongs] = useState([]);
  const [songsLoading, setSongsLoading] = useState(true);
  const [songsError, setSongsError] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const menuRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    async function fetchSongs() {
      const token = localStorage.getItem("token");
      try {
        const res = await fetch(`${API_URL}/songs/completed_songs`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to fetch completed songs");
        const { song_ids } = await res.json();
        console.log("SONGS: ", song_ids);

        const songDetails = await Promise.all(
          song_ids.map(async (id) => {
            try {
              const detailRes = await fetch(
                `${API_URL}/songs/${id}/song_data`,
                {
                  headers: { Authorization: `Bearer ${token}` },
                },
              );
              if (!detailRes.ok) throw new Error("Failed to fetch song data");
              const { song } = await detailRes.json();
              return {
                _id: id,
                title:
                  song?.title?.replace(/\.[^/.]+$/, "") || `${id.slice(0, 8)}`,
                status: song?.status || "complete",
              };
            } catch (err) {
              console.error(`Failed to fetch data for song ${id}:`, err);
              return {
                _id: id,
                title: `Song ${id.slice(0, 8)}`,
                status: "complete",
              };
            }
          }),
        );

        setSongs(songDetails);
      } catch (err) {
        console.error("Failed to load completed songs:", err);
        setSongsError("Couldn't load your songs. Try refreshing.");
      } finally {
        setSongsLoading(false);
      }
    }

    fetchSongs();
  }, []);

  function handleSignOut() {
    localStorage.removeItem("token");
    navigate("/");
  }

  function handleSwitchAccount() {
    localStorage.removeItem("token");
    navigate("/?mode=login");
  }

  function handleUploadClick() {
    fileInputRef.current.click();
  }

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
    navigate("/songPreview", {
      state: { audio_file: selectedFile, song_name: selectedFile.name },
    });
  }

  function handleOpenSong(song) {
    navigate("/songPreview", {
      state: { song_id: song._id, song_name: song.title },
    });
  }

  return (
    <div className="home-bg">
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      <input
        ref={fileInputRef}
        type="file"
        accept="audio/*"
        style={{ display: "none" }}
        onChange={handleFileSelected}
      />

      <div className="profile-menu" ref={menuRef}>
        <button className="profile-btn" onClick={() => setMenuOpen((v) => !v)}>
          <div className="profile-avatar">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
        </button>

        {menuOpen && (
          <div className="profile-dropdown">
            <div className="profile-dropdown-header">
              <div className="profile-avatar large">
                <svg
                  width="26"
                  height="26"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              </div>
              <p className="profile-email">{email}</p>
            </div>

            <div className="profile-dropdown-divider" />

            <button
              className="profile-dropdown-item"
              onClick={handleSwitchAccount}
            >
              <svg className="dropdown-icon" viewBox="0 0 24 24">
                <path d="M17 1l4 4-4 4" />
                <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                <path d="M7 23l-4-4 4-4" />
                <path d="M21 13v2a4 4 0 0 1-4 4H3" />
              </svg>
              Switch account
            </button>

            <button
              className="profile-dropdown-item danger"
              onClick={handleSignOut}
            >
              <svg className="dropdown-icon" viewBox="0 0 24 24">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              Sign out
            </button>
          </div>
        )}
      </div>

      <div className="home-content">
        <div className="app-icon">
          <svg viewBox="0 0 24 24">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
          <div className="icon-glow" />
        </div>

        <div className="home-text">
          <h1 className="home-title">Karaoke Expert</h1>
          <p className="home-desc">
            Upload any song and get instant karaoke with an instrumental track
            and synchronized lyrics.
          </p>
        </div>

        {selectedFile ? (
          <div className="file-confirm">
            <div className="file-confirm-icon">
              <svg viewBox="0 0 24 24">
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
              </svg>
            </div>
            <div className="file-confirm-info">
              <p className="file-confirm-name">{selectedFile.name}</p>
              <p className="file-confirm-size">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <div className="file-confirm-actions">
              <button
                className="home-btn secondary small"
                onClick={handleCancelSelection}
              >
                Cancel
              </button>
              <button
                className="home-btn primary small"
                onClick={handleConfirmUpload}
              >
                Continue
              </button>
            </div>
          </div>
        ) : (
          <div className="home-actions">
            <button className="home-btn primary" onClick={handleUploadClick}>
              <svg className="upload-icon" viewBox="0 0 24 24">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              Upload New Song
            </button>
          </div>
        )}

        {/* Uploaded songs list */}
        <div className="songs-section">
          <h2 className="songs-heading">Your Songs</h2>

          {songsLoading ? (
            <p className="songs-empty">Loading your songs...</p>
          ) : songsError ? (
            <p className="songs-empty">{songsError}</p>
          ) : songs.length === 0 ? (
            <p className="songs-empty">No songs uploaded yet.</p>
          ) : (
            <div className="songs-list">
              {songs.map((song) => (
                <button
                  key={song._id}
                  className="song-item"
                  onClick={() => handleOpenSong(song)}
                >
                  <div className="song-item-icon">
                    <svg viewBox="0 0 24 24">
                      <path d="M9 18V5l12-2v13" />
                      <circle cx="6" cy="18" r="3" />
                      <circle cx="18" cy="16" r="3" />
                    </svg>
                  </div>
                  <div className="song-item-info">
                    <p className="song-item-title">{song.title}</p>
                    <p className="song-item-status">{song.status}</p>
                  </div>
                  <svg className="dropdown-icon" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              ))}
            </div>
          )}
        </div>
        <p className="home-footer">
          Please do not upload copyrighted songs.
          <br />
          Disclaimer: Lyrics may not be 100% correct
        </p>
      </div>
    </div>
  );
}
