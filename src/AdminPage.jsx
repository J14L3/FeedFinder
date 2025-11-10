import React, { useState, useEffect } from 'react';
import { Trash2, Shield, AlertCircle } from 'lucide-react';
import { API_BASE } from './config';
import { authenticatedFetch } from './authService';

const inferMediaType = (url = "") => {
  const ext = url.split(".").pop()?.toLowerCase() || "";
  if (["mp4","mov","webm"].includes(ext)) return "video";
  return "image";
};

const isSafeImageUrl = (url = "") =>
  /^(https?:\/\/|blob:|\/|\.\/)/i.test(url || "") &&
  /\.(png|jpe?g|gif|webp|avif)$/i.test(new URL(url, window.location.origin).pathname);

const isSafeVideoUrl = (url = "") =>
  /^(https?:\/\/|blob:|\/|\.\/)/i.test(url || "") &&
  /\.(mp4|webm|mov|ogg)$/i.test(new URL(url, window.location.origin).pathname);

const AdminPage = ({ onBack }) => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState({});
  const [userRole, setUserRole] = useState(null);

  // Check if user is admin
  useEffect(() => {
    const checkAdmin = async () => {
      try {
        const { verifySession } = await import('./authService');
        const user = await verifySession();
        if (user && user.role === 'admin') {
          setUserRole('admin');
        } else {
          setUserRole('not_admin');
          setError('Access denied. Admin privileges required.');
        }
      } catch (err) {
        console.error('Error checking admin status:', err);
        setUserRole('not_admin');
        setError('Error verifying admin status.');
      }
    };
    checkAdmin();
  }, []);

  // Fetch all posts
  useEffect(() => {
    if (userRole === 'admin') {
      fetchPosts();
    }
  }, [userRole]);

  const fetchPosts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await authenticatedFetch(`${API_BASE}/api/admin/posts?limit=100`, {
        method: 'GET',
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.message || 'Failed to fetch posts');
      }

      const data = await response.json();
      if (data.success && data.posts) {
        // Format timestamp
        const formatTimestamp = (timestamp) => {
          if (!timestamp) return 'Unknown';
          const date = new Date(timestamp);
          return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          });
        };

        const formattedPosts = data.posts.map(post => ({
          ...post,
          formattedDate: formatTimestamp(post.created_at),
          mediaType: post.media_type || (post.media_url ? inferMediaType(post.media_url) : null)
        }));

        setPosts(formattedPosts);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      console.error('Error fetching posts:', err);
      setError(err.message || 'Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (postId) => {
    if (!window.confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
      return;
    }

    setDeleting(prev => ({ ...prev, [postId]: true }));

    try {
      const response = await authenticatedFetch(`${API_BASE}/api/admin/posts/${postId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.message || 'Failed to delete post');
      }

      // Remove post from list
      setPosts(prev => prev.filter(post => post.post_id !== postId));
    } catch (err) {
      console.error('Error deleting post:', err);
      alert(`Failed to delete post: ${err.message}`);
    } finally {
      setDeleting(prev => {
        const newState = { ...prev };
        delete newState[postId];
        return newState;
      });
    }
  };

  // Show access denied if not admin
  if (userRole === 'not_admin') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle size={32} className="text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-6">{error || 'Admin privileges required to access this page.'}</p>
          <button
            onClick={() => {
              if (onBack) {
                onBack();
              }
            }}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Show loading state
  if (loading || userRole === null) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading admin panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-orange-600 rounded-xl flex items-center justify-center">
                <Shield size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
                <p className="text-sm text-gray-500">Manage all posts</p>
              </div>
            </div>
            <div className="text-sm text-gray-600">
              {posts.length} {posts.length === 1 ? 'post' : 'posts'}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertCircle size={20} className="text-red-600" />
            <p className="text-red-800">{error}</p>
            <button
              onClick={fetchPosts}
              className="ml-auto px-4 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {posts.length === 0 && !loading ? (
          <div className="text-center py-12 bg-white rounded-2xl shadow-sm">
            <Shield size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">No posts found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {posts.map((post) => (
              <div
                key={post.post_id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition"
              >
                <div className="p-4">
                  {/* Post Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-gray-900">{post.user_name}</span>
                        <span className="text-sm text-gray-500">({post.user_email})</span>
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                          {post.privacy}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">Post ID: {post.post_id} • {post.formattedDate}</p>
                    </div>
                    <button
                      onClick={() => handleDelete(post.post_id)}
                      disabled={deleting[post.post_id]}
                      className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Delete post"
                    >
                      {deleting[post.post_id] ? (
                        <div className="w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <Trash2 size={18} />
                      )}
                    </button>
                  </div>

                  {/* Post Content */}
                  {post.content_text && (
                    <p className="text-gray-800 mb-3 whitespace-pre-wrap">{post.content_text}</p>
                  )}

                  {/* Media */}
                  {post.media_url && (
                    <div className="mb-3">
                      {post.mediaType === 'image' && isSafeImageUrl(post.media_url) ? (
                        <img
                          src={post.media_url.startsWith('/') ? `${API_BASE}${post.media_url}` : post.media_url}
                          alt="Post media"
                          className="max-w-full max-h-64 rounded-lg object-contain bg-gray-100"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      ) : post.mediaType === 'video' && isSafeVideoUrl(post.media_url) ? (
                        <video
                          src={post.media_url.startsWith('/') ? `${API_BASE}${post.media_url}` : post.media_url}
                          controls
                          className="max-w-full max-h-64 rounded-lg bg-gray-900"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      ) : (
                        <div className="p-4 bg-gray-100 rounded-lg text-center text-gray-500">
                          <p className="text-sm">Media: {post.media_url}</p>
                          <p className="text-xs mt-1">(Preview not available)</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminPage;

