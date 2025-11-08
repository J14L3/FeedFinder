import React, { useState } from 'react';
import { Search, UserPlus, User, Mail, Lock, FileText, Eye, EyeOff } from 'lucide-react';
import { API_BASE } from './config';

const RegisterPage = ({ setShowLoginModal, setIsLoggedIn }) => {
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
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage("");

    // Validate passwords match
    if (form.password !== form.confirm_password) {
      setMessage("Passwords do not match!");
      setIsError(true);
      setIsLoading(false);
      return;
    }

    try {
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
        // Switch to login page after a short delay
        setTimeout(() => {
          setShowLoginModal(true);
          setMessage("");
        }, 1500);
      } else {
        setMessage(data.message || "Error creating account. Please try again.");
        setIsError(true);
      }
    } catch (error) {
      setMessage("An error occurred. Please try again.");
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  };

  const switchToLogin = () => {
    setShowLoginModal(true);
    setMessage("");
    setForm({
      username: "",
      email: "",
      password: "",
      confirm_password: "",
      bio: "",
      private: false,
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4 py-8">
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg mb-4">
            <Search size={40} className="text-white" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            FeedFinder
          </h1>
          <p className="text-gray-600">Create your account to get started</p>
        </div>

        {/* Register Card */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Create Account</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {message && (
              <div
                className={`p-4 rounded-xl text-sm font-medium ${
                  isError 
                    ? "bg-red-50 text-red-700 border border-red-200" 
                    : "bg-green-50 text-green-700 border border-green-200"
                }`}
              >
                {message}
              </div>
            )}

            {/* Username Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User size={20} className="text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Choose a username"
                  className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Email Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail size={20} className="text-gray-400" />
                </div>
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock size={20} className="text-gray-400" />
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Create a password"
                  className="w-full pl-10 pr-12 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff size={20} className="text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye size={20} className="text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
            </div>

            {/* Confirm Password Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock size={20} className="text-gray-400" />
                </div>
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Confirm your password"
                  className="w-full pl-10 pr-12 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white"
                  value={form.confirm_password}
                  onChange={(e) =>
                    setForm({ ...form, confirm_password: e.target.value })
                  }
                  required
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showConfirmPassword ? (
                    <EyeOff size={20} className="text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye size={20} className="text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
            </div>

            {/* Bio Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bio <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <div className="relative">
                <div className="absolute top-3 left-3 pointer-events-none">
                  <FileText size={20} className="text-gray-400" />
                </div>
                <textarea
                  placeholder="Tell us about yourself..."
                  className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white resize-none h-24"
                  value={form.bio}
                  onChange={(e) => setForm({ ...form, bio: e.target.value })}
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Private Account Checkbox */}
            <label className="flex items-center space-x-3 p-3 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={form.private}
                onChange={(e) => setForm({ ...form, private: e.target.checked })}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                disabled={isLoading}
              />
              <span className="text-sm text-gray-700">Make my account private</span>
            </label>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2 mt-2"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Creating account...</span>
                </>
              ) : (
                <>
                  <UserPlus size={20} />
                  <span>Create Account</span>
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-center text-sm text-gray-600">
              Already have an account?{" "}
              <button
                onClick={switchToLogin}
                className="font-semibold text-blue-600 hover:text-blue-700 hover:underline transition-colors"
              >
                Sign in
              </button>
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-500 mt-6">
          © 2024 FeedFinder. All rights reserved.
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;

