<template>
  <div class="downloads-container">
    <div class="toolbar">
      <el-button-group>
        <el-button 
          type="primary" 
          @click="showAddDialog"
          :icon="Plus"
        >
          添加下载
        </el-button>
        <el-button 
          type="danger" 
          @click="batchCancel"
          :disabled="!selectedDownloads.length"
          :icon="Delete"
        >
          批量取消
        </el-button>
      </el-button-group>

      <div class="filters">
        <el-tag v-if="filterType" closable @close="filterType = ''">
          文件类型: {{ filterType }}
        </el-tag>
        <el-select v-model="filterType" placeholder="文件类型" clearable>
          <el-option
            v-for="type in Object.keys(fileTypes)"
            :key="type"
            :label="type"
            :value="type"
          />
        </el-select>
        
        <el-tag v-if="filterStatus" closable @close="filterStatus = ''">
          状态: {{ statusOptions.find(s => s.value === filterStatus)?.label }}
        </el-tag>
        <el-select v-model="filterStatus" placeholder="状态" clearable>
          <el-option
            v-for="status in statusOptions"
            :key="status.value"
            :label="status.label"
            :value="status.value"
          />
        </el-select>
      </div>
    </div>

    <!-- 新增速度图表 -->
    <div class="speed-chart" ref="speedChart"></div>

    <el-table 
      ref="downloadTable"
      :data="filteredDownloads"
      style="width: 100%"
      v-loading="loading"
      :empty-text="emptyText"
      stripe
      border
      highlight-current-row
      :row-class-name="tableRowClassName"
      @selection-change="handleSelectionChange"
    >
      <!-- 原有表格列定义 -->
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="文件名" min-width="200">
        <template #default="{row}">
          <div class="file-info" v-if="row">
            <el-icon :size="20" :color="getFileTypeColor(row.type)">
              <component :is="getFileTypeIcon(row.type)" />
            </el-icon>
              <div class="file-details">
                <div class="file-name">{{ extractFileName(row.path, row.url) }}</div>
                <div class="file-meta">
                  <div class="file-size">{{ formatFileSize(row.total_size) }}</div>
                  <div class="file-id">ID: {{ row.id }}</div>
                </div>
              </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="下载进度" min-width="300">
        <template #default="{row}">
          <div class="progress-container">
            <el-progress 
              :percentage="row.progress" 
              :status="getProgressStatus(row.status)"
              :stroke-width="12"
              :show-text="false"
            />
            <div class="progress-details">
              <div class="progress-info">
                <span class="progress-percent">{{ row.progress }}%</span>
                <span class="progress-size">
                  {{ formatFileSize(row.downloaded_size) }}/{{ formatFileSize(row.total_size) }}
                </span>
              </div>
              <div class="progress-speed">
                <span v-if="row.speed > 0">
                  {{ formatSpeed(row.speed) }} · 剩余: {{ calculateRemainingTime(row) }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="120" align="center">
        <template #default="{row}">
          <el-tag 
            size="small" 
            :type="getStatusTagType(row.status)"
            effect="plain"
            class="status-tag"
          >
            {{ formatStatus(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="150" fixed="right" align="center">
        <template #default="{row}">
          <div class="action-buttons">
            <el-button 
              size="small" 
              :type="row.status === 'paused' ? 'success' : 'warning'"
              @click="toggleDownload(row)"
              :icon="row.status === 'paused' ? 'CaretRight' : 'VideoPause'"
              :disabled="row.status === 'failed'"
            >
              {{ row.status === 'paused' ? '继续' : '暂停' }}
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="cancelDownload(row)"
              icon="Close"
            >
              取消
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="addDialogVisible" title="添加下载" width="50%">
      <el-form :model="newDownloadForm">
        <el-form-item label="下载URL">
          <el-input v-model="newDownloadForm.url" placeholder="请输入下载链接" />
        </el-form-item>
        <el-form-item label="保存文件名">
          <el-input v-model="newDownloadForm.filename" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addDownload">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import api from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Plus, Delete } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import websocket from '@/api/websocket'

const fileTypes = {
  video: ['mp4', 'avi', 'mkv', 'mov', 'wmv'],
  audio: ['mp3', 'wav', 'flac', 'aac', 'ogg'],
  image: ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
  document: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'],
  archive: ['zip', 'rar', '7z', 'tar', 'gz'],
  executable: ['exe', 'msi', 'dmg', 'pkg', 'deb'],
  other: []
}

const statusOptions = [
  { value: 'queued', label: '排队中' },
  { value: 'downloading', label: '下载中' },
  { value: 'paused', label: '已暂停' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' }
]

// 表格行类名方法
const tableRowClassName = ({ row }) => {
  if (row.status === 'failed') return 'error-row'
  if (row.status === 'completed') return 'success-row'
  return ''
}

// 状态管理
const loading = ref(false)
const filterStatus = ref('')
const emptyText = ref('暂无数据')
const filterType = ref('')
const statusFilters = ref(['queued', 'downloading', 'paused', 'completed', 'failed', 'cancelled'])
const selectedDownloads = ref([])
const addDialogVisible = ref(false)
const newDownloadForm = ref({
  url: '',
  filename: ''
})

// 数据
const allDownloads = ref([])

// 新增图表相关变量
const speedChart = ref(null)
const speedChartData = ref({
  timestamps: [],
  speeds: []
})

// 计算属性
const filteredDownloads = computed(() => {
  return allDownloads.value.filter(d => {
    const typeMatch = !filterType.value || d.type === filterType.value
    const statusMatch = statusFilters.value.includes(d.status)
    return typeMatch && statusMatch
  }).sort((a, b) => {
    // 正在下载的任务排在最前面
    if (a.status === 'downloading' && b.status !== 'downloading') return -1
    if (b.status === 'downloading' && a.status !== 'downloading') return 1
    // 然后按完成时间倒序
    return (b.end_time || 0) - (a.end_time || 0)
  })
})

// 方法
const formatSpeed = (bytes) => {
  if (!bytes) return '0 B/s'
  if (bytes < 1024) return `${bytes} B/s`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB/s`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB/s`
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

const calculateRemainingTime = (task) => {
  if (!task.speed || !task.total_size || task.progress >= 100) return '-'
  const remainingBytes = task.total_size * (100 - task.progress) / 100
  const seconds = Math.ceil(remainingBytes / task.speed)
  
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}小时${minutes}分`
}

const formatStatus = (status) => {
  const map = {
    'queued': '排队中',
    'downloading': '下载中',
    'paused': '已暂停',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return map[status] || status
}

const getStatusTagType = (status) => {
  const map = {
    'queued': '',
    'downloading': 'primary',
    'paused': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return map[status] || ''
}

const getProgressStatus = (status) => {
  return status === 'failed' ? 'exception' : status === 'completed' ? 'success' : ''
}

const getFileTypeIcon = (type) => {
  const icons = {
    video: 'VideoPlay',
    audio: 'Headset',
    image: 'Picture',
    document: 'Document',
    archive: 'Files',
    executable: 'Cpu',
    other: 'Download'
  }
  return icons[type] || 'Download'
}

const getFileTypeColor = (type) => {
  const colors = {
    video: '#ff4d4f',
    audio: '#1890ff',
    image: '#52c41a',
    document: '#faad14',
    archive: '#722ed1',
    executable: '#13c2c2',
    other: '#bfbfbf'
  }
  return colors[type] || '#bfbfbf'
}

const extractFileName = (path, url) => {
  if (path) {
    const parts = path.split('/')
    return parts[parts.length - 1]
  }
  if (url) {
    const parts = url.split('/')
    return parts[parts.length - 1]
  }
  return '未知文件'
}

const handleSelectionChange = (selection) => {
  selectedDownloads.value = selection
}

const showAddDialog = () => {
  addDialogVisible.value = true
}

const addDownload = async () => {
  try {
    loading.value = true
    await api.addDownload({
      url: newDownloadForm.value.url,
      filename: newDownloadForm.value.filename
    })
    ElMessage.success('下载任务已添加')
    addDialogVisible.value = false
    await fetchDownloads()
  } catch (error) {
    ElMessage.error(`添加失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

const batchCancel = async () => {
  try {
    loading.value = true
    await Promise.all(selectedDownloads.value.map(d => 
      api.deleteDownload(d.id)
    ))
    ElMessage.success('已取消选中的下载任务')
    await fetchDownloads()
  } catch (error) {
    ElMessage.error(`取消失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

const toggleDownload = async (download) => {
  try {
    loading.value = true
    if (download.status === 'paused') {
      await api.resumeDownload(download.id)
      ElMessage.success('已继续下载')
    } else {
      await api.pauseDownload(download.id, download.status)
      ElMessage.success('已暂停下载')
    }
    await fetchDownloads()
  } catch (error) {
    ElMessage.error(`操作失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

const cancelDownload = async (download) => {
  try {
    loading.value = true
    await api.deleteDownload(download.id)
    ElMessage.success('已取消下载')
    await fetchDownloads()
  } catch (error) {
    ElMessage.error(`取消失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

const deleteDownload = async (download) => {
  try {
    await ElMessageBox.confirm('确定删除此下载任务吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.deleteDownload(download.id)
    ElMessage.success('已删除下载任务')
    await fetchDownloads()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`删除失败: ${error.message}`)
    }
  }
}

const formatDateTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 新增图表更新方法
const updateSpeedChart = () => {
  if (!speedChart.value) return
  
  const chart = echarts.getInstanceByDom(speedChart.value)
  if (!chart) return
  
  const totalSpeed = allDownloads.value.reduce((sum, d) => {
    return d.status === 'downloading' ? sum + (d.speed || 0) : sum
  }, 0)
  
  const now = new Date()
  const timestamp = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  
  speedChartData.value.timestamps.push(timestamp)
  speedChartData.value.speeds.push(Math.round(totalSpeed / 1024))
  
  // 保留最近20个数据点
  if (speedChartData.value.timestamps.length > 20) {
    speedChartData.value.timestamps.shift()
    speedChartData.value.speeds.shift()
  }
  
  chart.setOption({
    xAxis: {
      data: speedChartData.value.timestamps
    },
    series: [{
      data: speedChartData.value.speeds
    }]
  })
}

const fetchDownloads = async () => {
  try {
    loading.value = true
    const res = await api.getDownloads()
    console.log('API response:', res)
    
    // 处理不同的响应格式
    let items = []
    if (Array.isArray(res)) {
      items = [...res]
    } else if (res?.items) {
      items = [...res.items]
    } else if (res?.data?.items) {
      items = [...res.data.items]
    } else {
      console.error('Unexpected API response format:', res)
      items = []
    }
    
    // 确保每个下载项都有必要字段
    items = items.map(item => ({
      id: item.id,
      status: item.status || item.status_display,
      progress: item.progress || 0,
      speed: item.speed || item.download_speed || 0,
      total_size: item.total_size || 0,
      downloaded_size: item.downloaded_size || 0,
      url: item.url,
      path: item.file_path,
      type: item.file_type || 'other'
    }))
    
    allDownloads.value = items
    console.log('Processed downloads:', allDownloads.value)
    updateSpeedChart()
  } catch (error) {
    console.error('Error fetching downloads:', error)  // 添加详细错误日志
    ElMessage.error(`获取下载列表失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  fetchDownloads()
  // 设置定时刷新
  const timer = setInterval(fetchDownloads, 5000)
  onUnmounted(() => clearInterval(timer))
  
  // 注册WebSocket回调
      websocket.on('downloads', (data) => {
        try {
          console.log('Received WebSocket message:', data)
          if (!data.task_id) return
          
          // 更新现有任务状态
          const index = allDownloads.value.findIndex(d => d.id === data.task_id)
          if (index !== -1) {
            // 直接修改响应式数组的特定字段
            if (data.status !== undefined) {
              allDownloads.value[index].status = data.status
            }
            if (data.progress !== undefined) {
              allDownloads.value[index].progress = data.progress
            }
            if (data.speed !== undefined || data.download_speed !== undefined) {
              allDownloads.value[index].speed = data.speed || data.download_speed
            }
            if (data.downloaded_size !== undefined) {
              allDownloads.value[index].downloaded_size = data.downloaded_size
            }
            if (data.end_time !== undefined) {
              allDownloads.value[index].end_time = data.end_time
            }
            updateSpeedChart()
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error)
          // 出错时也刷新列表确保数据一致
          fetchDownloads()
        }
      })
  
  // 初始化速度图表
  nextTick(() => {
    if (speedChart.value) {
      const chart = echarts.init(speedChart.value, null, {
        renderer: 'canvas',
        useDirtyRect: true
      })
      chart.setOption({
        tooltip: {
          trigger: 'axis',
          formatter: '{b}<br/>{a}: {c} KB/s'
        },
        xAxis: {
          type: 'category',
          data: speedChartData.value.timestamps
        },
        yAxis: {
          type: 'value',
          name: '下载速度 (KB/s)'
        },
        series: [{
          name: '下载速度',
          type: 'line',
          data: speedChartData.value.speeds,
          smooth: true,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(58, 77, 233, 0.8)' },
              { offset: 1, color: 'rgba(58, 77, 233, 0.1)' }
            ])
          }
        }]
      })
    }
  })
})
</script>

<style scoped>
.downloads-container {
  padding: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.filters {
  display: flex;
  gap: 10px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-weight: 500;
}

.file-size {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.file-id {
  font-family: monospace;
  color: var(--el-color-info);
  font-size: 11px;
}

.progress-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.speed-chart {
  width: 100%;
  height: 300px;
  margin-bottom: 20px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.status-tag {
  margin: 0 auto;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}
</style>
