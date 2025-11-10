import React, { useEffect, useState } from 'react';
import { Star, DollarSign, Lock, Crown, FileText } from 'lucide-react';
import { API_BASE } from './config';

const isRelativeOrTrusted = (url) =>
  /^(https?:\/\/|blob:|\/|\.\/)/i.test(url || "");

// images only
export const isSafeImageUrl = (url = "") =>
  isRelativeOrTrusted(url) &&
  /\.(png|jpe?g|gif|webp|avif)$/i.test(new URL(url, window.location.origin).pathname);

// videos only
export const isSafeVideoUrl = (url = "") =>
  isRelativeOrTrusted(url) &&
  /\.(mp4|webm|mov|ogg)$/i.test(new URL(url, window.location.origin).pathname);

const PostCards = ({ post, setShowRatingModal, isLoggedIn = false, isPremium = false, onAuthorClick, currentUserId }) => {
  const [avgRating, setAvgRating] = useState(null);
  const [ratingCount, setRatingCount] = useState(null);
  //checks if is own post
  const isOwnPost = Boolean(currentUserId) && (
    post?.author?.id === currentUserId || post?.author?.user_id === currentUserId
  );

  useEffect(() => {
    let mounted = true;
    const email = post?.author?.email || post?.user_email;
    if (!email) return;

    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/rating/${encodeURIComponent(email)}`);
        const data = await res.json().catch(() => ({}));
        if (!mounted) return;
        if (res.ok && data?.average != null) {
          setAvgRating(Number(data.average));
          setRatingCount(Number(data.count || 0));
        } else {
          setAvgRating(null);
          setRatingCount(null);
        }
      } catch {
        if (mounted) {
          setAvgRating(null);
          setRatingCount(null);
        }
      }
    })();

    return () => { mounted = false; };
  }, [post?.author?.email, post?.user_email]);

  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition mb-8 border-2 border-gray-200">
      {/* Author Header */}
      <div className="p-4 flex items-center justify-between">
        <div
          className={`flex items-center gap-3 ${onAuthorClick ? 'cursor-pointer hover:opacity-80 transition' : ''}`}
          onClick={onAuthorClick}
        >
          <div className="relative">
            <img
              src={post.author.avatar}
              alt={post.author.name}
              className="w-12 h-12 rounded-full"
              loading="lazy"
              decoding="async"
              referrerPolicy="no-referrer"
              crossOrigin="anonymous"
            />
            {post.author.isPremium && (
              <div className="absolute -bottom-1 -right-1 bg-gradient-to-r from-yellow-400 to-orange-400 rounded-full p-1">
                <Crown size={12} className="text-white" />
              </div>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <p className="font-semibold">{post.author.name}</p>
              {post.author.verified && (
                <div className="bg-blue-500 rounded-full p-0.5">
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </div>
            <div className="flex items-center gap-1 text-sm">
              <span className="text-gray-500">{post.author.username}</span>
              <span className="text-gray-300">•</span>
              <div className="flex items-center gap-1">
                <Star size={14} className="fill-yellow-400 text-yellow-400" />
                <span className="font-medium">
                  {avgRating != null ? avgRating.toFixed(2) : '—'}
                </span>
                {ratingCount ? <span className="text-gray-400 ml-1">({ratingCount})</span> : null}
              </div>
            </div>
          </div>
        </div>
        <span className="text-sm text-gray-500">{post.timestamp}</span>
      </div>

      {/* Content */}
      {post.type === 'image' && !post.isExclusive && (
        isSafeImageUrl(post.content) ? (
          <img
            src={post.content}
            alt="Post image"
            className="w-full aspect-square object-cover"
            loading="lazy"
            decoding="async"
            referrerPolicy="no-referrer"
            crossOrigin="anonymous"
          />
        ) : (
          <div className="w-full aspect-square bg-gray-100 flex items-center justify-center text-gray-500">
            Image unavailable
          </div>
        )
      )}
      {post.type === 'video' && !post.isExclusive && (
        <div className="relative w-full aspect-square bg-gray-900">
          {isSafeVideoUrl(post.content) ? (
            <video
              src={post.content}
              controls
              playsInline
              preload="metadata"
              className="w-full h-full object-contain bg-black"
            />
          ) : (
            <div className="w-full h-full bg-gray-800 flex items-center justify-center text-gray-400">
              Video unavailable
            </div>
          )}
        </div>
      )}
      {post.type === 'text' && (
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-8">
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center gap-2 mb-4">
              <FileText size={24} className="text-blue-600" />
              <span className="font-semibold text-gray-700">Text Post</span>
            </div>
          </div>
        </div>
      )}

      {/* Caption & Actions */}
      <div className="p-4">
        <p className="text-gray-800 mb-3">{post.caption}</p>
        <div className="flex items-center justify-end pt-3 border-t border-gray-100">
          <div className="flex items-center gap-2">
             {isLoggedIn && !isOwnPost && (
              <button
                onClick={() => setShowRatingModal(post)}
                className="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 rounded-full font-medium transition flex items-center gap-1"
              >
                <Star size={16} /> Rate
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PostCards;
