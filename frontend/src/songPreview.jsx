import { useState, useEffect, useMemo, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./SongPreview.css";

const API_URL = "http://localhost:5000";

// Split lines by if there is long difference in their time stamps (will use periods later)
// To avoid long lines, have a max character count of 60
function buildLyricsLines(data, maxGapSeconds = 1.5, maxLineLength = 60) {
  const lines = [];
  let current = "";
  let prevTime = null;

  data.forEach((entry) => {
    const isNewSection = prevTime !== null && entry.time - prevTime >= maxGapSeconds;

    if (isNewSection && current) {
      lines.push(current);
      current = "";
    }

    const candidate = current ? `${current} ${entry.words}` : entry.words;

    if (candidate.length > maxLineLength && current) {
      lines.push(current);
      current = entry.words;
    } else {
      current = candidate;
    }

    prevTime = entry.time;
  });

  if (current) lines.push(current);
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


  const lyricsLines = useMemo(() => buildLyricsLines(lyricsData), [lyricsData]);

  // Helper function to check if the song is ready repeatedly
  function pollStatus(token, songId) {
    return new Promise((resolve, reject) => {
      async function check() {
        try {
          const res = await fetch(`${API_URL}/songs/song_status?song_id=${songId}`, {
            method: "GET",
            headers: { Authorization: `Bearer ${token}` },
          });

          if (!res.ok) throw new Error("Status check failed");
          const data = await res.json();

          if (data.status === "ready") {
            resolve();
          } else if (data.status === "failed") {
            reject(new Error("Processing failed"));
          } else {
            setTimeout(check, 2500); // keep polling
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
    return await lyricsRes.json();
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
      const lyrics = await fetchSongData(token, song_id);
      setLyricsData(lyrics);

      // We're already on SongPreview, so just flip status instead of navigating
      setStatus("ready");

    } catch (err) {
      setUploadError("Something went wrong. Please try again.");
      setStatus("failed");
    }
  }

  // Kick off the upload flow as soon as we land on this page, if a file was passed in
  const hasStarted = useRef(false);
  useEffect(() => {
    if (audioFile && !hasStarted.current) {
      hasStarted.current = true;
      handleConfirmUpload();
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
            <p className="sp-lyrics-label">Lyrics Preview</p>
            <div className="sp-lyrics-scroll">
              {lyricsLines.length > 0 ? (
                lyricsLines.map((line, i) => (
                  <p key={i} className="sp-lyrics-line">{line}</p>
                ))
              ) : (
                <p className="sp-lyrics-line">No lyrics available for this song.</p>
              )}
            </div>
          </div>
        )}

        {status === "failed" && (
          <button className="sp-cta sp-cta-secondary" onClick={() => navigate("/home")}>
            Back to Home
          </button>
        )}
      </div>
    </div>
  );
}