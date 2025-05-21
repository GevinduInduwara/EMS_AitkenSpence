// Use your local network IP address for physical device testing
// In production, this should be your production API URL
export const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://172.20.10.3:5001';

// For debugging
console.log('API URL:', API_URL);

export function getApiUrl(path?: string) {
  return path ? `${API_URL}${path}` : API_URL;
}
