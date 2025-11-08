import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // IMPORTANT: Set base to your repository name when deploying to GitHub Pages
  // Example: if your repo is username.github.io/FeedFinder, use '/FeedFinder/'
  // Change this to match your actual repo name
  // base: '/', // use this for testing
  base: '/feedfinder', // use this for live
  server: {
    port: 5173
  }
});
