import React, { useState } from 'react';
import { API_BASE } from './config';
import { X, Star } from 'lucide-react';

const RatingModal = ({ post, setShowRatingModal, currentUserId }) => {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  const getRatingText = (rating) => {
    return rating === 5 ? 'Excellent!' : rating === 4 ? 'Great!' : rating === 3 ? 'Good' : rating === 2 ? 'Fair' : rating === 1 ? 'Needs Improvement' : 'Poor';
  };

  const handleSubmit = async () => {
    if (!currentUserId) {
      alert('Please log in to rate.');
      return;
    }
    if (!post?.author?.email) {
      alert('Error, unable to identify profile.');
      return;
    }
    if (rating === 0) return;

    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUserId,
          target_email: post.author.email,
          rating_value: rating
        })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.message || 'Failed to submit rating');

      alert('You have submitted a rating');
      setShowRatingModal(null);
    } catch (err) {
      console.error(err);
      alert(err.message || 'Could not submit rating.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fadeIn" onClick={() => setShowRatingModal(null)}>
      <div className="bg-white rounded-2xl w-full max-w-md animate-slideUp" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Rate Profile</h2>
            <button onClick={() => setShowRatingModal(null)} className="p-2 hover:bg-gray-100 rounded-full">
              <X size={24} />
            </button>
          </div>

          <div className="flex items-center gap-3 mb-6 p-4 bg-gray-50 rounded-xl">
            <img src={post.author.avatar} alt={post.author.name} className="w-12 h-12 rounded-full" />
            <div>
              <p className="font-semibold">{post.author.name}</p>
              <div className="flex items-center gap-1">
              </div>
            </div>
          </div>

          <div className="mb-6 text-center">
            <label className="block text-sm font-medium mb-3">Your Rating</label>
            <div className="flex justify-center gap-2 mb-4">
              {[1, 2, 3, 4, 5].map(star => (
                <button key={star}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                  onClick={() => setRating(star)}
                  className="transition-transform hover:scale-110"
                >
                  <Star size={40} className={star <= (hoverRating || rating) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'} />
                </button>
              ))}
            </div>
            {rating > 0 && <p className="text-lg font-semibold text-gray-700">{getRatingText(rating)}</p>}
          </div>
          <button
            onClick={handleSubmit}
            disabled={submitting || rating === 0}
            className="w-full bg-yellow-400 text-gray-900 font-semibold py-4 rounded-xl hover:bg-yellow-500 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <span className="w-4 h-4 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Star size={20} /> Submit Rating
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RatingModal;
