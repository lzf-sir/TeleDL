<template>
  <Layout />
</template>

<script setup>
import Layout from './layout/Layout.vue'
</script>

<style scoped>
.admin-root {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  background: #181a20;
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
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
  letter-spacing: 2px;
}
.header-center {
  flex: 1;
  text-align: center;
}
.sys-title {
  font-size: 18px;
  color: #fff;
  font-weight: 500;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.admin-body {
  flex: 1;
  display: flex;
  height: calc(100vh - 56px);
  overflow: hidden;
}
.admin-sidebar {
  width: 220px;
  background: #23272e;
  color: #fff;
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
  overflow-y: auto;
  background: #181a20;
  display: flex;
  flex-direction: column;
}
.main-content {
  max-width: 1100px;
  margin: 32px auto 0 auto;
  padding: 32px 24px 24px 24px;
  background: #23272e;
  border-radius: 12px;
  box-shadow: 0 2px 16px #0003;
  min-height: 70vh;
}
</style>
