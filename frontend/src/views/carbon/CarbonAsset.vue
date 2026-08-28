<template>
  <div class="page">
    <PageHeader title="碳资产管理" subtitle="管理碳配额、CCER 等碳资产，跟踪持有与使用情况" />

    <el-card class="panel">
      <div class="filter-bar">
        <el-button type="primary" @click="openAdd">新增资产</el-button>
      </div>
      <el-table :data="list" border stripe v-loading="loading" :empty-text="'暂无资产'">
        <el-table-column prop="asset_type" label="类型" width="90" />
        <el-table-column prop="year" label="年" width="70" />
        <el-table-column prop="project_name" label="项目名称" />
        <el-table-column prop="quantity" label="总量(tCO₂)" align="right" />
        <el-table-column prop="used_quantity" label="已用(tCO₂)" align="right" />
        <el-table-column label="剩余" align="right" width="100">
          <template #default="{ row }">{{ fmt(row.quantity - row.used_quantity) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }"><el-tag :type="row.status === '有效' ? 'success' : 'info'">{{ row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
    </el-card>

    <el-dialog v-model="visible" :title="editing ? '编辑资产' : '新增资产'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="资产类型">
          <el-select v-model="form.asset_type" style="width:100%"><el-option label="配额" value="配额" /><el-option label="CCER" value="CCER" /><el-option label="其他" value="其他" /></el-select>
        </el-form-item>
        <el-form-item label="年份" prop="year"><el-input v-model.number="form.year" type="number" /></el-form-item>
        <el-form-item label="项目名称"><el-input v-model="form.project_name" /></el-form-item>
        <el-form-item label="总量(tCO₂)"><el-input v-model.number="form.quantity" type="number" /></el-form-item>
        <el-form-item label="已用(tCO₂)"><el-input v-model.number="form.used_quantity" type="number" /></el-form-item>
        <el-form-item label="获取日期"><el-date-picker v-model="form.acquisition_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="到期日期"><el-date-picker v-model="form.expiry_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width:100%"><el-option label="有效" value="有效" /><el-option label="已过期" value="已过期" /><el-option label="已注销" value="已注销" /></el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import { listAssets, createAsset, updateAsset, deleteAsset } from '@/api'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(50); const loading = ref(false)
const visible = ref(false); const editing = ref(false); const saving = ref(false); const formRef = ref(null)
const form = reactive({ id: null, asset_type: '配额', year: new Date().getFullYear(), project_name: '', quantity: 0, used_quantity: 0, acquisition_date: null, expiry_date: null, status: '有效' })
const rules = { year: [{ required: true, message: '请输入年份', trigger: 'blur' }] }
function fmt(v, d = 2) { if (v == null || isNaN(v)) return '0'; return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d }) }

async function load() {
  loading.value = true
  try { const res = await listAssets({ page: page.value, page_size: pageSize.value }); list.value = res.items || []; total.value = res.total || 0 } finally { loading.value = false }
}
function openAdd() { editing.value = false; Object.assign(form, { id: null, asset_type: '配额', year: new Date().getFullYear(), project_name: '', quantity: 0, used_quantity: 0, acquisition_date: null, expiry_date: null, status: '有效' }); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try { if (editing.value) await updateAsset(form.id, { ...form }); else await createAsset({ ...form }); ElMessage.success('已保存'); visible.value = false; load() } finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm('删除该资产？', '提示', { type: 'warning' }).then(async () => { await deleteAsset(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(load)
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; } .filter-bar { display: flex; gap: 12px; margin-bottom: 14px; }</style>
