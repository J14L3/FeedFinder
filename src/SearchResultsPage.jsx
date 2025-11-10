import React, { useState, useEffect } from 'react';
import { Search, ArrowLeft } from 'lucide-react';
import { API_BASE } from './config';
import PostCards from './PostCards';

const inferMediaType = (url = "") => {
  const ext = url.split(".").pop()?.toLowerCase() || "";
  if (["mp4","mov","webm"].includes(ext)) return "video";
  return "image";
};

const SearchResultsPage = ({ searchQuery, onBack, isLoggedIn, isPremium, currentUserId, setShowRatingModal, onAuthorClick }) => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (searchQuery && searchQuery.trim()) {
      fetchSearchResults(searchQuery.trim());
    } else {
      setPosts([]);
      setLoading(false);
    }
  }, [searchQuery]);

  const fetchSearchResults = async (query) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/posts/search?q=${encodeURIComponent(query)}&limit=100`);
      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Failed to search posts');
      }

      // Helper function to format timestamp
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

      // Map backend rows into PostCards format
      const mapped = (data.items || []).map(p => ({
        id: p.post_id,
        author: {
          user_id: p.user_id,
          name: p.user_name || 'User',
          username: p.user_email ? `@${p.user_email.split('@')[0]}` : `@${p.user_name || 'user'}`,
          avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + (p.user_name || 'User'),
          rating: 0,
          verified: false,
          isPremium: false,
          email: p.user_email
        },
        type: p.media_type || (p.media_url ? inferMediaType(p.media_url) : 'image'),
        content: p.media_url || '',
        caption: p.content_text || '',
        timestamp: p.created_at ? formatTimestamp(p.created_at) : 'Just now',
        likes: 0,
        comments: 0,
        isExclusive: p.privacy === 'exclusive'
      }));

      setPosts(mapped);
    } catch (err) {
      console.error('Error searching posts:', err);
      setError(err.message || 'Could not search posts');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            {onBack && (
              <button
                onClick={onBack}
                className="p-2 hover:bg-gray-100 rounded-full transition"
                title="Go back"
              >
                <ArrowLeft size={20} className="text-gray-700" />
              </button>
            )}
            <div className="flex-1">
              <h1 className="text-xl font-bold text-gray-900">Search Results</h1>
              {searchQuery && (
                <p className="text-sm text-gray-500">
                  Results for: <span className="font-medium text-gray-700">"{searchQuery}"</span>
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-3xl mx-auto px-4 py-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="w-10 h-10 border-4 border-gray-300 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">Searching posts...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search size={32} className="text-red-600" />
            </div>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={() => searchQuery && fetchSearchResults(searchQuery)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Try Again
            </button>
          </div>
        ) : !searchQuery || !searchQuery.trim() ? (
          <div className="text-center py-12">
            <Search size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">Enter a search query to find posts</p>
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-12">
            <Search size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-2">No posts found</p>
            <p className="text-sm text-gray-500">
              Try searching with different keywords
            </p>
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-600">
              Found {posts.length} {posts.length === 1 ? 'post' : 'posts'}
            </div>
            {posts.map(post => (
              <PostCards
                key={post.id}
                post={post}
                setShowRatingModal={setShowRatingModal}
                isLoggedIn={isLoggedIn}
                isPremium={isPremium}
                onAuthorClick={onAuthorClick ? () => {
                  if (post.author?.user_id) {
                    onAuthorClick(post.author);
                  }
                } : undefined}
              />
            ))}
          </>
        )}
      </main>
    </div>
  );
};

export default SearchResultsPage;

