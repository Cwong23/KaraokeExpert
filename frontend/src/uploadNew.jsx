import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./uploadNew.css";

export default function Upload() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);

  function handleFile(f) {
    if (!f) return;
    setFile(f);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }

  function handleDragOver(e) {
    e.preventDefault();
    setDragging(true);
  }

  function handleDragLeave() {
    setDragging(false);
  }

  function handleChange(e) {
    handleFile(e.target.files[0]);
  }

  return (
    <div className="upload-bg">
      {/* Universal Background Orbs matching all other views */}
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      {/* Synchronized Navigation Header (Spread Left & Right) */}
      <header className="upload-nav">
        <button className="upload-back-nav-btn" onClick={() => navigate("/home")}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 5l-7 7 7 7"/>
          </svg>
          Back
        </button>

        <button className="upload-mysongs-nav-btn" onClick={() => navigate("/uploadOld")}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/>
            <line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
          My Songs
        </button>
      </header>

      {/* Main Glassmorphism Content Card */}
      <main className="upload-card">
        <div className="upload-card-header">
          <h1 className="upload-title">Upload Your Song</h1>
          <p className="upload-subtitle">
            We'll automatically extract the instrumental track and lyrics for you
          </p>
        </div>

        {/* Drop Zone */}
        <div
          className={`upload-dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
          onClick={() => fileInputRef.current.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            style={{ display: "none" }}
            onChange={handleChange}
          />

          {file ? (
            <div className="upload-file-info">
              <div className="upload-icon-wrap file-selected">
                <svg className="upload-glow-svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                </svg>
                <div className="icon-glow" />
              </div>
              <p className="upload-filename">{file.name}</p>
              <p className="upload-filesize">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              <p className="upload-change">Click to change file</p>
            </div>
          ) : (
            <div className="upload-prompt">
              <div className="upload-icon-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <div className="icon-glow" />
              </div>
              <p className="upload-prompt-text">Click to upload or drag and drop</p>
              <p className="upload-prompt-sub">MP3, WAV, or any audio format</p>
            </div>
          )}
        </div>

        {/* Crisp action button matching the main interface styling */}
        {file && (
          <button className="upload-submit-btn primary">
            Process Song
          </button>
        )}
      </main>
    </div>
  );
}