<template>
  <el-card>
    <el-form :model="config" label-width="160px">
      <el-form-item label="项目名称">
        <el-input v-model="config.project_name" disabled />
      </el-form-item>
      <el-form-item label="API 前缀">
        <el-input v-model="config.api_prefix" disabled />
      </el-form-item>
      <el-form-item label="允许跨域">
        <el-input v-model="config.cors_origins" />
      </el-form-item>
      <el-form-item label="下载目录">
        <el-input v-model="config.download_dir" />
      </el-form-item>
      <el-form-item label="最大并发下载数">
        <el-input-number v-model="config.max_concurrent_downloads" :min="1" :max="20" />
      </el-form-item>
      <el-form-item label="分块大小 (字节)">
        <el-input-number v-model="config.chunk_size" :min="1024" :step="1024" />
      </el-form-item>
      <el-form-item label="断点续传">
        <el-switch v-model="config.resume_support" />
      </el-form-item>
      <el-form-item label="重试次数">
        <el-input-number v-model="config.retry_attempts" :min="0" :max="10" />
      </el-form-item>
      <el-form-item label="重试间隔 (秒)">
        <el-input-number v-model="config.retry_delay" :min="0" :max="60" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="saveConfig">保存配置</el-button>
        <el-button @click="fetchConfig">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'

const config = ref({})

const fetchConfig = async () => {
  try {
    const res = await api.get('/config')
    if (typeof res === 'object' && res !== null && !Array.isArray(res)) {
      config.value = res
    } else {
      config.value = {}
      ElMessage.error('获取配置失败：返回数据异常')
    }
  } catch (e) {
    config.value = {}
    ElMessage.error('获取配置失败')
  }
}

const saveConfig = async () => {
  try {
    await api.put('/config', config.value)
    ElMessage.success('配置已保存')
    fetchConfig()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(fetchConfig)
</script>
