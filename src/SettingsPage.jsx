import React, { useState, useEffect } from 'react';
import { Settings, Mail, User, Save, CheckCircle, AlertCircle } from 'lucide-react';
import { fetchCurrentUserProfile, updateProfile } from './profileService';
import { verifySession } from './authService';

const SettingsPage = () => {
  const [email, setEmail] = useState('');
  const [bio, setBio] = useState('');
  const [profilePicture, setProfilePicture] = useState('https://api.dicebear.com/7.x/avataaars/svg?seed=User');
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null); // 'success' or 'error'
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  // Predefined profile picture options
  const profilePictureOptions = [
    'https://api.dicebear.com/7.x/avataaars/svg?seed=User',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=Alex',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=Emma',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=David',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=Lisa',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=John',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=Anna',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=Tom',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=Maria',
    'https://api.dicebear.com/7.x/avataaars/svg?seed=Chris'
  ];

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
          setProfilePicture(profile.profile_picture || 'https://api.dicebear.com/7.x/avataaars/svg?seed=User');
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

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSave = async () => {
    // Validate email
    if (!email.trim()) {
      setSaveStatus('error');
      setErrorMessage('Email is required.');
      return;
    }

    if (!validateEmail(email)) {
      setSaveStatus('error');
      setErrorMessage('Please enter a valid email address.');
      return;
    }

    setIsSaving(true);
    setSaveStatus(null);
    setErrorMessage('');

    try {
      // Prepare update data (only send fields that have changed)
      const updateData = {
        user_email: email.trim(),
        bio: bio.trim(),
        profile_picture: profilePicture
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

        {/* Profile Picture Section */}
        <div className="mb-8 pb-8 border-b border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-4">
            Profile Picture
          </label>
          <div className="flex items-start gap-6 mb-6">
            <div className="relative">
              <img
                src={profilePicture}
                alt="Profile"
                className="w-24 h-24 rounded-full object-cover border-4 border-blue-500"
              />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-600 mb-2">Current profile picture</p>
              <p className="text-xs text-gray-500">
                Select a new profile picture from the options below
              </p>
            </div>
          </div>
          
          {/* Profile Picture Selection Grid */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-3">Choose a profile picture:</p>
            <div className="grid grid-cols-4 sm:grid-cols-6 gap-4">
              {profilePictureOptions.map((avatar, index) => (
                <button
                  key={index}
                  onClick={() => setProfilePicture(avatar)}
                  className={`relative w-16 h-16 rounded-full overflow-hidden border-2 transition-all hover:scale-110 ${
                    profilePicture === avatar
                      ? 'border-blue-500 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <img
                    src={avatar}
                    alt={`Avatar ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                  {profilePicture === avatar && (
                    <div className="absolute inset-0 bg-blue-500 bg-opacity-20 flex items-center justify-center">
                      <CheckCircle size={20} className="text-blue-600" />
                    </div>
                  )}
                </button>
              ))}
            </div>
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
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email address"
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>
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
              onChange={(e) => setBio(e.target.value)}
              placeholder="Tell us about yourself..."
              rows={5}
              maxLength={500}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
            />
          </div>
          <div className="flex items-center justify-between mt-2">
            <p className="text-xs text-gray-500">
              Share a brief description about yourself with other users.
            </p>
            <p className="text-xs text-gray-400">
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
                <li>Profile picture and bio are visible to other users</li>
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

