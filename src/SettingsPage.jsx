import React, { useState, useEffect } from 'react';
import { Settings, Mail, User, Save, CheckCircle, AlertCircle, Lock, Unlock } from 'lucide-react';
import { fetchCurrentUserProfile, updateProfile } from './profileService';
import { verifySession } from './authService';

const SettingsPage = () => {
  const [email, setEmail] = useState('');
  const [bio, setBio] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null); // 'success' or 'error'
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch current user profile on mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        setIsLoading(true);
        setErrorMessage('');
        const profile = await fetchCurrentUserProfile();
        
        if (profile) {
          setEmail(profile.user_email || '');
          setBio(profile.bio || '');
          setIsPrivate(profile.is_private === 1 || profile.is_private === true);
        } else {
          // Check if user is authenticated
          const user = await verifySession();
          if (!user) {
            setErrorMessage('Please log in to view your settings');
          } else {
            setErrorMessage('Failed to load profile data');
          }
        }
      } catch (error) {
        console.error('Error loading profile:', error);
        setErrorMessage('Failed to load profile data');
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, []);

  const [fieldErrors, setFieldErrors] = useState({});

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = () => {
    const newErrors = {};
    const trimmedEmail = email.trim();
    const trimmedBio = bio.trim();

    // Email validation
    if (!trimmedEmail) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(trimmedEmail)) {
      newErrors.email = 'Please enter a valid email address';
    } else if (trimmedEmail.length > 255) {
      newErrors.email = 'Email must be less than 255 characters';
    }

    // Bio validation
    if (trimmedBio.length > 500) {
      newErrors.bio = 'Bio must be less than 500 characters';
    }

    setFieldErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    setFieldErrors({});
    setSaveStatus(null);
    setErrorMessage('');

    if (!validateForm()) {
      setSaveStatus('error');
      setErrorMessage('Please fix the errors before saving.');
      return;
    }

    setIsSaving(true);

    try {
      // Prepare update data (only send fields that have changed)
      const updateData = {
        user_email: email.trim(),
        bio: bio.trim(),
        is_private: isPrivate
      };

      const result = await updateProfile(updateData);

      if (result.success) {
        setSaveStatus('success');
        // Clear success message after 3 seconds
        setTimeout(() => {
          setSaveStatus(null);
        }, 3000);
      } else {
        setSaveStatus('error');
        setErrorMessage(result.error || 'Failed to save settings. Please try again.');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaveStatus('error');
      setErrorMessage('An error occurred while saving settings. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="w-full">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 md:p-8">
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="ml-3 text-gray-600">Loading settings...</span>
          </div>
        </div>
      </div>
    );
  }

  if (errorMessage && !email) {
    return (
      <div className="w-full">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 md:p-8">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Settings size={32} className="text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
            </div>
          </div>
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle size={20} className="text-red-600 flex-shrink-0" />
            <p className="text-sm text-red-800">{errorMessage}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 md:p-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Settings size={32} className="text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          </div>
          <p className="text-gray-600">Manage your account information and preferences</p>
        </div>

        {/* Privacy Section */}
        <div className="mb-8 pb-8 border-b border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-4">
            Privacy Settings
          </label>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center gap-3">
              {isPrivate ? (
                <Lock size={20} className="text-gray-600" />
              ) : (
                <Unlock size={20} className="text-gray-600" />
              )}
              <div>
                <p className="text-sm font-medium text-gray-900">Private Profile</p>
                <p className="text-xs text-gray-500">
                  {isPrivate 
                    ? 'Your profile is private. Only approved followers can see your posts.'
                    : 'Your profile is public. Anyone can see your posts.'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsPrivate(!isPrivate)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                isPrivate ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isPrivate ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Email Section */}
        <div className="mb-8 pb-8 border-b border-gray-200">
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
            Email Address
          </label>
          <div className="relative">
            <Mail size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (fieldErrors.email) {
                  setFieldErrors({ ...fieldErrors, email: '' });
                }
              }}
              onBlur={validateForm}
              placeholder="Enter your email address"
              className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none ${
                fieldErrors.email ? 'border-red-500' : 'border-gray-300'
              }`}
              maxLength={255}
            />
          </div>
          {fieldErrors.email && (
            <p className="text-red-500 text-sm mt-1">{fieldErrors.email}</p>
          )}
          <p className="text-xs text-gray-500 mt-2">
            We'll use this email to send you important updates and notifications.
          </p>
        </div>

        {/* Bio Section */}
        <div className="mb-8">
          <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-2">
            Bio <span className="text-gray-400">(optional)</span>
          </label>
          <div className="relative">
            <User size={20} className="absolute left-3 top-3 text-gray-400" />
            <textarea
              id="bio"
              value={bio}
              onChange={(e) => {
                const newBio = e.target.value;
                if (newBio.length <= 500) {
                  setBio(newBio);
                  if (fieldErrors.bio) {
                    setFieldErrors({ ...fieldErrors, bio: '' });
                  }
                }
              }}
              onBlur={validateForm}
              placeholder="Tell us about yourself..."
              rows={5}
              maxLength={500}
              className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none ${
                fieldErrors.bio ? 'border-red-500' : 'border-gray-300'
              }`}
            />
          </div>
          <div className="flex items-center justify-between mt-2">
            {fieldErrors.bio ? (
              <p className="text-red-500 text-sm">{fieldErrors.bio}</p>
            ) : (
              <p className="text-xs text-gray-500">
                Share a brief description about yourself with other users.
              </p>
            )}
            <p className={`text-xs ml-auto ${bio.length > 450 ? 'text-orange-500' : 'text-gray-400'}`}>
              {bio.length}/500 characters
            </p>
          </div>
        </div>

        {/* Save Status */}
        {saveStatus === 'success' && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
            <CheckCircle size={20} className="text-green-600 flex-shrink-0" />
            <p className="text-sm text-green-800">Settings saved successfully!</p>
          </div>
        )}

        {saveStatus === 'error' && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle size={20} className="text-red-600 flex-shrink-0" />
            <p className="text-sm text-red-800">{errorMessage || 'Failed to save settings. Please try again.'}</p>
          </div>
        )}

        {/* Save Button */}
        <div className="flex gap-4">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex-1 bg-blue-500 text-white font-semibold py-4 rounded-xl hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSaving ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Saving...
              </>
            ) : (
              <>
                <Save size={20} />
                Save Changes
              </>
            )}
          </button>
        </div>

        {/* Info Box */}
        <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Privacy & Security</p>
              <ul className="list-disc list-inside space-y-1 text-blue-700">
                <li>Your email will be kept private and secure</li>
                <li>Bio is visible to other users</li>
                <li>Private profiles restrict who can see your posts</li>
                <li>You can update your information at any time</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;

