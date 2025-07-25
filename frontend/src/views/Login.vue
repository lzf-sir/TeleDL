<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>TeleDL 后台登录</h2>
      <el-form 
        :model="loginForm" 
        :rules="loginRules" 
        ref="loginFormRef"
        @submit.native.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            prefix-icon="User"
            placeholder="用户名"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            prefix-icon="Lock"
            placeholder="密码"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            native-type="submit"
            :loading="loading">
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

const loginForm = ref({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const loginFormRef = ref(null)
const loading = ref(false)

const handleLogin = async () => {
  try {
    loading.value = true
    await loginFormRef.value.validate()
    
    const response = await api.login(loginForm.value)
    console.log('Full login response:', response)
    
    // 拦截器已处理token存储，这里只需检查登录状态
    if (!response.success) {
      console.error('Login failed:', response)
      throw new Error(response.message || '登录失败')
    }
    
    // 确保拦截器已存储token
    const accessToken = localStorage.getItem('access_token')
    if (!accessToken) {
      console.error('No access token found in storage')
      throw new Error('登录成功但未获取到访问令牌')
    }
    console.log('Token stored:', accessToken)
    
    try {
      // Verify token and update user state
      const meResponse = await api.getMe()
      console.log('User info:', meResponse.data)
      
      // Store user info in localStorage
      localStorage.setItem('user_info', JSON.stringify(meResponse.data))
      localStorage.setItem('authenticated', 'true')
      
      // Connect WebSocket
      import('@/api/websocket').then(ws => {
        ws.default.connectAfterAuth()
      })
      
      ElMessage.success('登录成功')
      try {
        await router.push('/')
        console.log('成功跳转到首页')
        window.location.reload() // 确保应用状态完全刷新
      } catch (error) {
        console.error('路由跳转失败:', error)
        window.location.href = '/' // 回退方案：直接修改location
      }
    } catch (error) {
      console.error('Token verification failed:', error)
      ElMessage.error('登录状态验证失败')
      localStorage.removeItem('token')
    }
  } catch (error) {
    console.error('Login error:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '登录失败')
      localStorage.removeItem('token')
  } finally {
    loading.value = false
  }
}

const handleLogout = async () => {
  try {
    await api.logout()
    // 清除所有认证相关数据
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    localStorage.removeItem('authenticated')
    // 关闭WebSocket连接
    import('@/api/websocket').then(ws => {
      ws.default.close()
    })
    // 跳转到登录页
    router.push('/login')
    // 刷新页面确保状态重置
    window.location.reload()
  } catch (error) {
    console.error('Logout failed:', error)
    ElMessage.error('登出失败: ' + (error.message || '未知错误'))
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}

.login-card {
  width: 400px;
  padding: 20px;
}

h2 {
  text-align: center;
  margin-bottom: 20px;
}
</style>
