<template>
  <router-view />
</template>

<script setup>
import { RouterView, useRouter } from 'vue-router'
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()

onMounted(async () => {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      await api.getMe()
    } catch (error) {
      localStorage.removeItem('token')
      ElMessage.error('登录已过期，请重新登录')
      router.push('/login')
    }
  } else if (router.currentRoute.value.meta.requiresAuth) {
    router.push('/login')
  }
})
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  height: 100vh;
}
</style>
