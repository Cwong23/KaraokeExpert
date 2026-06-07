import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App.jsx";
import Home from "./Home.jsx";
import UploadNew from "./uploadNew.jsx";
import UploadOld from "./uploadOld.jsx";


createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/home" element={<Home />} />
        <Route path="/uploadNew" element={<UploadNew />} />
        <Route path="/uploadOld" element={<UploadOld />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
);