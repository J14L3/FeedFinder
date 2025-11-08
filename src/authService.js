/**
 * Authentication Service
 * Handles CSRF tokens, authentication state, and API requests with credentials
 */

const API_BASE = import.meta.env.VITE_API_BASE || '';

let csrfToken = null;

/**
 * Fetch CSRF token from server
 */
export async function fetchCSRFToken() {
  try {
    const response = await fetch(`${API_BASE}/api/csrf-token`, {
      method: 'GET',
      credentials: 'include', // Include cookies
    });
    
    if (response.ok) {
      const data = await response.json();
      csrfToken = data.csrf_token;
      return csrfToken;
    }
    return null;
  } catch (error) {
    console.error('Error fetching CSRF token:', error);
    return null;
  }
}

/**
 * Get current CSRF token (fetch if not available)
 */
export async function getCSRFToken() {
  if (!csrfToken) {
    await fetchCSRFToken();
  }
  return csrfToken;
}

/**
 * Make authenticated API request
 */
export async function authenticatedFetch(url, options = {}) {
  // Ensure CSRF token is available
  const token = await getCSRFToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  // Add CSRF token to headers
  if (token) {
    headers['X-CSRF-Token'] = token;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Include cookies for authentication
  });
  
  // If token expired, try to refresh
  if (response.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      // Retry the request
      return fetch(url, {
        ...options,
        headers,
        credentials: 'include',
      });
    }
  }
  
  return response;
}

/**
 * Refresh access token
 */
export async function refreshToken() {
  try {
    const response = await fetch(`${API_BASE}/api/refresh`, {
      method: 'POST',
      credentials: 'include',
    });
    
    if (response.ok) {
      return true;
    }
    return false;
  } catch (error) {
    console.error('Error refreshing token:', error);
    return false;
  }
}

/**
 * Verify current session
 */
export async function verifySession() {
  try {
    const response = await authenticatedFetch(`${API_BASE}/api/verify-session`, {
      method: 'GET',
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.user;
    }
    return null;
  } catch (error) {
    console.error('Error verifying session:', error);
    return null;
  }
}

/**
 * Logout
 */
export async function logout() {
  try {
    const response = await authenticatedFetch(`${API_BASE}/api/logout`, {
      method: 'POST',
    });
    
    // Clear CSRF token
    csrfToken = null;
    
    return response.ok;
  } catch (error) {
    console.error('Error logging out:', error);
    return false;
  }
}

/**
 * Login
 */
export async function login(username, password) {
  try {
    const token = await getCSRFToken();
    
    const response = await fetch(`${API_BASE}/api/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token || '',
      },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });
    
    const data = await response.json();
    return { success: response.ok, data };
  } catch (error) {
    console.error('Error logging in:', error);
    return { success: false, data: { message: 'An error occurred during login' } };
  }
}

/**
 * Register
 */
export async function register(userData) {
  try {
    const token = await getCSRFToken();
    
    const response = await fetch(`${API_BASE}/api/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token || '',
      },
      credentials: 'include',
      body: JSON.stringify(userData),
    });
    
    const data = await response.json();
    return { success: response.ok, data };
  } catch (error) {
    console.error('Error registering:', error);
    return { success: false, data: { message: 'An error occurred during registration' } };
  }
}

