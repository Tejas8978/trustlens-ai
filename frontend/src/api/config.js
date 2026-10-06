import axios from 'axios';

export const DEFAULT_FALLBACK_URL = 'https://trustlens-backend.onrender.com';

/**
 * Returns the active Backend API URL.
 * Priority:
 * 1. User-customized URL in localStorage ('VITE_API_URL')
 * 2. Vite environment variable ('import.meta.env.VITE_API_URL')
 * 3. Empty string on localhost (routes through Vite dev proxy)
 * 4. Production default Render service fallback
 */
export function getApiUrl() {
  const stored = localStorage.getItem('VITE_API_URL');
  if (stored !== null) {
    return stored.trim().replace(/\/$/, '');
  }

  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) {
    return envUrl.trim().replace(/\/$/, '');
  }

  if (
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ) {
    return '';
  }

  return DEFAULT_FALLBACK_URL;
}

/**
 * Save user-configured API URL to localStorage and notify listeners.
 */
export function setApiUrl(url) {
  const cleanUrl = (url || '').trim().replace(/\/$/, '');
  if (cleanUrl) {
    localStorage.setItem('VITE_API_URL', cleanUrl);
  } else {
    localStorage.setItem('VITE_API_URL', '');
  }
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('trustlens_api_url_changed', { detail: cleanUrl }));
  }
}

/**
 * Reset API URL to default.
 */
export function resetApiUrl() {
  localStorage.removeItem('VITE_API_URL');
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('trustlens_api_url_changed', { detail: getApiUrl() }));
  }
}

/**
 * Test connectivity to a target backend URL.
 * Checks the /health endpoint.
 */
export async function testApiUrl(targetUrl) {
  const base = (targetUrl !== undefined ? targetUrl : getApiUrl()).replace(/\/$/, '');
  const endpoint = base ? `${base}/health` : '/health';
  const start = Date.now();

  try {
    const res = await axios.get(endpoint, {
      timeout: 18000,
      headers: {
        'Accept': 'application/json',
      },
    });
    const latency = Date.now() - start;
    return {
      ok: true,
      status: res.status,
      latency,
      data: res.data,
    };
  } catch (err) {
    const latency = Date.now() - start;
    const status = err.response?.status;
    const isTimeout = err.code === 'ECONNABORTED' || latency >= 17000;
    const isNoServer = status === 404 && (
      err.response?.headers?.['x-render-routing'] === 'no-server' ||
      typeof err.response?.data === 'string' && err.response?.data.includes('Not Found')
    );

    return {
      ok: false,
      status,
      latency,
      timeout: isTimeout,
      noServer: isNoServer,
      error: err.response?.data?.detail || err.message || 'Cannot reach server',
    };
  }
}
