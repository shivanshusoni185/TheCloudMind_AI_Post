import axios from 'axios';

const API_BASE = '/api';

// 15 s timeout — enough for a warm backend; prevents hanging forever on
// cold-start or transient network issues.
const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── localStorage stale-while-revalidate cache ────────────────────
// Keyed by request path. Shows cached data instantly while the fresh
// request completes in the background. TTL: 5 minutes.
const CACHE_PREFIX = 'tcm_v1_';
const CACHE_TTL_MS = 5 * 60 * 1000;

export function getLocalCache(key) {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_TTL_MS) return null;
    return data;
  } catch {
    return null;
  }
}

export function setLocalCache(key, data) {
  try {
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({ data, ts: Date.now() }));
  } catch {
    // Quota exceeded — silently ignore
  }
}

// ── Auto-retry helper ────────────────────────────────────────────
// Retries once after a 1.5 s delay on network errors or 5xx responses.
async function withRetry(fn) {
  try {
    return await fn();
  } catch (err) {
    const isRetryable =
      !err.response || err.response.status >= 500;
    if (isRetryable) {
      await new Promise((r) => setTimeout(r, 1500));
      return fn();
    }
    throw err;
  }
}

// ── Public API ───────────────────────────────────────────────────
export const newsApi = {
  getAll: (search = '', tag = '') => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (tag) params.append('tag', tag);
    return withRetry(() => api.get(`/news?${params.toString()}`));
  },
  getById: (id) => withRetry(() => api.get(`/news/${id}`)),
  getBySlug: (slug) => withRetry(() => api.get(`/news/by-slug/${slug}`)),
};

export const adminApi = {
  login: (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/admin/login', formData.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  getAllNews: () => api.get('/admin/news'),
  createNews: (formData) =>
    api.post('/admin/news', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  updateNews: (id, formData) =>
    api.put(`/admin/news/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  deleteNews: (id) => api.delete(`/admin/news/${id}`),
  runAutomation: () => api.post('/admin/automation/run', null, { timeout: 120000 }),
  refreshAutomationImages: () => api.post('/admin/automation/refresh-images', null, { timeout: 120000 }),
  refreshAutomationContent: () => api.post('/admin/automation/refresh-content', null, { timeout: 120000 }),
};

export const getImageUrl = (imagePath) => {
  if (!imagePath) return null;
  if (imagePath.startsWith('/')) return `/api${imagePath}`;
  return `/api${imagePath}`;
};

export default api;
