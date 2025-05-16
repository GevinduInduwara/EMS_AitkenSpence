export const API_URL = process.env.EXPO_PUBLIC_API_URL || 'https://your-api-url.com';

export function getApiUrl(path?: string) {
  return path ? `${API_URL}${path}` : API_URL;
}
