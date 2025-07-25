<template>
  <div class="settings-container">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>

      <el-tabs type="border-card">
        <el-tab-pane label="下载设置">
          <el-form 
            :model="settings" 
            label-width="180px"
            :rules="rules"
            ref="settingsForm"
          >
            <el-form-item label="下载目录" prop="downloadDir">
              <el-input v-model="settings.downloadDir" placeholder="请输入下载目录路径">
                <template #append>
                  <el-button icon="el-icon-folder-opened" @click="selectDirectory" />
                </template>
              </el-input>
              <el-tag size="small" type="info" style="margin-left: 10px;">
                默认值: {{defaultSettings.downloadDir}}
              </el-tag>
            </el-form-item>

            <el-form-item label="最大下载速度" prop="maxDownloadSpeed">
              <el-input-number 
                v-model="settings.maxDownloadSpeed" 
                :min="0" 
                :step="100"
                controls-position="right"
              />
              <span class="unit">KB/s</span>
              <el-tag size="small" type="info" style="margin-left: 10px;">
                默认值: {{defaultSettings.maxDownloadSpeed}} KB/s
              </el-tag>
            </el-form-item>

            <el-form-item label="最大上传速度" prop="maxUploadSpeed">
              <el-input-number 
                v-model="settings.maxUploadSpeed" 
                :min="0" 
                :step="100"
                controls-position="right"
              />
              <span class="unit">KB/s</span>
              <el-tag size="small" type="info" style="margin-left: 10px;">
                默认值: {{defaultSettings.maxUploadSpeed}} KB/s
              </el-tag>
            </el-form-item>

            <el-form-item label="最大并发下载数" prop="maxConcurrentDownloads">
              <el-input-number 
                v-model="settings.maxConcurrentDownloads" 
                :min="1" 
                :max="20"
              />
              <el-tag size="small" type="info" style="margin-left: 10px;">
                默认值: {{defaultSettings.maxConcurrentDownloads}}
              </el-tag>
            </el-form-item>

            <el-form-item label="重试次数" prop="retryAttempts">
              <el-input-number 
                v-model="settings.retryAttempts" 
                :min="0" 
                :max="10"
              />
              <el-tag size="small" type="info" style="margin-left: 10px;">
                默认值: {{defaultSettings.retryAttempts}}
              </el-tag>
            </el-form-item>

            <el-form-item label="超时时间" prop="timeout">
              <el-input-number 
                v-model="settings.timeout" 
                :min="10" 
                :max="300"
              />
              <span class="unit">秒</span>
              <el-tag size="small" type="info" style="margin-left: 10px;">
                默认值: {{defaultSettings.timeout}} 秒
              </el-tag>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="网络设置">
          <el-form 
            :model="settings" 
            label-width="180px"
          >
            <el-form-item label="监听端口" prop="port">
              <el-input-number 
                v-model="settings.port" 
                :min="1024" 
                :max="65535"
              />
              <el-tag size="small" type="info" style="margin-left: 10px;">
                默认值: {{defaultSettings.port}}
              </el-tag>
            </el-form-item>

            <el-form-item label="最大连接数" prop="maxConnections">
              <el-input-number 
                v-model="settings.maxConnections" 
                :min="1" 
                :max="500"
              />
              <el-tag size="small" type="info" style="margin-left: 10px;">
                默认值: {{defaultSettings.maxConnections}}
              </el-tag>
            </el-form-item>

            <el-form-item label="启用代理" prop="useProxy">
              <el-switch v-model="settings.useProxy" />
            </el-form-item>

            <el-form-item label="代理地址" prop="proxyAddress" v-if="settings.useProxy">
              <el-input v-model="settings.proxyAddress" placeholder="例如: http://proxy.example.com:8080" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <div class="form-actions">
        <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
        <el-button @click="resetSettings">恢复默认</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onBeforeMount } from 'vue'
import api from '@/api'
import { ElMessage } from 'element-plus'

const defaultSettings = {
  downloadDir: '/downloads',
  maxDownloadSpeed: 0,
  maxUploadSpeed: 0,
  maxConcurrentDownloads: 5,
  retryAttempts: 3,
  timeout: 60,
  port: 6881,
  maxConnections: 100,
  useProxy: false,
  proxyAddress: ''
}

// 使用reactive确保深度响应式
const settings = reactive({})
const rules = reactive({
  downloadDir: [
    { required: true, message: '请输入下载目录', trigger: 'blur' }
  ],
  maxDownloadSpeed: [
    { type: 'number', min: 0, message: '必须大于等于0', trigger: 'blur' }
  ],
  port: [
    { type: 'number', min: 1024, max: 65535, message: '端口范围1024-65535', trigger: 'blur' }
  ]
})

const saving = ref(false)
const settingsForm = ref(null)

// 在组件挂载前加载设置
onBeforeMount(async () => {
  Object.assign(settings, JSON.parse(JSON.stringify(defaultSettings)))
  await loadSettings()
})

const loadSettings = async () => {
  try {
    const response = await api.getConfig()
    if (response.success && response.data) {
      settings.value = response.data.data
    } else {
      throw new Error(response.message || '获取配置失败')
    }
  } catch (error) {
    console.error('加载设置失败:', error)
    ElMessage.error('加载设置失败')
  }
}

const saveSettings = async () => {
  try {
    saving.value = true
    const response = await api.updateConfig(settings.value)
    if (response.success) {
      ElMessage.success('设置保存成功')
    } else {
      throw new Error(response.message || '保存配置失败')
    }
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

const resetSettings = async () => {
  try {
    // 重置为默认配置
    settings.value = {...defaultSettings}
    await api.updateConfig(defaultSettings)
    ElMessage.success('已恢复默认设置')
  } catch (error) {
    console.error('恢复默认设置失败:', error)
    ElMessage.error('恢复默认设置失败')
  }
}

const selectDirectory = () => {
  // TODO: 实现目录选择对话框
  console.log('选择目录')
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
}

.settings-card {
  max-width: 900px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-actions {
  margin-top: 20px;
  text-align: center;
}

.unit {
  margin-left: 10px;
  color: #909399;
}
</style>
