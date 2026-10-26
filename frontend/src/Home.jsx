import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Home.css";

const API_URL = import.meta.env.VITE_API_URL;

// Validation constants
const MAX_FILE_SIZE_MB = 50;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const MAX_FILE_NAME_LENGTH = 255;
const ALLOWED_AUDIO_EXTENSIONS = [
  "mp3",
  "wav",
  "m4a",
  "aac",
  "flac",
  "ogg",
  "oga",
  "opus",
  "webm",
];

function validateAudioFile(file) {
  if (!file) return "No file selected.";
  if (!(file instanceof File)) return "Invalid file.";

  const name = typeof file.name === "string" ? file.name.trim() : "";
  if (!name) return "File must have a name.";
  if (name.length > MAX_FILE_NAME_LENGTH)
    return `File name must be ${MAX_FILE_NAME_LENGTH} characters or fewer.`;

  const extension = name.includes(".")
    ? name.split(".").pop().toLowerCase()
    : "";
  const hasAudioMime =
    typeof file.type === "string" && file.type.startsWith("audio/");
  const hasAudioExtension = ALLOWED_AUDIO_EXTENSIONS.includes(extension);
  if (!hasAudioMime && !hasAudioExtension)
    return "Please choose an audio file (e.g. MP3, WAV, M4A).";

  if (file.size === 0) return "This file is empty.";
  if (file.size > MAX_FILE_SIZE_BYTES)
    return `File is too large. Maximum size is ${MAX_FILE_SIZE_MB} MB.`;

  return "";
}

function isValidSongId(id) {
  return typeof id === "string" && id.trim().length > 0;
}

const AUDIO_CHECK_TIMEOUT_MS = 15000;
const CORRUPTED_FILE_ERROR =
  "This audio file appears to be corrupted or in an unsupported format.";

function withTimeout(promise, ms) {
  let timer;
  const timeout = new Promise((resolve) => {
    timer = setTimeout(() => resolve(false), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

function checkAudioMetadata(file) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const audio = document.createElement("audio");
    audio.preload = "metadata";

    let done = false;
    function finish(ok) {
      if (done) return;
      done = true;
      audio.onloadedmetadata = null;
      audio.onerror = null;
      audio.removeAttribute("src");
      audio.load();
      URL.revokeObjectURL(url);
      resolve(ok);
    }

    audio.onloadedmetadata = () => finish(audio.duration > 0);
    audio.onerror = () => finish(false);
    audio.src = url;
  });
}

async function checkAudioDecodes(file) {
  const OfflineCtx =
    window.OfflineAudioContext || window.webkitOfflineAudioContext;
  if (!OfflineCtx) return true;
  try {
    const ctx = new OfflineCtx(1, 1, 44100);
    const buffer = await file.arrayBuffer();
    const decoded = await ctx.decodeAudioData(buffer);
    return (
      decoded.duration > 0 && decoded.numberOfChannels > 0 && decoded.length > 0
    );
  } catch {
    return false;
  }
}

async function validateAudioContents(file) {
  const metadataOk = await withTimeout(
    checkAudioMetadata(file),
    AUDIO_CHECK_TIMEOUT_MS,
  );
  if (!metadataOk) return CORRUPTED_FILE_ERROR;

  const decodesOk = await withTimeout(
    checkAudioDecodes(file),
    AUDIO_CHECK_TIMEOUT_MS,
  );
  if (!decodesOk) return CORRUPTED_FILE_ERROR;

  return "";
}

export default function Home() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [email, setEmail] = useState("Account");
  const [songs, setSongs] = useState([]);
  const [songsLoading, setSongsLoading] = useState(true);
  const [songsError, setSongsError] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [validatingFile, setValidatingFile] = useState(false);
  const menuRef = useRef(null);
  const fileInputRef = useRef(null);
  const validationIdRef = useRef(0);

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
      if (!token) {
        setSongsLoading(false);
        navigate("/?mode=login");
        return;
      }
      if (!API_URL) {
        console.error("VITE_API_URL is not set");
        setSongsError("Couldn't load your songs. Try refreshing.");
        setSongsLoading(false);
        return;
      }
      try {
        const res = await fetch(`${API_URL}/songs/completed_songs`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.status === 401) {
          localStorage.removeItem("token");
          navigate("/?mode=login");
          return;
        }
        if (!res.ok) throw new Error("Failed to fetch completed songs");
        const data = await res.json();
        const song_ids = Array.isArray(data?.song_ids)
          ? data.song_ids.filter(isValidSongId)
          : [];

        const songDetails = await Promise.all(
          song_ids.map(async (id) => {
            try {
              const detailRes = await fetch(
                `${API_URL}/songs/${encodeURIComponent(id)}/song_data`,
                {
                  headers: { Authorization: `Bearer ${token}` },
                },
              );
              if (!detailRes.ok) throw new Error("Failed to fetch song data");
              const { song } = await detailRes.json();
              return {
                _id: id,
                title:
                  (typeof song?.title === "string" &&
                    song.title.replace(/\.[^/.]+$/, "").trim()) ||
                  `${id.slice(0, 8)}`,
                status:
                  typeof song?.status === "string" && song.status
                    ? song.status
                    : "complete",
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
    if (!fileInputRef.current || validatingFile) return;
    setUploadError("");
    fileInputRef.current.click();
  }

  async function handleFileSelected(e) {
    const input = e.target;
    const file = input.files?.[0];
    if (!file) return;

    // Ignore results from an older check if a newer file was picked
    const validationId = ++validationIdRef.current;
    setSelectedFile(null);
    setUploadError("");

    let error = validateAudioFile(file);
    if (!error) {
      setValidatingFile(true);
      error = await validateAudioContents(file);
      if (validationId !== validationIdRef.current) return;
      setValidatingFile(false);
    }

    if (error) {
      setUploadError(error);
      // Reset so the same file can be re-selected after an error
      input.value = "";
      return;
    }
    setSelectedFile(file);
  }

  function handleCancelSelection() {
    validationIdRef.current++;
    setValidatingFile(false);
    setSelectedFile(null);
    setUploadError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function handleConfirmUpload() {
    const error = validateAudioFile(selectedFile);
    if (error) {
      setUploadError(error);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    navigate("/songPreview", {
      state: { audio_file: selectedFile, song_name: selectedFile.name },
    });
  }

  function handleOpenSong(song) {
    if (!song || !isValidSongId(song._id)) return;
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
            <button
              className="home-btn primary"
              onClick={handleUploadClick}
              disabled={validatingFile}
            >
              <svg className="upload-icon" viewBox="0 0 24 24">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              {validatingFile ? "Checking file..." : "Upload New Song"}
            </button>
          </div>
        )}

        {uploadError && (
          <p className="upload-error" role="alert">
            {uploadError}
          </p>
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
