import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Автоматически добавляем токен в каждый запрос
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fb_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Глобальная обработка ошибок (например, 401 Unauthorized)
api.interceptors.response.use((response) => {
  return response;
}, (error) => {
  if (error.response?.status === 401) {
    console.error('Session expired. Please re-authenticate.');
    // Можно добавить логику редиректа на логин, если нужно
  }
  return Promise.reject(error);
});

export default api;
