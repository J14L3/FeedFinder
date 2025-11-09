import { useState } from "react";
import { Link } from "react-router-dom";
import { API_BASE } from "./config";

export default function Register() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirm_password: "",
    bio: "",
    private: false,
  });

  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [errors, setErrors] = useState({});

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = () => {
    const newErrors = {};
    const trimmedUsername = form.username.trim();
    const trimmedEmail = form.email.trim();
    const trimmedPassword = form.password.trim();
    const trimmedConfirmPassword = form.confirm_password.trim();
    const trimmedBio = form.bio.trim();

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

    // Email validation
    if (!trimmedEmail) {
      newErrors.email = "Email is required";
    } else if (!validateEmail(trimmedEmail)) {
      newErrors.email = "Please enter a valid email address";
    } else if (trimmedEmail.length > 255) {
      newErrors.email = "Email must be less than 255 characters";
    }

    // Password validation
    if (!trimmedPassword) {
      newErrors.password = "Password is required";
    } else if (trimmedPassword.length < 8) {
      newErrors.password = "Password must be at least 8 characters long";
    } else if (trimmedPassword.length > 128) {
      newErrors.password = "Password must be less than 128 characters";
    }

    // Confirm password validation
    if (!trimmedConfirmPassword) {
      newErrors.confirm_password = "Please confirm your password";
    } else if (trimmedPassword !== trimmedConfirmPassword) {
      newErrors.confirm_password = "Passwords do not match";
    }

    // Bio validation
    if (trimmedBio && trimmedBio.length > 500) {
      newErrors.bio = "Bio must be less than 500 characters";
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
      email: form.email.trim(),
      password: form.password.trim(),
      confirm_password: form.confirm_password.trim(),
      bio: form.bio.trim(),
      private: form.private,
    };

    try {
      const res = await fetch(`${API_BASE}/api/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(trimmedForm),
      });
      const data = await res.json();

      if (res.ok) {
        setMessage(data.message || "Account created successfully!");
        setIsError(false);
        setForm({
          username: "",
          email: "",
          password: "",
          confirm_password: "",
          bio: "",
          private: false,
        });
      } else {
        setMessage(data.message || "Error creating account.");
        setIsError(true);
      }
    } catch (error) {
      setMessage("An error occurred. Please try again.");
      setIsError(true);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-6 rounded-2xl shadow-md w-96 space-y-4"
      >
        <h2 className="text-xl font-bold text-center">Create Account</h2>

        {message && (
          <div
            className={`text-center p-2 rounded ${
              isError ? "text-red-600" : "text-green-600"
            }`}
          >
            {message}
          </div>
        )}

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
            required
            maxLength={50}
          />
          {errors.username && <p className="text-red-500 text-sm mt-1">{errors.username}</p>}
        </div>

        <div>
          <input
            type="email"
            placeholder="Email"
            className={`border p-2 w-full rounded ${errors.email ? 'border-red-500' : ''}`}
            value={form.email}
            onChange={(e) => {
              setForm({ ...form, email: e.target.value });
              if (errors.email) {
                setErrors({ ...errors, email: '' });
              }
            }}
            onBlur={validateForm}
            required
            maxLength={255}
          />
          {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
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
              if (errors.confirm_password && e.target.value === form.confirm_password) {
                setErrors({ ...errors, confirm_password: '' });
              }
            }}
            onBlur={validateForm}
            required
            maxLength={128}
          />
          {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
        </div>

        <div>
          <input
            type="password"
            placeholder="Confirm Password"
            className={`border p-2 w-full rounded ${errors.confirm_password ? 'border-red-500' : ''}`}
            value={form.confirm_password}
            onChange={(e) => {
              setForm({ ...form, confirm_password: e.target.value });
              if (errors.confirm_password) {
                setErrors({ ...errors, confirm_password: '' });
              }
            }}
            onBlur={validateForm}
            required
            maxLength={128}
          />
          {errors.confirm_password && <p className="text-red-500 text-sm mt-1">{errors.confirm_password}</p>}
        </div>

        {/* Bio textarea */}
        <div>
          <textarea
            placeholder="Write your bio..."
            className={`border p-2 w-full rounded h-20 resize-none ${errors.bio ? 'border-red-500' : ''}`}
            value={form.bio}
            onChange={(e) => {
              const newBio = e.target.value;
              if (newBio.length <= 500) {
                setForm({ ...form, bio: newBio });
                if (errors.bio) {
                  setErrors({ ...errors, bio: '' });
                }
              }
            }}
            onBlur={validateForm}
            maxLength={500}
          ></textarea>
          <div className="flex justify-between items-center mt-1">
            {errors.bio && <p className="text-red-500 text-sm">{errors.bio}</p>}
            <p className={`text-xs ml-auto ${form.bio.length > 450 ? 'text-orange-500' : 'text-gray-400'}`}>
              {form.bio.length}/500 characters
            </p>
          </div>
        </div>

        {/* Private Account checkbox */}
        <label className="flex items-center space-x-2 text-sm">
          <input
            type="checkbox"
            checked={form.private}
            onChange={(e) => setForm({ ...form, private: e.target.checked })}
          />
          <span>Private Account</span>
        </label>

        <button
          type="submit"
          className="bg-blue-600 text-white p-2 rounded w-full hover:bg-blue-700"
        >
          Create Account
        </button>
        {/* 👇 Login link */}
        <p className="text-sm text-center text-gray-600">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-600 hover:underline">
            Login
          </Link>
        </p>
      </form>
    </div>
  );
}
