import './App.css';

function App() {
  return (
    <div className="container">
      <h1>Karaoke Expert</h1>
      <p className="subtitle">
        Upload a song to get the instrumental track and practice your singing with real-time pitch feedback.
        All languages supported!
      </p>

      <div className="upload-box">
        <p>Drag and drop your song here</p>
        <p className="or">or</p>
        <button>Browse Files</button>
      </div>
    </div>
  );
}

export default App;