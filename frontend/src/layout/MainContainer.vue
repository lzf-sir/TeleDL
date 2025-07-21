<template>
  <div class="main-content">
    <div class="main-card">
      <slot />
    </div>
  </div>
</template>

<script setup>
// 仅布局，无逻辑
</script>

<style scoped>
.main-content {
  width: 100%;
  height: 100%;
  margin: 0;
  background: var(--bg-main, #f6f7fb);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  position: relative;
  box-sizing: border-box;
}
.main-card {
  width: 100%;
  height: 100%;
  background: var(--bg-card, #fff);
  border-radius: 18px;
  box-shadow: 0 8px 32px 0 rgba(0,0,0,0.12);
  border: 1.5px solid var(--border-main, #e3e6ee);
  display: flex;
  flex-direction: column;
  padding: 32px 32px 24px 32px;
  box-sizing: border-box;
  overflow: hidden;
}
</style>
