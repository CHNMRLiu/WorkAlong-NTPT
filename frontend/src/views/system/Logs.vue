<template>
  <div class="page">
    <PageHeader title="操作日志" subtitle="记录关键操作，便于审计追溯" />
    <div class="app-card">
      <div class="filter-bar">
        <el-select v-model="module" placeholder="按模块筛选" clearable style="width:180px" @change="load">
          <el-option v-for="m in modules" :key="m" :label="m" :value="m" />
        </el-select>
        <el-button @click="load">查询</el-button>
      </div>
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column prop="module" label="模块" width="100" />
        <el-table-column prop="action" label="动作" width="100" />
        <el-table-column prop="ip" label="IP" width="130" />
        <el-table-column prop="user_agent" label="客户端" show-overflow-tooltip />
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next"
        :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import { listLogs } from '@/api'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const module = ref('')
const loading = ref(false)
const modules = ['认证', '系统管理', '能源消费', '碳排放', '看板']

async function load() {
  loading.value = true
  try { const res = await listLogs({ page: page.value, page_size: pageSize.value, module: module.value }); list.value = res.items; total.value = res.total } catch (e) {} finally { loading.value = false }
}
onMounted(load)
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; }</style>
