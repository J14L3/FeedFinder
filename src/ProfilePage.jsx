import React, { useState, useEffect } from 'react';
import { 
  Star, Crown, MapPin, Calendar, Edit2, Camera, Heart, 
  MessageCircle, Share2, Grid, List, Settings, DollarSign,
  Users, Award, TrendingUp
} from 'lucide-react';
import PostCards from './PostCards';
import RatingModal from './RatingModal';
import { fetchProfile, fetchUserPosts, fetchProfileStats, updateProfile } from './profileService';
import { authenticatedFetch } from './authService';
import { API_BASE } from './config';

const ProfilePage = ({ 
  userId = null,
  isOwnProfile = false,
  isLoggedIn = false,
  isPremium = false,
  currentUserId: propCurrentUserId = null,
  setShowRatingModal,
  onBack
}) => {
  const [activeView, setActiveView] = useState('posts'); // posts, about, stats
  const [isEditing, setIsEditing] = useState(false);
  const [editBio, setEditBio] = useState('');
  const [userProfile, setUserProfile] = useState(null);
  const [userPosts, setUserPosts] = useState([]);
  const [stats, setStats] = useState({
    totalPosts: 0,
    totalLikes: 0,
    totalComments: 0,
    totalRatings: 0,
    averageRating: 0,
    totalDonations: 0,
    followers: 0,
    following: 0,
    monthlyDonations: 0,
    topDonation: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(propCurrentUserId);

  // Get current user ID if not provided as prop
  useEffect(() => {
    if (propCurrentUserId) {
      setCurrentUserId(propCurrentUserId);
      return;
    }
    
    const getCurrentUserId = async () => {
      try {
        const { verifySession } = await import('./authService');
        const user = await verifySession();
        if (user && user.id) {
          setCurrentUserId(user.id);
        }
      } catch (err) {
        console.error('Error getting current user:', err);
      }
    };
    getCurrentUserId();
  }, [propCurrentUserId]);

  // Fetch profile data from database
  useEffect(() => {
    const loadProfileData = async () => {
      if (!userId) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      // Add timeout to prevent infinite loading
      const timeoutId = setTimeout(() => {
        setError('Request timed out. Please try again.');
        setLoading(false);
      }, 15000); // 15 second timeout

      try {
        // Fetch profile
        const profileData = await fetchProfile(userId);

        if (profileData) {
          setUserProfile(profileData);
          setEditBio(profileData.bio || '');

          // Fetch profile statistics and posts in parallel with timeout
          const statsPromise = (async () => {
            try {
              const statsResponse = await authenticatedFetch(`${API_BASE}/api/profile/${userId}/stats`, {
                method: 'GET',
              });
              if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                if (statsData.stats) {
                  return statsData.stats;
                }
              }
              // Fallback to basic stats
              return await fetchProfileStats(userId, profileData.user_email);
            } catch (err) {
              console.error('Error fetching stats:', err);
              // Fallback to basic stats
              return await fetchProfileStats(userId, profileData.user_email);
            }
          })();

          // Fetch posts - currentUserId is used by backend to determine if viewing own posts
          // If currentUserId is null, backend will only return public posts
          const postsPromise = fetchUserPosts(userId, currentUserId);
          console.log('ProfilePage: Fetching posts with userId:', userId, 'currentUserId:', currentUserId);

          // Use Promise.race with timeout to prevent hanging
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Request timeout')), 10000)
          );

          const [statsResult, posts] = await Promise.all([
            Promise.race([statsPromise, timeoutPromise]).catch(() => {
              // Return default stats on timeout
              return {
                totalPosts: 0,
                totalLikes: 0,
                totalComments: 0,
                totalRatings: 0,
                averageRating: 0,
                followers: 0,
                following: 0
              };
            }),
            Promise.race([postsPromise, timeoutPromise]).catch((err) => {
              console.error('Error fetching posts (timeout or error):', err);
              return [];
            })
          ]);

          clearTimeout(timeoutId);

          console.log('ProfilePage: Posts received:', posts);
          console.log('ProfilePage: Posts count:', Array.isArray(posts) ? posts.length : 'Not an array');

          // Set stats
          setStats(statsResult);

          // Transform posts to match PostCards format
          const transformedPosts = Array.isArray(posts) ? posts.map(post => ({
            id: post.post_id,
            author: {
              user_id: userId,
              name: profileData.user_name,
              username: `@${profileData.user_name}`,
              avatar: profileData.profile_picture || `https://api.dicebear.com/7.x/avataaars/svg?seed=${profileData.user_name}`,
              rating: parseFloat(statsResult.averageRating) || 0,
              verified: false,
              isPremium: profileData.is_premium || false
            },
            type: post.media_url ? (post.media_url.match(/\.(mp4|webm|mov)$/i) ? 'video' : 'image') : 'text',
            content: post.media_url || '',
            caption: post.content_text || '',
            timestamp: post.created_at ? formatTimestamp(post.created_at) : 'Just now',
            likes: post.like_count || 0,
            comments: 0,
            isExclusive: post.privacy === 'exclusive'
          })) : [];
          
          console.log('ProfilePage: Transformed posts count:', transformedPosts.length);
          setUserPosts(transformedPosts);
        } else {
          clearTimeout(timeoutId);
          setError('Profile not found');
        }
      } catch (err) {
        clearTimeout(timeoutId);
        console.error('Error loading profile:', err);
        setError(err.message || 'Failed to load profile. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      loadProfileData();
    } else {
      setLoading(false);
    }
  }, [userId, currentUserId]);

  // Format timestamp helper
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Just now';
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const handleSaveBio = async () => {
    if (isOwnProfile && userProfile?.user_id) {
      const result = await updateProfile({
        user_id: userProfile.user_id,
        user_name: userProfile.user_name,
        bio: editBio,
        profile_picture: userProfile.profile_picture,
        is_private: userProfile.is_private
      });
      if (result.success) {
        setUserProfile(prev => ({ ...prev, bio: editBio }));
        setIsEditing(false);
      } else {
        alert(result.error || 'Failed to update bio');
      }
    } else {
      setIsEditing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error || !userProfile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg mb-4">{error || 'Profile not found'}</p>
          {onBack && (
            <button
              onClick={onBack}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
            >
              Go Back
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Profile Header with Banner */}
      <div className="relative">
        {/* Banner */}
        <div className="h-48 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 relative overflow-hidden">
          <div className="absolute inset-0 bg-black bg-opacity-10"></div>
          {isOwnProfile && (
            <button
              onClick={() => {/* Open banner upload */}}
              className="absolute top-4 right-4 p-2 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition shadow-lg"
            >
              <Camera size={20} className="text-gray-700" />
            </button>
          )}
        </div>

        {/* Profile Info Section */}
        <div className="relative -mt-20 px-4 pb-6">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-6 border-2 border-gray-100">
              <div className="flex flex-col md:flex-row gap-6">
                {/* Avatar */}
                <div className="relative -mt-20 md:-mt-24">
                  <div className="relative">
                    <img
                      src={userProfile.profile_picture || `https://api.dicebear.com/7.x/avataaars/svg?seed=${userProfile.user_name}`}
                      alt={userProfile.user_name}
                      className="w-32 h-32 md:w-40 md:h-40 rounded-full border-4 border-white shadow-xl object-cover"
                      loading="lazy"
                      decoding="async"
                      referrerPolicy="no-referrer"
                      crossOrigin="anonymous"
                      onError={(e) => {
                        e.target.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${userProfile.user_name}`;
                      }}
                    />
                    {isPremium && (
                      <div className="absolute -bottom-2 -right-2 bg-gradient-to-r from-yellow-400 to-orange-400 rounded-full p-2 shadow-lg">
                        <Crown size={24} className="text-white" />
                      </div>
                    )}
                    {isOwnProfile && (
                      <button
                        onClick={() => {/* Open avatar upload */}}
                        className="absolute bottom-0 right-0 p-2 bg-blue-500 rounded-full shadow-lg hover:bg-blue-600 transition"
                      >
                        <Camera size={16} className="text-white" />
                      </button>
                    )}
                  </div>
                </div>

                {/* User Info */}
                <div className="flex-1 mt-4 md:mt-0">
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h1 className="text-3xl font-bold text-gray-900">{userProfile.user_name}</h1>
                        {isPremium && (
                          <span className="px-3 py-1 bg-gradient-to-r from-yellow-400 to-orange-400 text-white text-sm font-semibold rounded-full flex items-center gap-1">
                            <Crown size={14} />
                            Premium
                          </span>
                        )}
                      </div>
                      <p className="text-gray-500 mt-1">@{userProfile.user_name}</p>
                      
                      {/* Rating */}
                      <div className="flex items-center gap-2 mt-2">
                        <div className="flex items-center gap-1">
                          <Star size={18} className="fill-yellow-400 text-yellow-400" />
                          <span className="font-bold text-lg">{stats.averageRating > 0 ? stats.averageRating : 'N/A'}</span>
                        </div>
                        <span className="text-gray-400">•</span>
                        <span className="text-sm text-gray-600">{stats.totalRatings || 0} ratings</span>
                      </div>

                      {/* Bio */}
                      <div className="mt-4">
                        {isEditing && isOwnProfile ? (
                          <div className="space-y-2">
                            <textarea
                              value={editBio}
                              onChange={(e) => setEditBio(e.target.value)}
                              rows={3}
                              className="w-full px-4 py-2 border-2 border-blue-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                              placeholder="Tell us about yourself..."
                            />
                            <div className="flex gap-2">
                              <button
                                onClick={handleSaveBio}
                                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-medium"
                              >
                                Save
                              </button>
                              <button
                                onClick={() => {
                                  setEditBio(userProfile.bio || '');
                                  setIsEditing(false);
                                }}
                                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-start justify-between gap-4">
                            <p className="text-gray-700 leading-relaxed">
                              {userProfile.bio || 'No bio yet. Tell us about yourself!'}
                            </p>
                            {isOwnProfile && (
                              <button
                                onClick={() => setIsEditing(true)}
                                className="p-2 hover:bg-gray-100 rounded-full transition"
                              >
                                <Edit2 size={18} className="text-gray-600" />
                              </button>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Join Date */}
                      <div className="flex items-center gap-4 mt-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <Calendar size={16} />
                          <span>Joined {userProfile.user_email ? 'recently' : 'recently'}</span>
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                      {isOwnProfile ? (
                        <button
                          onClick={() => {/* Navigate to settings */}}
                          className="px-6 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full font-medium transition flex items-center gap-2"
                        >
                          <Settings size={18} />
                          Edit Profile
                        </button>
                      ) : (
                        <>
                          <button
                            onClick={() => setShowRatingModal({ author: userProfile })}
                            className="px-6 py-2.5 bg-yellow-400 hover:bg-yellow-500 text-gray-900 rounded-full font-medium transition flex items-center gap-2"
                          >
                            <Star size={18} />
                            Rate
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Stats Bar */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{stats.totalPosts}</div>
                  <div className="text-sm text-gray-600">Posts</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{stats.followers}</div>
                  <div className="text-sm text-gray-600">Followers</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{stats.totalLikes}</div>
                  <div className="text-sm text-gray-600">Likes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{stats.following}</div>
                  <div className="text-sm text-gray-600">Following</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content Tabs */}
      <div className="max-w-4xl mx-auto px-4 mt-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1 mb-6">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveView('posts')}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition ${
                activeView === 'posts'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <Grid size={18} />
                Posts ({userPosts.length})
              </div>
            </button>
            <button
              onClick={() => setActiveView('about')}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition ${
                activeView === 'about'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              About
            </button>
            <button
              onClick={() => setActiveView('stats')}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition ${
                activeView === 'stats'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <TrendingUp size={18} />
                Stats
              </div>
            </button>
          </div>
        </div>

        {/* Content based on active view */}
        {activeView === 'posts' && (
          <div>
            {userPosts.length === 0 ? (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-12 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Camera size={32} className="text-gray-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No posts yet</h3>
                <p className="text-gray-600 mb-6">Start sharing your content with the community!</p>
              </div>
            ) : (
              <div className="space-y-6">
                {userPosts.map(post => (
                  <PostCards
                    key={post.id}
                    post={post}
                    currentUserId={currentUserId} 
                    setShowRatingModal={setShowRatingModal}
                    isLoggedIn={isLoggedIn}
                    isPremium={isPremium}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {activeView === 'about' && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Users size={20} className="text-purple-500" />
                Social
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-xl">
                  <div className="text-3xl font-bold text-gray-900">{stats.followers}</div>
                  <div className="text-sm text-gray-600 mt-1">Followers</div>
                </div>
                <div className="p-4 bg-gray-50 rounded-xl">
                  <div className="text-3xl font-bold text-gray-900">{stats.following}</div>
                  <div className="text-sm text-gray-600 mt-1">Following</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === 'stats' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Engagement</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Total Likes</span>
                  <span className="font-bold text-gray-900">{stats.totalLikes}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Total Comments</span>
                  <span className="font-bold text-gray-900">{stats.totalComments}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Average Rating</span>
                  <span className="font-bold text-gray-900 flex items-center gap-1">
                    <Star size={16} className="fill-yellow-400 text-yellow-400" />
                    {stats.averageRating || 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
              <h3 className="text-lg font-semibold mb-4">Performance Overview</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-3xl font-bold">{stats.totalPosts}</div>
                  <div className="text-sm opacity-90 mt-1">Posts Created</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">{stats.totalRatings}</div>
                  <div className="text-sm opacity-90 mt-1">Ratings Received</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;

