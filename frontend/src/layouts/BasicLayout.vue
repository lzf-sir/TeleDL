<template>
  <el-container>
    <el-aside width="200px">
      <!-- 侧边栏菜单 -->
      <el-menu
        :default-active="activeMenu"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><pie-chart /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/downloads">
          <el-icon><download /></el-icon>
          <span>下载管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <!-- 顶部导航 -->
        <div class="header-right">
          <el-dropdown>
            <span class="el-dropdown-link">
              <el-avatar :size="30" />
              管理员
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人资料</el-dropdown-item>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main>
        <!-- 页面内容 -->
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import {
  PieChart,
  Upload,
  Download,
  Setting
} from '@element-plus/icons-vue'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const activeMenu = ref(route.path)

const handleLogout = async () => {
  try {
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
.el-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.el-aside {
  background: #1a2a3a;
  min-height: 100vh;
  transition: all 0.3s;
}

.el-menu {
  background: transparent;
}

.el-menu-item, .el-submenu__title {
  color: rgba(255, 255, 255, 0.8);
}

.el-menu-item:hover, .el-submenu__title:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.el-menu-item.is-active {
  color: #fff;
  background-color: rgba(24, 144, 255, 0.2);
}

.el-menu {
  border-right: none;
}
</style>
