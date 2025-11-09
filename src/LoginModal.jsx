import React, { useState, useEffect } from 'react';
import { Search, LogIn, User, Lock } from 'lucide-react';
import { login } from './authService';

const LoginPage = ({ setShowRegisterModal, setIsLoggedIn }) => {
  const [form, setForm] = useState({ username: "", password: "" });
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Fetch CSRF token on component mount
    import('./authService').then(({ fetchCSRFToken }) => {
      fetchCSRFToken();
    });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage("");
    
    try {
      const { success, data } = await login(form.username, form.password);
      
      if (success) {
        setMessage(data.message || "Login successful!");
        setIsError(false);
        // Set logged in after a short delay
        setTimeout(() => {
          setIsLoggedIn(true);
          setForm({ username: "", password: "" });
          setMessage("");
        }, 1000);
      } else {
        setMessage(data.message || "Login failed. Please check your credentials and try again.");
        setIsError(true);
      }
    } catch (error) {
      setMessage("An error occurred. Please try again.");
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  };

  const switchToRegister = () => {
    setShowRegisterModal(true);
    setMessage("");
    setForm({ username: "", password: "" });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg mb-4">
            <Search size={40} className="text-white" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            FeedFinder
          </h1>
          <p className="text-gray-600">Welcome back! Please sign in to continue</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Sign In</h2>

          <form onSubmit={handleSubmit} className="space-y-5">
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
                  placeholder="Enter your username"
                  className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
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
                  type="password"
                  placeholder="Enter your password"
                  className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <LogIn size={20} />
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          {/* Register Link */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-center text-sm text-gray-600">
              Don't have an account?{" "}
              <button
                onClick={switchToRegister}
                className="font-semibold text-blue-600 hover:text-blue-700 hover:underline transition-colors"
              >
                Create one now
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

export default LoginPage;

