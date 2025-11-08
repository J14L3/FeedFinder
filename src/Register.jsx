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

  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await fetch(`${API_BASE}/api/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
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

        <input
          type="text"
          placeholder="Username"
          className="border p-2 w-full rounded"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />

        <input
          type="email"
          placeholder="Email"
          className="border p-2 w-full rounded"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />

        <input
          type="password"
          placeholder="Password"
          className="border p-2 w-full rounded"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />

        <input
          type="password"
          placeholder="Confirm Password"
          className="border p-2 w-full rounded"
          value={form.confirm_password}
          onChange={(e) =>
            setForm({ ...form, confirm_password: e.target.value })
          }
          required
        />

        {/* Bio textarea */}
        <textarea
          placeholder="Write your bio..."
          className="border p-2 w-full rounded h-20 resize-none"
          value={form.bio}
          onChange={(e) => setForm({ ...form, bio: e.target.value })}
        ></textarea>

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
