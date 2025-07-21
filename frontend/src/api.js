import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
});

// 请求拦截器，可加 token
api.interceptors.request.use(config => {
  // config.headers['Authorization'] = 'Bearer ...';
  return config;
});

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => Promise.reject(error)
);

export default api;
