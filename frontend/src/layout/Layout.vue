<template>
  <div class="layout-root">
    <header class="admin-header">
      <div class="header-left">
        <span class="logo-mini">T</span>
        <span class="logo-text">TeleDL 后台</span>
      </div>
      <div class="header-center">
        <span class="sys-title">HTTP 下载管理系统</span>
      </div>
      <div class="header-right">
        <el-button size="small" circle :icon="themeIcon" @click="toggleTheme" style="margin-right: 8px;" />
        <!-- 右侧可放用户、设置等 -->
      </div>
    </header>
    <div class="admin-body">
      <aside class="admin-sidebar">
        <el-menu :default-active="activeMenu" router background-color="#23272e" text-color="#fff" active-text-color="#409EFF" class="sidebar-menu">
          <el-menu-item index="/">
            <el-icon><Download /></el-icon>
            <span>任务管理</span>
          </el-menu-item>
          <el-menu-item index="/config">
            <el-icon><Menu /></el-icon>
            <span>配置管理</span>
          </el-menu-item>
        </el-menu>
        <div class="sidebar-footer">© 2025 TeleDL</div>
      </aside>
      <main class="admin-main">
        <MainContainer>
          <router-view />
        </MainContainer>
      </main>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import { Download, Menu, Sunny, Moon } from '@element-plus/icons-vue'
import MainContainer from './MainContainer.vue'
const route = useRoute()
const activeMenu = computed(() => route.path)

const theme = ref('dark')
const themeIcon = computed(() => theme.value === 'dark' ? Sunny : Moon)

const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.classList.toggle('light-theme', theme.value === 'light')
  document.documentElement.classList.toggle('dark-theme', theme.value === 'dark')
}

onMounted(() => {
  document.documentElement.classList.add('dark-theme')
})
</script>

<style scoped>
.layout-root {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  background: #23272e;
}

.admin-header {
  height: 56px;
  background: #23272e;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px #0002;
  padding: 0 32px;
  z-index: 10;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo-mini {
  font-size: 26px;
  font-weight: bold;
  color: #409EFF;
  background: #fff1;
  border-radius: 8px;
  /* 不限制宽高，随父容器自适应 */
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 主题切换样式 */
:root.light-theme {
  --bg-main: #f6f7fb;
  --bg-card: #fff;
  --bg-sidebar: #fff;
  --text-main: #222;
  --text-secondary: #666;
  --border-main: #e3e6ee;
}
:root.dark-theme {
  --bg-main: #23272e;
  --bg-card: #23272e;
  --bg-sidebar: #23272e;
  --text-main: #fff;
  --text-secondary: #b0b6c3;
  --border-main: #23272e;
}
.logo-text {
  background: var(--bg-main);
  font-weight: bold;
  color: #409EFF;
  background: var(--bg-sidebar);
}
.header-center {
  flex: 1;
  background: var(--bg-sidebar);
}
.sys-title {
  font-size: 18px;
  background: var(--bg-sidebar);
  font-weight: 500;
}
/* 主体区域左右布局 */
.admin-body {
  flex: 1;
  display: flex;
  flex-direction: row;
  min-height: 0;
  min-width: 0;
  background: var(--bg-main);
}
.admin-sidebar {
  width: 220px;
  background: var(--bg-sidebar);
  color: var(--text-main);
  box-shadow: 2px 0 8px #0002;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  padding: 0;
  justify-content: flex-start;
  z-index: 2;
}
.sidebar-menu {
  border-right: none;
  width: 100%;
  background: transparent;
  flex: 1;
}
.sidebar-footer {
  color: #888;
  font-size: 13px;
  text-align: center;
  padding: 16px 0 12px 0;
  width: 100%;
}
.admin-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  background: var(--bg-main);
}
  .main-content {
    flex: 1;
    width: 100%;
    height: 100%;
    margin: 0;
    background: var(--bg-main);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    position: relative;
    box-sizing: border-box;
  }

  .main-card {
    width: 100%;
    height: 100%;
    background: var(--bg-card);
    border-radius: 18px;
    box-shadow: 0 8px 32px 0 rgba(0,0,0,0.18);
    border: 1.5px solid var(--border-main);
    display: flex;
    flex-direction: column;
    padding: 32px 32px 24px 32px;
    box-sizing: border-box;
    overflow: hidden;
  }
</style>
