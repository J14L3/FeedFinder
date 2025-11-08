import React from "react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./index.css"; // Tailwind CSS import

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);