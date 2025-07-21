<template>
  <el-card>
    <el-table :data="categories" style="width: 100%">
      <el-table-column prop="key" label="分类标识">
        <template #default="{ row }">
          <el-tag type="info" effect="plain">
            <el-icon><i-ep-Folder /></el-icon>
            {{ row.key }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="desc" label="描述" />
    </el-table>
    <el-button type="primary" @click="fetchCategories" style="margin-top: 16px">刷新</el-button>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { Folder } from '@element-plus/icons-vue'

const categories = ref([])

const fetchCategories = async () => {
  try {
    const res = await api.get('/categories')
    categories.value = Object.entries(res).map(([key, desc]) => ({ key, desc }))
  } catch (e) {
    ElMessage.error('获取分类失败')
  }
}

onMounted(fetchCategories)
</script>
