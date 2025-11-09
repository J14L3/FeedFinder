import { useState } from "react";
import { Link } from "react-router-dom";
import { API_BASE } from "./config";

export default function Login() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    const trimmedUsername = form.username.trim();
    const trimmedPassword = form.password.trim();

    // Username validation
    if (!trimmedUsername) {
      newErrors.username = "Username is required";
    } else if (trimmedUsername.length < 3) {
      newErrors.username = "Username must be at least 3 characters long";
    } else if (trimmedUsername.length > 50) {
      newErrors.username = "Username must be less than 50 characters";
    } else if (!/^[a-zA-Z0-9_]+$/.test(trimmedUsername)) {
      newErrors.username = "Username can only contain letters, numbers, and underscores";
    }

    // Password validation
    if (!trimmedPassword) {
      newErrors.password = "Password is required";
    } else if (trimmedPassword.length < 8) {
      newErrors.password = "Password must be at least 8 characters long";
    } else if (trimmedPassword.length > 128) {
      newErrors.password = "Password must be less than 128 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setErrors({});

    if (!validateForm()) {
      return;
    }

    const trimmedForm = {
      username: form.username.trim(),
      password: form.password.trim()
    };

    try {
      const res = await fetch(`${API_BASE}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(trimmedForm),
      });
      const data = await res.json();
      setMessage(data.message || "Done");
    } catch (error) {
      setMessage("An error occurred. Please try again.");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-6 rounded-2xl shadow-md w-80 space-y-4"
      >
        <h2 className="text-xl font-bold text-center">FeedFinder Login</h2>
        <div>
          <input
            type="text"
            placeholder="Username"
            className={`border p-2 w-full rounded ${errors.username ? 'border-red-500' : ''}`}
            value={form.username}
            onChange={(e) => {
              setForm({ ...form, username: e.target.value });
              if (errors.username) {
                setErrors({ ...errors, username: '' });
              }
            }}
            onBlur={validateForm}
          />
          {errors.username && <p className="text-red-500 text-sm mt-1">{errors.username}</p>}
        </div>
        <div>
          <input
            type="password"
            placeholder="Password"
            className={`border p-2 w-full rounded ${errors.password ? 'border-red-500' : ''}`}
            value={form.password}
            onChange={(e) => {
              setForm({ ...form, password: e.target.value });
              if (errors.password) {
                setErrors({ ...errors, password: '' });
              }
            }}
            onBlur={validateForm}
          />
          {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
        </div>
        <button
          type="submit"
          className="bg-blue-600 text-white p-2 rounded w-full hover:bg-blue-700"
        >
          Log In
        </button>

        {/* Show message */}
        {message && <p className="text-sm text-center text-gray-600">{message}</p>}

        {/* 👇 Register link */}
        <p className="text-sm text-center text-gray-600">
          Don’t have an account?{" "}
          <Link to="/register" className="text-blue-600 hover:underline">
            Register
          </Link>
        </p>
      </form>
    </div>
  );
}
