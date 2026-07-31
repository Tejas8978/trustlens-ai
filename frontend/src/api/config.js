export function getApiUrl() {
  const stored = localStorage.getItem('VITE_API_URL');
  if (stored) return stored.replace(/\/$/, '');

  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) return envUrl.replace(/\/$/, '');

  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return '';
  }

  return 'https://trustlens-backend.onrender.com';
}
