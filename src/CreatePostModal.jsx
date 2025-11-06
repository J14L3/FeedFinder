import React, { useState } from 'react';
import { X, Camera, Video, FileText, Upload, Lock } from 'lucide-react';

const CreatePostModal = ({ setShowCreateModal }) => {
  const [contentType, setContentType] = useState('image');
  const [isExclusive, setIsExclusive] = useState(false);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fadeIn" onClick={() => setShowCreateModal(false)}>
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-auto animate-slideUp" onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <h2 className="text-xl font-bold">Create Post</h2>
          <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-gray-100 rounded-full">
            <X size={24} />
          </button>
        </div>

        <div className="p-6">
          <div className="flex gap-2 mb-6">
            {['image', 'video', 'text'].map(type => (
              <button
                key={type}
                onClick={() => setContentType(type)}
                className={`flex-1 py-3 rounded-lg font-medium transition flex items-center justify-center gap-2 ${
                  contentType === type ? 'bg-blue-500 text-white' : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                {type === 'image' && <Camera size={20} />}
                {type === 'video' && <Video size={20} />}
                {type === 'text' && <FileText size={20} />}
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>

          {(contentType === 'image' || contentType === 'video') && (
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center mb-6 hover:border-blue-500 transition cursor-pointer">
              <Upload size={48} className="mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600 mb-2">Click to upload {contentType === 'image' ? 'images' : 'video'}</p>
              <p className="text-sm text-gray-400">or drag and drop</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Caption</label>
              <textarea 
                rows={4}
                placeholder="Share your story..."
                maxLength={500}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-amber-50 rounded-lg border border-amber-200">
              <div className="flex items-center gap-3">
                <Lock size={20} className="text-amber-600" />
                <div>
                  <p className="font-medium text-gray-900">Exclusive Content</p>
                  <p className="text-sm text-gray-600">Only visible to premium supporters</p>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={isExclusive}
                  onChange={(e) => setIsExclusive(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
              </label>
            </div>

            <button className="w-full bg-blue-500 text-white font-semibold py-4 rounded-xl hover:bg-blue-600 transition">
              Publish Post
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreatePostModal;
