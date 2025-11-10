import React, { useState, useEffect, useRef } from 'react';
import { Search, Home, PlusSquare, User, Star, Crown, Bell, LogOut, Settings, Shield } from 'lucide-react';
import { API_BASE } from './config'; 
import CreatePostModal from './CreatePostModal';
import RatingModal from './RatingModal';
import LoginPage from './LoginModal';
import RegisterPage from './RegisterModal';
import PostCards from './PostCards';
import UploadMedia from './UploadMedia';
import SettingsPage from './SettingsPage';
import PremiumUpgrade from './PremiumUpgrade';
import ProfilePage from './ProfilePage';
import AdminPage from './AdminPage';
import SearchResultsPage from './SearchResultsPage';

// Load all images in the folder dynamically (Vite)
const imageUrls = import.meta.glob('./assets/images/*.{png,jpg,jpeg,gif,webp,avif}', {
  eager: true,
  as: 'url'
});

// Map filename => url for easy lookup, e.g. imagesByName['yz.jpg']
const imagesByName = Object.fromEntries(
  Object.entries(imageUrls).map(([path, url]) => [path.split('/').pop(), url])
);

const inferMediaType = (url = "") => {
  const ext = url.split(".").pop()?.toLowerCase() || "";
  if (["mp4","mov","webm"].includes(ext)) return "video";
  return "image";
};

const FeedFinder = () => {
  const [activeTab, setActiveTab] = useState('home');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRatingModal, setShowRatingModal] = useState(null);
  const [showRegisterPage, setShowRegisterPage] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResultsQuery, setSearchResultsQuery] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isPremium, setIsPremium] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [posts, setPosts] = useState([]);
  const [loadingFeed, setLoadingFeed] = useState(true);
  const [feedError, setFeedError] = useState("");
  const [viewingProfile, setViewingProfile] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const userMenuRef = useRef(null);


  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { verifySession } = await import('./authService');
        const user = await verifySession();
        if (user) {
          setIsLoggedIn(true);
          if (user.id) {
            setCurrentUserId(user.id ?? user.user_id ?? null);
          }
          // Check both 'role' and 'user_role' fields, and handle empty strings
          const role = user.role || user.user_role;
          console.log('Auth check - user object:', user);
          console.log('Auth check - role:', role);
          if (role) {
            setUserRole(role);
            console.log('Auth check - setUserRole called with:', role);
          } else {
            console.warn('Auth check - No role found in user object');
            setUserRole(null);
          }
        }
      } catch (error) {
        console.error('Error checking authentication:', error);
      } finally {
        setIsCheckingAuth(false);
      }
    };
    checkAuth();
  }, []);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);

  // Fetch dynamic posts from backend
  useEffect(() => {
    if (!isCheckingAuth && isLoggedIn && activeTab === 'home') {
      const fetchPosts = async () => {
        setLoadingFeed(true);
        setFeedError("");
        try {
          const res = await fetch(`${API_BASE}/api/posts/public`);
          const data = await res.json();

          if (!res.ok || !data?.success) {
            throw new Error(data?.message || 'Failed to load posts');
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
           const mapped = data.items.map(p => ({
             id: p.post_id,
             author: {
               user_id: p.user_id,
               name: p.user_name || 'User',
               username: p.user_email ? `@${p.user_email.split('@')[0]}` : `@${p.user_name || 'user'}`,
               avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + (p.user_name || 'User'),
               rating: 0,
               verified: false,
               isPremium: false,
               email : p.user_email
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
          console.error(err);
          setFeedError(err.message || 'Could not fetch posts');
        } finally {
          setLoadingFeed(false);
        }
      };

      fetchPosts();
    }
  }, [isCheckingAuth, isLoggedIn, activeTab]);

  const filteredPosts = posts.filter(post =>
    post.author.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.author.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.caption.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Show loading state while checking authentication
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show login/register page if not logged in
  if (!isLoggedIn) {
    if (showRegisterPage) {
      return (
        <RegisterPage
          setShowLoginModal={() => setShowRegisterPage(false)}
          setIsLoggedIn={setIsLoggedIn}
        />
      );
    }
    return (
      <LoginPage
        setShowRegisterModal={() => setShowRegisterPage(true)}
        setIsLoggedIn={setIsLoggedIn}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between gap-4">
            {/* Logo */}
            <button
              onClick={() => {
                if (activeTab === 'home') {
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                  setActiveTab('home');
                  setSearchQuery('');
                  setTimeout(() => {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }, 100);
                }
              }}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Search size={20} className="text-white" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent hidden sm:block">
                FeedFinder
              </h1>
            </button>

            {/* Search Bar */}
            <div className="flex-1 max-w-2xl mx-4">
              <div className="relative">
                <Search size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 z-10" />
                <input
                  type="text"
                  placeholder="Search profiles, posts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && searchQuery.trim()) {
                      // Basic sanitization: remove HTML tags and limit length
                      const sanitized = searchQuery.trim()
                        .replace(/<[^>]*>/g, '')  // Remove HTML tags to prevent XSS
                        .substring(0, 200);       // Limit length
                      
                      if (sanitized) {
                        setSearchResultsQuery(sanitized);
                        setActiveTab('search');
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }
                    }
                  }}
                  className="w-full pl-10 pr-4 py-2.5 bg-white border-2 border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm hover:shadow-md transition-all"
                />
              </div>
            </div>

            {/* Right Side Actions */}
            <div className="flex items-center gap-2">
              <button className="p-2 hover:bg-gray-100 rounded-full relative">
                <Bell size={22} className="text-gray-700" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={async () => {
                    // Refresh user role when opening menu to ensure it's up-to-date
                    if (!showUserMenu) {
                      try {
                        const { verifySession } = await import('./authService');
                        const user = await verifySession();
                        if (user) {
                          const role = user.role || user.user_role;
                          if (role) {
                            setUserRole(role);
                            console.log('Menu open - refreshed role:', role);
                          }
                        }
                      } catch (error) {
                        console.error('Error refreshing role:', error);
                      }
                    }
                    setShowUserMenu(!showUserMenu);
                  }}
                  className="flex items-center gap-2 p-1.5 hover:bg-gray-100 rounded-full transition-all border-2 border-gray-200 hover:border-blue-500 shadow-sm hover:shadow-md"
                >
                  <img
                    src="https://api.dicebear.com/7.x/avataaars/svg?seed=User"
                    alt="User"
                    className="w-9 h-9 rounded-full ring-2 ring-white"
                  />
                  {isPremium && (
                    <Crown size={18} className="text-yellow-500" />
                  )}
                </button>
                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-[100] animate-slideUp">
                    <button
                      onClick={() => {
                        setActiveTab('upload');
                        setShowUserMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-gray-900"
                    >
                      <PlusSquare size={18} />
                      Create
                    </button>
                     <button 
                       onClick={() => {
                         setViewingProfile(null);
                         setActiveTab('profile');
                         setShowUserMenu(false);
                       }}
                       className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-gray-900"
                     >
                       <User size={18} />
                       Profile
                     </button>
                    <button
                      onClick={() => {
                        setActiveTab('settings');
                        setShowUserMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-gray-900"
                    >
                      <Settings size={18} />
                      Settings
                    </button>
                    {(() => {
                      const isAdmin = userRole && String(userRole).toLowerCase() === 'admin';
                      console.log('Admin panel render check:', {
                        userRole,
                        isAdmin,
                        userRoleType: typeof userRole
                      });
                      return isAdmin;
                    })() && (
                      <button
                        onClick={() => {
                          setActiveTab('admin');
                          setShowUserMenu(false);
                        }}
                        className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-red-600"
                      >
                        <Shield size={18} />
                        Admin Panel
                      </button>
                    )}
                    {/* {!isPremium && (
                      <button
                        onClick={() => {
                          setActiveTab('premium');
                          setShowUserMenu(false);
                        }}
                        className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-yellow-600"
                      >
                        <Crown size={18} />
                        Upgrade to Premium
                      </button>
                    )} */}
                    <hr className="my-2" />
                    <button
                      onClick={async () => {
                        try {
                          const { logout } = await import('./authService');
                          const success = await logout();
                          if (success) {
                            setIsLoggedIn(false);
                            setShowUserMenu(false);
                          }
                        } catch (error) {
                          console.error('Error logging out:', error);
                          // Still logout locally even if API call fails
                          setIsLoggedIn(false);
                          setShowUserMenu(false);
                        }
                      }}
                      className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-red-600"
                    >
                      <LogOut size={18} />
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Premium Banner */}
      {!isPremium && (
        <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-4 py-2">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Crown size={20} />
              <span className="text-sm font-medium">RATE YOUR FAVOURITE CREATORS!</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-4 py-6">
        {activeTab === 'upload' ? (
          <UploadMedia />
        ) : activeTab === 'settings' ? (
          <SettingsPage />
        ) : activeTab === 'premium' ? (
          <PremiumUpgrade setIsPremium={setIsPremium} setActiveTab={setActiveTab} />
        ) : activeTab === 'admin' ? (
          <AdminPage 
            onBack={() => {
              setActiveTab('home');
            }}
          />
        ) : activeTab === 'search' ? (
          <SearchResultsPage
            searchQuery={searchResultsQuery}
            onBack={() => {
              setActiveTab('home');
              setSearchQuery('');
              setSearchResultsQuery('');
            }}
            isLoggedIn={isLoggedIn}
            isPremium={isPremium}
            currentUserId={currentUserId}
            setShowRatingModal={setShowRatingModal}
            onAuthorClick={(author) => {
              if (author?.user_id) {
                setViewingProfile({ user_id: author.user_id });
                setActiveTab('profile');
              }
            }}
          />
          ) : activeTab === 'profile' ? (
           viewingProfile?.user_id || currentUserId ? (
             <ProfilePage
               userId={viewingProfile?.user_id || currentUserId}
               isOwnProfile={!viewingProfile || viewingProfile.user_id === currentUserId}
               isLoggedIn={isLoggedIn}
               isPremium={isPremium}
               currentUserId={currentUserId}
               setShowRatingModal={setShowRatingModal}
               onBack={() => {
                 setViewingProfile(null);
                 setActiveTab('home');
               }}
             />
           ) : (
             <div className="text-center py-12">
               <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
               <p className="text-gray-600">Loading profile...</p>
             </div>
           )
          ) : (
          <>    
            {
              loadingFeed ? (
                <div className="text-center py-12">
                  <div className="w-10 h-10 border-4 border-gray-300 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading posts...</p>
                </div>
              ) : feedError ? (
                <div className="text-center py-12 text-red-600">
                  {feedError}
                </div>
              ) : filteredPosts.length === 0 ? (
                <div className="text-center py-12">
                  <Search size={48} className="mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-600">No public posts available</p>
                </div>
              ) : (
                 filteredPosts.map(post => (
                   <PostCards
                     key={post.id}
                     post={post}
                     setShowRatingModal={setShowRatingModal}
                     currentUserId={currentUserId} 
                     isLoggedIn={isLoggedIn}
                     isPremium={isPremium}
                     onAuthorClick={() => {
                       if (post.author?.user_id) {
                         setViewingProfile({ user_id: post.author.user_id });
                         setActiveTab('profile');
                       }
                     }}
                   />
                 ))
               )
             }
           </>
          )}
        </main>

      {/* Bottom Navigation Bar */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-md border-t-2 border-gray-300 shadow-2xl z-30">
        <div className="flex items-center justify-around py-3 max-w-7xl mx-auto">
          <button
            onClick={() => {
              if (activeTab === 'home') {
                window.scrollTo({ top: 0, behavior: 'smooth' });
              } else {
                setActiveTab('home');
                setTimeout(() => {
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }, 100);
              }
            }}
            className={`flex flex-col items-center gap-1 p-2 ${activeTab === 'home' ? 'text-blue-600' : 'text-gray-600'}`}
          >
            <Home size={24} />
            <span className="text-xs">Home</span>
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex flex-col items-center gap-1 p-2 ${activeTab === 'upload' ? 'text-blue-600' : 'text-gray-600'}`}
          >
            <PlusSquare size={24} />
            <span className="text-xs">Create</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('search');
              // If no search query, focus the search input after a short delay
              if (!searchResultsQuery) {
                setTimeout(() => {
                  const searchInput = document.querySelector('input[placeholder="Search profiles, posts..."]');
                  if (searchInput) {
                    searchInput.focus();
                  }
                }, 100);
              }
            }}
            className={`flex flex-col items-center gap-1 p-2 ${activeTab === 'search' ? 'text-blue-600' : 'text-gray-600'}`}
          >
            <Search size={24} />
            <span className="text-xs">Search</span>
          </button>
          <button
            onClick={() => {
              setViewingProfile(null);
              setActiveTab('profile');
            }}
            className={`flex flex-col items-center gap-1 p-2 ${activeTab === 'profile' ? 'text-blue-600' : 'text-gray-600'}`}
          >
            <User size={24} />
            <span className="text-xs">Profile</span>
          </button>
        </div>
      </nav>

      {/* Modals */}
      {showCreateModal && <CreatePostModal setShowCreateModal={setShowCreateModal} />}
      {showRatingModal && <RatingModal post={showRatingModal} setShowRatingModal={setShowRatingModal} currentUserId={currentUserId}/>}
    </div>
  );
};

export default FeedFinder;
