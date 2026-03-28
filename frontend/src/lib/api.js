import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const newsApi = {
  getAll: (search = '', tag = '') => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (tag) params.append('tag', tag);
    return api.get(`/news?${params.toString()}`);
  },
  getById: (id) => api.get(`/news/${id}`),
  getBySlug: (slug) => api.get(`/news/by-slug/${slug}`),
};

export const adminApi = {
  login: (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    return api.post('/admin/login', formData.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },
  getAllNews: () => api.get('/admin/news'),
  createNews: (formData) => api.post('/admin/news', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  updateNews: (id, formData) => api.put(`/admin/news/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteNews: (id) => api.delete(`/admin/news/${id}`),
  runAutomation: () => api.post('/admin/automation/run'),
  backfillImages: () => api.post('/admin/backfill-images'),
};

export const getImageUrl = (imagePath) => {
  if (!imagePath) return null;
  // Images are now served from database via API endpoint
  if (imagePath.startsWith('/')) {
    return `/api${imagePath}`;
  }
  return `/api${imagePath}`;
};

export default api;
