import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://localhost:8848',
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

// Add request interceptor to include token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token && !config.url.includes('/auth/token')) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Add response interceptor for consistent error handling
apiClient.interceptors.response.use(
  response => {
    // 处理登录响应，存储token
    if (response.config.url === '/auth/token') {
      console.log('完整登录响应:', response)
      const token = response.data?.token || response.data?.data?.token
      if (token) {
        localStorage.setItem('access_token', token)
        console.log('成功存储access_token:', token)
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
      } else {
        console.error('登录响应中未找到token字段', response.data)
      }
    }
    return response.data
  },
  error => {
    if (error.response) {
      const { data, status } = error.response
      return Promise.reject(data || {
        code: status,
        message: error.message
      })
    }
    return Promise.reject({
      code: 500,
      message: 'Network error'
    })
  }
)

export default {
  // Download相关API
  addDownload(data) {
    return apiClient.post('/api/v1/downloads', data)
  },
  getDownloads(params) {
    return apiClient.get('/api/v1/downloads', { params })
  },
  pauseDownload(id, status) {
    if (status !== 'downloading') {
      return Promise.reject({ 
        code: 400, 
        message: '只有正在下载的任务可以暂停' 
      })
    }
    return apiClient.post(`/api/v1/downloads/${id}/pause`)
  },
  resumeDownload(id) {
    return apiClient.post(`/api/v1/downloads/${id}/resume`)
  },
  deleteDownload(id) {
    return apiClient.delete(`/api/v1/downloads/${id}`)
  },

  // Config相关API
  getConfig() {
    return apiClient.get('/api/v1/config')
  },
  updateConfig(data) {
    return apiClient.put('/api/v1/config', data)
  },

  // Auth相关API
  login(credentials) {
    return apiClient.post('/auth/token', credentials, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
  },
  getMe() {
    return apiClient.get('/auth/me')
  },
  logout() {
    return Promise.resolve({ success: true })
  },
  refreshToken() {
    return apiClient.post('/auth/refresh', {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
  }
}
