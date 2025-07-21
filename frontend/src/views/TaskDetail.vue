<template>
  <el-card v-if="task">
    <div style="margin-bottom: 16px;">
      <el-button size="small" @click="pauseTask" type="warning" plain v-if="task.status === 'DOWNLOADING' || task.status === 'QUEUED'">暂停</el-button>
      <el-button size="small" @click="resumeTask" type="success" plain v-if="task.status === 'FAILED' || task.status === 'PAUSED'">恢复</el-button>
      <el-button size="small" @click="deleteTask" type="danger" plain>删除</el-button>
    </div>
    <el-descriptions title="任务详情" :column="2" border>
      <el-descriptions-item label="任务ID">{{ task.id }}</el-descriptions-item>
      <el-descriptions-item label="文件名">{{ task.filename }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="statusType(task.status)" effect="dark">{{ statusLabel(task.status) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="进度">
        <el-progress :percentage="task.progress" :status="progressStatus(task.status)" :text-inside="true" :stroke-width="18" />
      </el-descriptions-item>
      <el-descriptions-item label="速度">{{ task.download_speed }} KB/s</el-descriptions-item>
      <el-descriptions-item label="分类">{{ task.category }}</el-descriptions-item>
      <el-descriptions-item label="开始时间">{{ task.start_time_str }}</el-descriptions-item>
      <el-descriptions-item label="结束时间">{{ task.end_time_str }}</el-descriptions-item>
      <el-descriptions-item label="错误信息">
        <span v-if="task.error" style="color: #f56c6c">{{ task.error }}</span>
        <span v-else>--</span>
      </el-descriptions-item>
    </el-descriptions>
    <el-button @click="$router.back()" style="margin-top: 16px">返回</el-button>
  </el-card>
</template>

<script setup>
const pauseTask = async () => {
  try {
    await api.post(`/downloads/${task.value.id}/pause`)
    ElMessage.success('任务已暂停')
    fetchTask()
  } catch (e) {
    ElMessage.error('暂停失败')
  }
}
const resumeTask = async () => {
  try {
    await api.post(`/downloads/${task.value.id}/resume`)
    ElMessage.success('任务已恢复')
    fetchTask()
  } catch (e) {
    ElMessage.error('恢复失败')
  }
}
const deleteTask = async () => {
  try {
    await api.delete(`/downloads/${task.value.id}`)
    ElMessage.success('任务已删除')
    task.value = null
    setTimeout(() => { history.back() }, 500)
  } catch (e) {
    ElMessage.error('删除失败')
  }
}
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const task = ref(null)

const statusLabel = s => ({
  QUEUED: '排队中',
  DOWNLOADING: '下载中',
  COMPLETED: '已完成',
  FAILED: '失败',
  PAUSED: '暂停',
  CANCELLED: '已取消'
}[s] || s)
const statusType = s => ({
  QUEUED: 'info',
  DOWNLOADING: 'primary',
  COMPLETED: 'success',
  FAILED: 'danger',
  PAUSED: 'warning',
  CANCELLED: 'warning'
}[s] || 'info')
const progressStatus = s => ({
  COMPLETED: 'success',
  FAILED: 'exception',
  PAUSED: 'warning',
  CANCELLED: 'warning'
}[s] || 'active')

const fetchTask = async () => {
  try {
    const res = await api.get(`/downloads/${route.params.id}`)
    task.value = res
  } catch (e) {
    ElMessage.error('获取任务详情失败')
  }
}

onMounted(fetchTask)
</script>
