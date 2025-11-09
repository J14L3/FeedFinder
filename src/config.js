// src/config.js
// For local development
// export const API_BASE = "http://localhost:5000";

// For production - use relative URL so nginx handles SSL termination
// This works if nginx proxies /api/* to your backend
export const API_BASE = "http://3.150.122.114:5000";

// Alternative: If you need absolute URL, use your domain with HTTPS
// export const API_BASE = "https://your-domain.com";