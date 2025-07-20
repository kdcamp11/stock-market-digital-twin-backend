// src/api.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://stock-market-digital-twin-backend-6.onrender.com';

// Export the base URL for direct use
export const apiUrl = API_BASE_URL;

// Helper function to build full API URLs
export function buildApiUrl(path) {
  return `${API_BASE_URL}${path}`;
}
