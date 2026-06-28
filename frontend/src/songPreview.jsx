import { useState, useEffect, useMemo, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./SongPreview.css";

const API_URL = "http://localhost:5000";

// Split lines by periods/question marks, with a max character count of 60 to avoid overly long lines.
// Each line also keeps the timestamp it started at, so playback can be synced to it.
function buildLyricsLines(data, maxLineLength = 60) {
  const lines = [];
  let current = "";
  let lineStartTime = 0;

  data.forEach((entry) => {
    // Break this entry's words into segments at each . or ? (punctuation stays attached to its segment)
    const segments = entry.words.match(/[^.?!]+[.?!]|[^.?!]+$/g) || [entry.words];

    segments.forEach((rawSegment) => {
      const segment = rawSegment.trim();
      if (!segment) return;

      if (!current) lineStartTime = entry.time;

      const candidate = current ? `${current} ${segment}` : segment;

      if (candidate.length > maxLineLength && current) {
        lines.push({ text: current, time: lineStartTime });
        current = segment;
        lineStartTime = entry.time;
      } else {
        current = candidate;
      }

      if (/[.?!]$/.test(segment)) {
        lines.push({ text: current, time: lineStartTime });
        current = "";
      }
    });
  });

  if (current) lines.push({ text: current, time: lineStartTime });
  return lines;
}

const LOADING_MESSAGES = {
  uploading: "Uploading your song...",
  processing: "Processing audio...",
  polling: "Almost ready...",
};

export default function SongPreview() {
  const location = useLocation();
  const navigate = useNavigate();
  const audioFile = location.state?.audio_file;
  const songName = location.state?.song_name || "Your song";

  const [songId, setSongId] = useState(location.state?.song_id || null);
  const [status, setStatus] = useState(audioFile ? "uploading" : "failed");
  const [uploadError, setUploadError] = useState("");
  const [lyricsData, setLyricsData] = useState([]);
  const [instrumentalUrl, setInstrumentalUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackStarted, setPlaybackStarted] = useState(false); // distinguishes "never played" from currentTime just happening to be 0
  const [menuOpen, setMenuOpen] = useState(false);
  const [email, setEmail] = useState("Account");
  const audioRef = useRef(null);
  const lineRefs = useRef([]);
  const menuRef = useRef(null);

  // Close the profile dropdown when clicking outside it
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


  const lyricsLines = useMemo(() => buildLyricsLines(lyricsData), [lyricsData]);

  // Figure out which lyric line is "active" right now, based on playback time.
  // Lines are in ascending time order, so this is just the last line whose time has passed.
  const activeLineIndex = useMemo(() => {
    if (!playbackStarted) return -1; // nothing should be highlighted before the user has pressed play
    let idx = -1;
    for (let i = 0; i < lyricsLines.length; i++) {
      if (lyricsLines[i].time <= currentTime) {
        idx = i;
      } else {
        break;
      }
    }
    return idx;
  }, [lyricsLines, currentTime, playbackStarted]);

  // Auto-scroll the active line into view as playback progresses
  useEffect(() => {
    const el = lineRefs.current[activeLineIndex];
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [activeLineIndex]);

  // Helper function to check if the song is ready repeatedly
  function pollStatus(token, songId) {
    return new Promise((resolve, reject) => {
      async function check() {
        try {
          const res = await fetch(`${API_URL}/songs/${songId}/song_status`, {
            method: "GET",
            headers: { Authorization: `Bearer ${token}` },
          });

          if (!res.ok) throw new Error("Status check failed");
          const data = await res.json();

          if (data.status === "complete") {
            resolve();
          } else if (data.status === "failed") {
            reject(new Error("Processing failed"));
          } else {
            setTimeout(check, 60000); // poll once every minute
          }
        } catch (err) {
          reject(err);
        }
      }
      check();
    });
  }

  // Fetch the processed song's data (including lyrics) once it's ready
  async function fetchSongData(token, songId) {
    const res = await fetch(`${API_URL}/songs/${songId}/song_objects`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) throw new Error("Failed to fetch song objects");

    const { urls } = await res.json();
    const [instrumentalUrl, lyricsUrl] = urls;

    const lyricsRes = await fetch(lyricsUrl);
    if (!lyricsRes.ok) throw new Error("Failed to fetch lyrics file");
    const lyrics = await lyricsRes.json();

    return { lyrics, instrumentalUrl };
  }

  async function handleConfirmUpload() {
    setStatus("uploading");
    setUploadError("");
    const token = localStorage.getItem("token");

    try {
      // Call create upload to get presigned URL
      const res = await fetch(`${API_URL}/songs/create_upload`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ song_name: audioFile.name }),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => null);
        console.error("create_upload failed:", errBody);
        throw new Error("Failed to create upload");
      }

      const { url, song_id } = await res.json();

      console.log("Got presigned URL:", url);
      console.log("Got song_id:", song_id);

      setSongId(song_id);

      // Using presigned URL to put upload song to MinIO
      const uploadRes = await fetch(url, {
        method: "PUT",
        body: audioFile,
      });

      if (!uploadRes.ok) throw new Error("Failed to upload file to storage");

      console.log("File uploaded successfully to MinIO!");

      // Call process_song so that song will become processed in backend
      setStatus("processing");
      const processRes = await fetch(`${API_URL}/songs/process_song`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ song_id }),
      });

      if (!processRes.ok) throw new Error("Failed to start processing");
      console.log("Processing started for song_id:", song_id);

      // Call helper function
      setStatus("polling");
      await pollStatus(token, song_id);
      console.log("Song is ready!");

      // Fetch the real lyrics now that processing is done
      const { lyrics, instrumentalUrl } = await fetchSongData(token, song_id);
      setLyricsData(lyrics);
      setInstrumentalUrl(instrumentalUrl);

      // We're already on SongPreview, so just flip status instead of navigating
      setStatus("ready");

    } catch (err) {
      setUploadError("Something went wrong. Please try again.");
      setStatus("failed");
    }
  }

  function togglePlayback() {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch((err) => console.error("Playback failed:", err));
      setPlaybackStarted(true);
    }
    setIsPlaying((prev) => !prev);
  }

  // Jump playback (and the lyric sync) back to the very start of the song
  function restartPlayback() {
    if (!audioRef.current) return;
    audioRef.current.currentTime = 0;
    setCurrentTime(0); // update immediately so the active lyric line resets right away, not on the next timeupdate tick
  }


  // Kick off the upload flow as soon as we land on this page, if a file was passed in.
  // If there's no file but a song_id was passed instead (e.g. opened from the library),
  // poll and fetch that real song's data.
  const hasStarted = useRef(false);
  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    if (audioFile) {
      handleConfirmUpload();
      return;
    }

    if (songId) {
      async function loadExistingSong() {
        setStatus("polling");
        const token = localStorage.getItem("token");
        try {
          await pollStatus(token, songId);
          const { lyrics, instrumentalUrl } = await fetchSongData(token, songId);
          setLyricsData(lyrics);
          setInstrumentalUrl(instrumentalUrl);
          setStatus("ready");
        } catch (err) {
          console.error("Failed to load song:", err);
          setUploadError(err.message);
          setStatus("failed");
        }
      }
      loadExistingSong();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isLoading = status === "uploading" || status === "processing" || status === "polling";
  const isReady = status === "ready";

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

      <div className="sp-stage">
        {/* Signature element: vinyl record */}
        <div className={`sp-vinyl ${isReady ? "sp-vinyl-ready" : !isLoading ? "sp-vinyl-stopped" : ""}`}>
          <div className="sp-vinyl-grooves" />
          <div className={`sp-vinyl-label ${isLoading ? "sp-vinyl-spinning" : ""}`}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 18V5l12-2v13"/>
              <circle cx="6" cy="18" r="3"/>
              <circle cx="18" cy="16" r="3"/>
            </svg>
          </div>
          {isReady && <div className="sp-vinyl-pulse" />}
        </div>

        <p className="sp-eyebrow">{songName}</p>

        {isLoading && (
          <>
            <h1 className="sp-status">{LOADING_MESSAGES[status]}</h1>
            <p className="sp-subtext">This may take a moment depending on the song length.</p>
          </>
        )}

        {status === "failed" && (
          <>
            <h1 className="sp-status sp-status-failed">Song not found</h1>
            <p className="sp-subtext">
              {uploadError || "We couldn't find this song. Try uploading it again from the home page."}
            </p>
          </>
        )}

        {isReady && (
          <div className="sp-lyrics-card">
            <div className="sp-lyrics-header">
              <p className="sp-lyrics-label">Lyrics Preview</p>
              <div className="sp-lyrics-controls">
                <button className="sp-restart-btn" onClick={restartPlayback} aria-label="Restart from beginning">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="19 20 9 12 19 4 19 20"></polygon>
                    <line x1="5" y1="19" x2="5" y2="5"></line>
                  </svg>
                </button>
                <button className="sp-play-btn" onClick={togglePlayback}>
                  {isPlaying ? "Pause" : "Play"}
                </button>
              </div>
            </div>
            <div className="sp-lyrics-scroll">
              {lyricsLines.length > 0 ? (
                lyricsLines.map((line, i) => (
                  <p
                    key={i}
                    ref={(el) => (lineRefs.current[i] = el)}
                    className={`sp-lyrics-line ${i === activeLineIndex ? "sp-lyrics-line-active" : ""}`}
                  >
                    {line.text}
                  </p>
                ))
              ) : (
                <p className="sp-lyrics-line">No lyrics available for this song.</p>
              )}
            </div>
          </div>
        )}

        {instrumentalUrl && (
          <audio
            ref={audioRef}
            src={instrumentalUrl}
            preload="auto"
            onEnded={() => setIsPlaying(false)}
            onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
          />
        )}

        {status === "failed" && (
          <button className="sp-cta sp-cta-secondary" onClick={() => navigate("/home")}>
            Back to Home
          </button>
        )}

        <p className="sp-footer">
          Please only upload music you own or have the rights to use. <br />
          Do not upload copyrighted songs.
        </p>
      </div>
    </div>
  );
}