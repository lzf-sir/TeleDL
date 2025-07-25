import { ElNotification } from 'element-plus'

class WebSocketClient {
  constructor() {
    this.socket = null
    this.heartbeatInterval = null
    this.callbacks = {
      connect: [],
      downloads: [],
      error: [],
      disconnect: []
    }
    this.connectionState = 'disconnected'
    this.reconnectAttempts = 1
  }

  async connect() {
    // Clear any existing connection
    if (this.socket) {
      this.close()
    }

    let token = localStorage.getItem('access_token')
    if (!token) {
      console.error('缺少access_token - 无法建立WebSocket连接')
      ElNotification.error({
        title: '连接错误',
        message: '用户未登录或token无效'
      })
      return false
    }

    // Check token expiration
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const now = Date.now() / 1000
      if (payload.exp < now + 300) { // If token expires in less than 5 minutes
        const response = await api.refreshToken()
        if (response.success) {
          token = response.data.token
          localStorage.setItem('access_token', token)
        }
      }
    } catch (error) {
      console.error('Token验证失败:', error)
    }
    console.log('获取到的access_token:', token)  // 添加token调试日志
    
    try {
    // 强制使用环境变量配置，不依赖window.location
    const protocol = import.meta.env.VITE_WS_PROTOCOL
    const host = import.meta.env.VITE_WS_HOST
    const port = import.meta.env.VITE_WS_PORT
    const path = import.meta.env.VITE_WS_PATH
    const url = `${protocol}://${host}:${port}${path}?token=${encodeURIComponent(token)}`
    console.log('WebSocket连接URL:', url)  // 添加调试日志
    console.log('Connecting to WebSocket:', url)
    this.socket = new WebSocket(url)
    this.setupSocketHandlers()
    return true
    } catch (error) {
      console.error('WebSocket connection failed:', error)
      return false
    }
  }

  // Call this after successful login
  connectAfterAuth() {
    return this.connect()
  }

  setupSocketHandlers() {
    if (!this.socket) return

    this.socket.onopen = () => {
      this.connectionState = 'connected'
      this.callbacks.connect.forEach(cb => cb())
      ElNotification.success({
        title: 'Connected',
        message: 'WebSocket connection established'
      })
      
      // Start heartbeat
      this.heartbeatInterval = setInterval(() => {
        if (this.socket?.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({type: 'ping'}))
        }
      }, 30000)
    }

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'downloads') {
        this.callbacks.downloads.forEach(cb => cb(data.payload))
      }
    }

    this.socket.onerror = (error) => {
      this.callbacks.error.forEach(cb => cb(error))
      ElNotification.error({
        title: 'WebSocket Error',
        message: error.message
      })
    }

    this.socket.onclose = (event) => {
      this.connectionState = 'disconnected'
      console.log('WebSocket closed:', event.code, event.reason)
      
      // Clear heartbeat
      if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval)
        this.heartbeatInterval = null
      }
      
      this.callbacks.disconnect.forEach(cb => cb(event))
      
      if (event.code !== 1000) { // Don't reconnect if closed normally
        const baseDelay = import.meta.env.VITE_WS_RECONNECT_INTERVAL || 5000
        const maxDelay = 30000
        const attempt = this.reconnectAttempts || 1
        const delay = Math.min(baseDelay * Math.pow(2, attempt - 1), maxDelay)
        this.reconnectAttempts = attempt + 1
        
        console.log(`Will attempt reconnect in ${delay}ms`)
        setTimeout(() => {
          console.log('Attempting to reconnect WebSocket...')
          this.connect().then(success => {
            if (!success) {
              this.socket?.close()
              this.socket = null
            } else {
              this.reconnectAttempts = 1 // Reset on successful reconnect
            }
          })
        }, delay)
      }
    }
  }

  on(event, callback) {
    if (this.callbacks[event]) {
      this.callbacks[event].push(callback)
    }
    return this
  }

  close() {
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
  }
}

export default new WebSocketClient()
