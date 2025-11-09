import React, { useState, useEffect } from 'react';
import { Search, UserPlus, User, Mail, Lock, FileText, Eye, EyeOff } from 'lucide-react';
import { register } from './authService';

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
  const [errors, setErrors] = useState({});

  useEffect(() => {
    // Fetch CSRF token on component mount
    import('./authService').then(({ fetchCSRFToken }) => {
      fetchCSRFToken();
    });
  }, []);

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password) => {
    // At least 8 characters, can contain letters, numbers, and special characters
    if (password.length < 8) {
      return "Password must be at least 8 characters long";
    }
    if (password.length > 128) {
      return "Password must be less than 128 characters";
    }
    return null;
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
    const passwordError = validatePassword(trimmedPassword);
    if (!trimmedPassword) {
      newErrors.password = "Password is required";
    } else if (passwordError) {
      newErrors.password = passwordError;
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
    setIsLoading(true);
    setMessage("");
    setErrors({});

    if (!validateForm()) {
      setIsLoading(false);
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
      const { success, data } = await register(trimmedForm);

      if (success) {
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
        // Automatically log in after registration
        setTimeout(() => {
          setIsLoggedIn(true);
          setShowLoginModal(false);
          setMessage("");
        }, 1000);
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
                  className={`w-full pl-10 pr-4 py-3 border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white ${
                    errors.username ? 'border-red-500' : 'border-gray-200'
                  }`}
                  value={form.username}
                  onChange={(e) => {
                    setForm({ ...form, username: e.target.value });
                    if (errors.username) {
                      setErrors({ ...errors, username: '' });
                    }
                  }}
                  onBlur={validateForm}
                  required
                  disabled={isLoading}
                  maxLength={50}
                />
              </div>
              {errors.username && <p className="text-red-500 text-sm mt-1">{errors.username}</p>}
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
                  className={`w-full pl-10 pr-4 py-3 border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white ${
                    errors.email ? 'border-red-500' : 'border-gray-200'
                  }`}
                  value={form.email}
                  onChange={(e) => {
                    setForm({ ...form, email: e.target.value });
                    if (errors.email) {
                      setErrors({ ...errors, email: '' });
                    }
                  }}
                  onBlur={validateForm}
                  required
                  disabled={isLoading}
                  maxLength={255}
                />
              </div>
              {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
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
                  className={`w-full pl-10 pr-12 py-3 border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white ${
                    errors.password ? 'border-red-500' : 'border-gray-200'
                  }`}
                  value={form.password}
                  onChange={(e) => {
                    setForm({ ...form, password: e.target.value });
                    if (errors.password) {
                      setErrors({ ...errors, password: '' });
                    }
                    // Clear confirm password error if passwords now match
                    if (errors.confirm_password && e.target.value === form.confirm_password) {
                      setErrors({ ...errors, confirm_password: '' });
                    }
                  }}
                  onBlur={validateForm}
                  required
                  disabled={isLoading}
                  maxLength={128}
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
              {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
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
                  className={`w-full pl-10 pr-12 py-3 border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white ${
                    errors.confirm_password ? 'border-red-500' : 'border-gray-200'
                  }`}
                  value={form.confirm_password}
                  onChange={(e) => {
                    setForm({ ...form, confirm_password: e.target.value });
                    if (errors.confirm_password) {
                      setErrors({ ...errors, confirm_password: '' });
                    }
                  }}
                  onBlur={validateForm}
                  required
                  disabled={isLoading}
                  maxLength={128}
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
              {errors.confirm_password && <p className="text-red-500 text-sm mt-1">{errors.confirm_password}</p>}
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
                  className={`w-full pl-10 pr-4 py-3 border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-gray-50 focus:bg-white resize-none h-24 ${
                    errors.bio ? 'border-red-500' : 'border-gray-200'
                  }`}
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
                  disabled={isLoading}
                  maxLength={500}
                />
              </div>
              <div className="flex justify-between items-center mt-1">
                {errors.bio && <p className="text-red-500 text-sm">{errors.bio}</p>}
                <p className={`text-xs ml-auto ${form.bio.length > 450 ? 'text-orange-500' : 'text-gray-400'}`}>
                  {form.bio.length}/500 characters
                </p>
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

