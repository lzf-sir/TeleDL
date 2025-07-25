<template>
  <div class="dashboard-container">
    <h1>系统仪表盘</h1>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <h3>下载统计</h3>
          <p>进行中: 0</p>
          <p>已完成: 0</p>
          <el-progress :percentage="0" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <h3>系统状态</h3>
          <p>CPU使用率: 0%</p>
          <p>内存使用率: 0%</p>
          <el-progress :percentage="0" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
// 这里将添加数据获取逻辑
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.el-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.el-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.el-progress {
  margin-top: 10px;
}
</style>
