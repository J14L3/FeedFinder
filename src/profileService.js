/**
 * Profile Service
 * Handles fetching profile data from the backend API
 */

import { authenticatedFetch } from './authService';
import { API_BASE } from './config';

/**
 * Fetch user profile by user_id
 */
export async function fetchProfile(userId) {
  if (!userId) {
    console.error('fetchProfile: userId is required');
    return null;
  }

  try {
    console.log('fetchProfile: Fetching profile for userId:', userId);
    const response = await authenticatedFetch(`${API_BASE}/api/profile/${userId}`, {
      method: 'GET',
    });

    console.log('fetchProfile: Response status:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('fetchProfile: Profile data received:', data ? 'Success' : 'Null');
      return data;
    } else if (response.status === 404) {
      console.log('fetchProfile: Profile not found (404)');
      return null;
    }
    
    const errorText = await response.text().catch(() => 'Unknown error');
    console.error('fetchProfile: Error response:', response.status, errorText);
    throw new Error(`Failed to fetch profile: ${response.status}`);
  } catch (error) {
    console.error('fetchProfile: Exception caught:', error);
    return null;
  }
}

/**
 * Fetch current user's profile
 */
export async function fetchCurrentUserProfile() {
  try {
    // Get current user from session
    const { verifySession } = await import('./authService');
    const user = await verifySession();
    
    if (!user || !user.id) {
      return null;
    }

    const response = await authenticatedFetch(`${API_BASE}/api/profile/${user.id}`, {
      method: 'GET',
    });

    if (response.ok) {
      const data = await response.json();
      return data;
    }
    return null;
  } catch (error) {
    console.error('Error fetching current user profile:', error);
    return null;
  }
}

/**
 * Fetch user's posts for profile page
 * The backend endpoint uses optional_auth, so viewerId is determined from the session token
 */
export async function fetchUserPosts(userId, viewerId = null) {
  try {
    const url = `${API_BASE}/api/posts/user/${userId}`;

    const response = await authenticatedFetch(url, {
      method: 'GET',
    });

    if (response.ok) {
      const data = await response.json();
      return Array.isArray(data) ? data : [];
    }
    return [];
  } catch (error) {
    console.error('Error fetching user posts:', error);
    return [];
  }
}

/**
 * Fetch profile statistics (fallback method if stats endpoint is not available)
 */
export async function fetchProfileStats(userId, userEmail = null) {
  try {
    // Try to use the stats endpoint first
    const statsResponse = await authenticatedFetch(`${API_BASE}/api/profile/${userId}/stats`, {
      method: 'GET',
    });
    
    if (statsResponse.ok) {
      const data = await statsResponse.json();
      if (data.stats) {
        return data.stats;
      }
    }
  } catch (err) {
    console.error('Error fetching stats from endpoint:', err);
  }

  // Fallback: calculate basic stats
  try {
    let stats = {
      totalPosts: 0,
      totalLikes: 0,
      totalComments: 0,
      totalRatings: 0,
      averageRating: 0,
      followers: 0,
      following: 0
    };

    // Get posts count
    const posts = await fetchUserPosts(userId);
    stats.totalPosts = posts.length;

    // Get rating stats if email is provided
    if (userEmail) {
      try {
        const ratingResponse = await authenticatedFetch(`${API_BASE}/api/rating/${encodeURIComponent(userEmail)}`, {
          method: 'GET',
        });
        if (ratingResponse.ok) {
          const ratingData = await ratingResponse.json();
          if (ratingData.average) {
            // Convert from 1-10 scale to 1-5 scale
            stats.averageRating = (parseFloat(ratingData.average) / 2.0).toFixed(1);
            stats.totalRatings = ratingData.count || 0;
          }
        }
      } catch (err) {
        console.error('Error fetching ratings:', err);
      }
    }

    // Get following count
    try {
      const friendsResponse = await authenticatedFetch(`${API_BASE}/api/friends/${userId}`, {
        method: 'GET',
      });
      if (friendsResponse.ok) {
        const friends = await friendsResponse.json();
        stats.following = Array.isArray(friends) ? friends.length : 0;
      }
    } catch (err) {
      console.error('Error fetching friends:', err);
    }

    return stats;
  } catch (error) {
    console.error('Error fetching profile stats:', error);
    return {
      totalPosts: 0,
      totalLikes: 0,
      totalComments: 0,
      totalRatings: 0,
      averageRating: 0,
      followers: 0,
      following: 0
    };
  }
}

/**
 * Update user profile
 */
export async function updateProfile(profileData) {
  try {
    const response = await authenticatedFetch(`${API_BASE}/api/profile/update`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profileData),
    });

    if (response.ok) {
      const data = await response.json();
      return { success: true, data };
    }
    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: errorData.message || errorData.error || 'Failed to update profile' };
  } catch (error) {
    console.error('Error updating profile:', error);
    return { success: false, error: 'An error occurred while updating profile' };
  }
}

