import React, { useState, useEffect, useRef } from 'react';
import { Search, Home, PlusSquare, User, Star, Crown, Bell, LogIn, LogOut, Settings } from 'lucide-react';
import CreatePostModal from './CreatePostModal';
import DonateModal from './DonateModal';
import RatingModal from './RatingModal';
import PostCards from './PostCards';
import UploadMedia from './UploadMedia';
import SettingsPage from './SettingsPage';
import PremiumUpgrade from './PremiumUpgrade';

// Load all images in the folder dynamically (Vite)
const imageUrls = import.meta.glob('./assets/images/*.{png,jpg,jpeg,gif,webp,avif}', {
  eager: true,
  as: 'url'
});

// Map filename => url for easy lookup, e.g. imagesByName['yz.jpg']
const imagesByName = Object.fromEntries(
  Object.entries(imageUrls).map(([path, url]) => [path.split('/').pop(), url])
);

const FeedFinder = () => {
  const [activeTab, setActiveTab] = useState('home');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDonateModal, setShowDonateModal] = useState(null);
  const [showRatingModal, setShowRatingModal] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isPremium, setIsPremium] = useState(false);
  const userMenuRef = useRef(null);

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

  // Sample posts data
  const posts = [
    {
      id: 1,
      author: {
        name: 'Lee Yong Zhang',
        username: '@lyz',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah',
        rating: 4.8,
        verified: true,
        isPremium: true
      },
      type: 'image',
      content: imagesByName['yz.jpg'] || '',
      caption: 'Look at my tattoo! Hit me up if you want some! 💙',
      timestamp: '2h ago',
      likes: 1247,
      comments: 89,
      isExclusive: false
    },
    {
      id: 2,
      author: {
        name: 'Mike Chen',
        username: '@mikechen',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike',
        rating: 4.5,
        verified: false,
        isPremium: false
      },
      type: 'video',
      content: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&h=800&fit=crop',
      caption: 'Behind the scenes of my latest video! Check out my exclusive content for more 🎬',
      timestamp: '5h ago',
      likes: 892,
      comments: 45,
      isExclusive: true
    },
    {
      id: 3,
      author: {
        name: 'Emma Williams',
        username: '@emmaw',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emma',
        rating: 4.9,
        verified: true,
        isPremium: true
      },
      type: 'image',
      content: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&h=800&fit=crop',
      caption: 'Feeling grateful for all the support! Your donations help me create better content 🙏',
      timestamp: '8h ago',
      likes: 2103,
      comments: 156,
      isExclusive: false
    },
    {
      id: 4,
      author: {
        name: 'David Martinez',
        username: '@davidm',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=David',
        rating: 4.2,
        verified: false,
        isPremium: false
      },
      type: 'text',
      content: '',
      caption: 'Just want to share my thoughts on building meaningful connections in the digital age. Sometimes the best conversations happen when we take the time to truly understand each other. What are your thoughts?',
      timestamp: '12h ago',
      likes: 456,
      comments: 78,
      isExclusive: false
    },
    {
      id: 5,
      author: {
        name: 'Lisa Anderson',
        username: '@lisaa',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Lisa',
        rating: 4.7,
        verified: true,
        isPremium: true
      },
      type: 'image',
      content: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=800&h=800&fit=crop',
      caption: 'New exclusive content dropping this week! Premium members get early access ✨',
      timestamp: '1d ago',
      likes: 1789,
      comments: 234,
      isExclusive: true
    }
  ];

  const filteredPosts = posts.filter(post => 
    post.author.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.author.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.caption.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
                  className="w-full pl-10 pr-4 py-2.5 bg-white border-2 border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm hover:shadow-md transition-all"
                />
              </div>
            </div>

            {/* Right Side Actions */}
            <div className="flex items-center gap-2">
              {isLoggedIn ? (
                <>
                  <button className="p-2 hover:bg-gray-100 rounded-full relative">
                    <Bell size={22} className="text-gray-700" />
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                  </button>
                  <div className="relative" ref={userMenuRef}>
                    <button
                      onClick={() => setShowUserMenu(!showUserMenu)}
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
                        <button className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-gray-900">
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
                        {!isPremium && (
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
                        )}
                        <hr className="my-2" />
                        <button
                          onClick={() => setIsLoggedIn(false)}
                          className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2 text-red-600"
                        >
                          <LogOut size={18} />
                          Logout
                        </button>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <button
                  onClick={() => setIsLoggedIn(true)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-full font-medium hover:bg-blue-600 transition flex items-center gap-2"
                >
                  <LogIn size={18} />
                  <span className="hidden sm:inline">Login</span>
                </button>
              )}
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
              <span className="text-sm font-medium">Upgrade to Premium for unlimited ratings and exclusive content!</span>
            </div>
            <button 
              onClick={() => setActiveTab('premium')}
              className="px-4 py-1 bg-white text-orange-600 rounded-full text-sm font-semibold hover:bg-gray-100 transition"
            >
              Learn More
            </button>
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
        ) : activeTab === 'search' ? (
          <div className="text-center py-12">
            <Search size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">Search functionality coming soon...</p>
          </div>
        ) : activeTab === 'profile' ? (
          <div className="text-center py-12">
            <User size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">Profile page coming soon...</p>
          </div>
        ) : (
          <>
            {filteredPosts.length === 0 ? (
              <div className="text-center py-12">
                <Search size={48} className="mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600">No posts found matching your search</p>
              </div>
            ) : (
              filteredPosts.map(post => (
                <PostCards
                  key={post.id}
                  post={post}
                  setShowDonateModal={setShowDonateModal}
                  setShowRatingModal={setShowRatingModal}
                  isLoggedIn={isLoggedIn}
                  isPremium={isPremium}
                />
              ))
            )}
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
            onClick={() => setActiveTab('search')}
            className={`flex flex-col items-center gap-1 p-2 ${activeTab === 'search' ? 'text-blue-600' : 'text-gray-600'}`}
          >
            <Search size={24} />
            <span className="text-xs">Search</span>
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            className={`flex flex-col items-center gap-1 p-2 ${activeTab === 'profile' ? 'text-blue-600' : 'text-gray-600'}`}
          >
            <User size={24} />
            <span className="text-xs">Profile</span>
          </button>
        </div>
      </nav>

      {/* Modals */}
      {showCreateModal && <CreatePostModal setShowCreateModal={setShowCreateModal} />}
      {showDonateModal && <DonateModal post={showDonateModal} setShowDonateModal={setShowDonateModal} />}
      {showRatingModal && <RatingModal post={showRatingModal} setShowRatingModal={setShowRatingModal} />}
    </div>
  );
};

export default FeedFinder;
