import React, { useState, useRef } from 'react';
import { Upload, X, Image, Video, File, CheckCircle, AlertCircle, Trash2 } from 'lucide-react';
import { API_BASE } from './config'; 

const UploadMedia = ({ currUserId }) => { // receive the current user ID from main page
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [postDescription, setPostDescription] = useState('');
  const fileInputRef = useRef(null);

  // Accepted file types
  const acceptedTypes = {
    image: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/avif'],
    video: ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime']
  };

  const allAcceptedTypes = [
    ...acceptedTypes.image,
    ...acceptedTypes.video
  ];

  const getFileType = (file) => {
    if (acceptedTypes.image.includes(file.type)) return 'image';
    if (acceptedTypes.video.includes(file.type)) return 'video';
    return 'other';
  };

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'image':
        return <Image size={24} className="text-blue-500" />;
      case 'video':
        return <Video size={24} className="text-purple-500" />;
      default:
        return <File size={24} className="text-gray-500" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleFileSelect = (files) => {
    const file = files[0]; // Only take the first file
    if (!file) return;

    if (!allAcceptedTypes.includes(file.type)) {
      alert(`${file.name} is not a supported file type.`);
      return;
    }
    if (file.size > 100 * 1024 * 1024) { // 100MB limit
      alert(`${file.name} is too large. Maximum file size is 100MB.`);
      return;
    }

    // Clear previous file preview if exists
    if (uploadedFile?.preview) {
      URL.revokeObjectURL(uploadedFile.preview);
    }

    const newFile = {
      id: Date.now(),
      file,
      name: file.name,
      size: file.size,
      type: getFileType(file),
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
      status: 'pending'
    };

    setUploadedFile(newFile);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files);
    }
  };

  const handleFileInputChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFileSelect(files);
    }
  };

  const removeFile = () => {
    if (uploadedFile?.preview) {
      URL.revokeObjectURL(uploadedFile.preview);
    }
    setUploadedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // const handleUpload = async () => {
  //   if (!uploadedFile && postDescription.trim().length === 0) {
  //     alert('Please add a file or a description to create a post.');
  //     return;
  //   }

  //   // Simulate upload process
  //   setUploadedFile(prev => {
  //     if (prev) {
  //       return { ...prev, status: 'uploading' };
  //     }
  //     return prev;
  //   });

  //   // Simulate API call
  //   setTimeout(() => {
  //     setUploadedFile(prev => {
  //       if (prev) {
  //         return { ...prev, status: 'success' };
  //       }
  //       return prev;
  //     });
  //     setTimeout(() => {
  //       alert('Post created successfully!');
  //       setUploadedFile(prev => {
  //         if (prev?.preview) {
  //           URL.revokeObjectURL(prev.preview);
  //         }
  //         return null;
  //       });
  //       setPostDescription('');
  //       if (fileInputRef.current) {
  //         fileInputRef.current.value = '';
  //       }
  //     }, 1000);
  //   }, 2000);
  // };

  const handleUpload = async () => {
    if (!uploadedFile && postDescription.trim().length === 0) {
      alert("Please add a file or a description to create a post.");
      return;
    }

    try {
      // upload media file
      let mediaUrl = "";
      if (uploadedFile) {
        const formData = new FormData();
        formData.append("file", uploadedFile.file);

        const uploadRes = await fetch(`${API_BASE}/api/upload`, {
          method: "POST",
          body: formData,
        });
        const uploadData = await uploadRes.json();

        if (!uploadData.success) {
          alert(uploadData.message || "Media upload failed");
          return;
        }

        mediaUrl = uploadData.media_url;
      }

      // create post
      const postRes = await fetch(`${API_BASE}/api/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: currUserId,
          content_text: postDescription,
          media_url: mediaUrl,
          privacy: "public",
        }),
      });

      const postData = await postRes.json();
      if (postData.success || postRes.ok) {
        alert("Post created successfully!");
        setPostDescription("");
        setUploadedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
      } else {
        alert(postData.message || "Failed to create post.");
      }
    } catch (err) {
      console.error(err);
      alert("An error occurred while uploading your post.");
    }
  };

  const handleClearAll = () => {
    if (uploadedFile?.preview) {
      URL.revokeObjectURL(uploadedFile.preview);
    }
    setUploadedFile(null);
    setPostDescription('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 md:p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Post</h1>
          <p className="text-gray-600">Upload media files and add a description to create a new post</p>
        </div>

        {/* Upload Area */}
        <div
          className={`border-2 border-dashed rounded-xl p-12 text-center mb-6 transition-all ${isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
            }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={64} className={`mx-auto mb-4 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
          <p className="text-lg font-medium text-gray-700 mb-2">
            {isDragging ? 'Drop file here' : 'Drag and drop file here'}
          </p>
          <p className="text-sm text-gray-500 mb-4">or click to browse</p>
          <button className="px-6 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition">
            Select File
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept={allAcceptedTypes.join(',')}
            onChange={handleFileInputChange}
            className="hidden"
          />
          <p className="text-xs text-gray-400 mt-4">
            Supported: Images (JPEG, PNG, GIF, WebP) and Videos (MP4, WebM)
          </p>
          <p className="text-xs text-gray-400">Maximum file size: 100MB per file</p>
        </div>

        {/* Uploaded File */}
        {uploadedFile && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Selected File
              </h2>
              <button
                onClick={removeFile}
                className="text-sm text-red-600 hover:text-red-700 font-medium flex items-center gap-1"
              >
                <Trash2 size={16} />
                Remove
              </button>
            </div>

            <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition">
              <div className="flex items-start gap-4">
                {/* Preview/Icon */}
                <div className="flex-shrink-0">
                  {uploadedFile.preview ? (
                    <img
                      src={uploadedFile.preview}
                      alt={uploadedFile.name}
                      className="w-20 h-20 object-cover rounded-lg"
                    />
                  ) : (
                    <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center">
                      {getFileIcon(uploadedFile.type)}
                    </div>
                  )}
                </div>

                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{uploadedFile.name}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {formatFileSize(uploadedFile.size)} • {uploadedFile.type.charAt(0).toUpperCase() + uploadedFile.type.slice(1)}
                      </p>
                      {uploadedFile.status === 'uploading' && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                          </div>
                        </div>
                      )}
                      {uploadedFile.status === 'success' && (
                        <div className="mt-2 flex items-center gap-1 text-green-600">
                          <CheckCircle size={16} />
                          <span className="text-sm">Uploaded successfully</span>
                        </div>
                      )}
                    </div>

                    {/* Remove Button */}
                    <button
                      onClick={removeFile}
                      className="p-2 hover:bg-red-50 rounded-full text-red-600 transition"
                      disabled={uploadedFile.status === 'uploading'}
                    >
                      <X size={20} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Post Description */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Post Description <span className="text-gray-400">(optional)</span>
          </label>
          <textarea
            value={postDescription}
            onChange={(e) => setPostDescription(e.target.value)}
            placeholder="What's on your mind? Share your thoughts about this post..."
            rows={4}
            maxLength={500}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
          />
          <p className="text-xs text-gray-400 mt-1 text-right">
            {postDescription.length}/500 characters
          </p>
        </div>

        {/* Create Post Button */}
        {(uploadedFile || postDescription.trim().length > 0) && (
          <div className="flex gap-4">
            <button
              onClick={handleUpload}
              disabled={uploadedFile?.status === 'uploading' || (!uploadedFile && postDescription.trim().length === 0)}
              className="flex-1 bg-blue-500 text-white font-semibold py-4 rounded-xl hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {uploadedFile?.status === 'uploading' ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Creating Post...
                </>
              ) : (
                <>
                  <Upload size={20} />
                  Create Post
                </>
              )}
            </button>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Post Guidelines</p>
              <ul className="list-disc list-inside space-y-1 text-blue-700">
                <li>Ensure all files comply with our community guidelines</li>
                <li>Large files may take longer to upload</li>
                <li>You can upload one file per post</li>
                <li>Add a description to give context to your post</li>
                <li>Posts can contain media, text, or both</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadMedia;

