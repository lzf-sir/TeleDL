<template>
  <el-card class="tasklist-card">
    <div class="tasklist-toolbar">
      <el-button type="primary" @click="showCreate = true" icon="el-icon-Plus">新建任务</el-button>
      <el-button type="warning" @click="batchPause" :disabled="!multipleSelection.length">批量暂停</el-button>
      <el-button type="success" @click="batchResume" :disabled="!multipleSelection.length">批量恢复</el-button>
      <el-button type="danger" @click="batchDelete" :disabled="!multipleSelection.length">批量删除</el-button>
      <el-select v-model="status" placeholder="状态筛选" clearable style="width: 120px">
        <el-option label="全部" value="" />
        <el-option label="排队中" value="QUEUED" />
        <el-option label="下载中" value="DOWNLOADING" />
        <el-option label="已完成" value="COMPLETED" />
        <el-option label="失败" value="FAILED" />
      </el-select>
      <el-select v-model="downloadType" placeholder="类型筛选" clearable style="width: 120px">
        <el-option label="全部" value="" />
        <el-option label="HTTP" value="http" />
        <el-option label="BT" value="bt" />
      </el-select>
      <el-select v-model="category" placeholder="分类筛选" clearable style="width: 120px">
        <el-option label="全部" value="" />
        <el-option v-for="c in categoryOptions" :key="c.key" :label="c.desc" :value="c.key" />
      </el-select>
      <el-input v-model="keyword" placeholder="关键字搜索（文件名/任务ID）" clearable style="width: 200px" @keyup.enter.native="fetchTasks" />
      <el-button type="primary" @click="fetchTasks" icon="el-icon-Refresh">刷新</el-button>
    </div>
    <div class="tasklist-table-area">
      <el-table :data="tasks" style="width: 100%">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="任务ID" width="220" />
      <el-table-column prop="filename" label="文件名" />
      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" effect="dark">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度">
        <template #default="{ row }">
          <el-progress :percentage="row.progress" :status="progressStatus(row.status)" :text-inside="true" :stroke-width="18" />
        </template>
      </el-table-column>
      <el-table-column prop="download_speed" label="速度(KB/s)" />
      <el-table-column prop="category" label="分类" />
      <el-table-column prop="start_time_str" label="开始时间" />
      <el-table-column prop="end_time_str" label="结束时间" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)" type="primary" plain>详情</el-button>
          <el-button size="small" @click="pauseTask(row)" type="warning" plain v-if="row.status === 'DOWNLOADING' || row.status === 'QUEUED'">暂停</el-button>
          <el-button size="small" @click="resumeTask(row)" type="success" plain v-if="row.status === 'FAILED' || row.status === 'PAUSED'">恢复</el-button>
          <el-button size="small" @click="deleteTask(row)" type="danger" plain>删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>
    <div class="tasklist-pagination">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchTasks"
      />
    </div>

  </el-card>

  <el-dialog v-model="showCreate" title="新建下载任务" width="400px">
    <el-form :model="createForm">
      <el-form-item label="下载链接"><el-input v-model="createForm.url" /></el-form-item>
      <el-form-item label="文件名"><el-input v-model="createForm.filename" /></el-form-item>
      <el-form-item label="类型">
        <el-select v-model="createForm.download_type">
          <el-option label="HTTP" value="http" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showCreate = false">取消</el-button>
      <el-button type="primary" @click="createTask">创建</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const downloadType = ref('')
const category = ref('')
const keyword = ref('')
const categoryOptions = ref([])

const fetchCategories = async () => {
  try {
    const res = await api.get('/categories')
    categoryOptions.value = Object.entries(res).map(([key, desc]) => ({ key, desc }))
  } catch (e) {
    categoryOptions.value = []
  }
}
const showCreate = ref(false)
const multipleSelection = ref([])
const handleSelectionChange = (val) => {
  multipleSelection.value = val
}
// 暂停任务
const pauseTask = async (row) => {
  try {
    await api.post(`/downloads/${row.id}/pause`)
    ElMessage.success('任务已暂停')
    fetchTasks()
  } catch (e) {
    ElMessage.error('暂停失败')
  }
}
// 批量操作
const batchPause = async () => {
  for (const row of multipleSelection.value) {
    if (row.status === 'DOWNLOADING' || row.status === 'QUEUED') await pauseTask(row)
  }
}
const batchResume = async () => {
  for (const row of multipleSelection.value) {
    if (row.status === 'FAILED' || row.status === 'PAUSED') await resumeTask(row)
  }
}
const batchDelete = async () => {
  for (const row of multipleSelection.value) {
    await deleteTask(row)
  }
}
const createForm = reactive({ url: '', filename: '', download_type: 'http' })
const createTask = async () => {
  try {
    await api.post('/downloads', createForm)
    ElMessage.success('任务创建成功')
    showCreate.value = false
    fetchTasks()
  } catch (e) {
    ElMessage.error('创建失败')
  }
}
// 恢复任务
const resumeTask = async (row) => {
  try {
    await api.post(`/downloads/${row.id}/resume`)
    ElMessage.success('任务已恢复')
    fetchTasks()
  } catch (e) {
    ElMessage.error('恢复失败')
  }
}

// 删除任务
const deleteTask = async (row) => {
  try {
    await api.delete(`/downloads/${row.id}`)
    ElMessage.success('任务已删除')
    fetchTasks()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const tasks = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const status = ref('')
const router = useRouter()

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
  CANCELLED: 'warning',
  QUEUED: '',
  DOWNLOADING: '',
  FETCHING_METADATA: '',
  DOWNLOADING_TORRENT: '',
  SEEDING: '',
  DELETED: 'exception' // 假设 DELETED 状态为异常
}[s] || '')

const fetchTasks = async () => {
  try {
    const res = await api.get('/downloads', {
      params: {
        status: status.value || undefined,
        download_type: downloadType.value || undefined,
        category: category.value || undefined,
        limit: pageSize,
        offset: (page.value - 1) * pageSize
      }
    })
    let items = res.items || []
    // 前端关键字过滤（如后端未支持）
    if (keyword.value) {
      items = items.filter(t => (t.filename && t.filename.includes(keyword.value)) || (t.id && t.id.includes(keyword.value)))
    }
    tasks.value = items
    total.value = res.total || items.length
  } catch (e) {
    ElMessage.error('获取任务失败')
  }
}

const viewDetail = (row) => {
  router.push(`/task/${row.id}`)
}

onMounted(fetchTasks)
onMounted(fetchCategories)
</script>

<style>
.tasklist-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: var(--bg-card, #fff);
  border-radius: 16px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.10);
  border: 1px solid var(--border-main, #e3e6ee);
  padding: 0;
  overflow: hidden;
}
.tasklist-toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.tasklist-table-area {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
  background: var(--bg-main, #f6f7fb);
  padding: 0 8px;
}
.tasklist-pagination {
  border-top: 1px solid var(--border-main, #e3e6ee);
  padding: 16px 24px 12px 0;
  background: var(--bg-card, #fff);
  text-align: right;
}
</style>