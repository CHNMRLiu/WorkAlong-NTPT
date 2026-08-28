<template>
  <div class="page">
    <PageHeader title="供应链碳管理" subtitle="管理上游供应商及其材料/能耗碳数据，支撑范围3核算" />

    <el-row :gutter="16">
      <el-col :span="11">
        <el-card class="panel">
          <template #header><span class="panel__title">供应商</span>
            <el-button style="float:right" type="primary" size="small" @click="openSup">新增供应商</el-button>
          </template>
          <el-table :data="suppliers" border stripe v-loading="loadingSup" highlight-current-row @current-change="onSup" :empty-text="'暂无供应商'">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="category" label="类别" width="90" />
            <el-table-column prop="risk_level" label="风险" width="70" />
            <el-table-column prop="total_emission" label="碳排(tCO₂)" align="right" width="100" />
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button link type="primary" @click="openSup(row)">编辑</el-button>
                <el-button link type="danger" @click="removeSup(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="13">
        <el-card class="panel">
          <template #header>
            <span class="panel__title">碳数据{{ currentSup ? ` · ${currentSup.name}` : '' }}</span>
            <el-button style="float:right" type="primary" size="small" :disabled="!currentSup" @click="carbonVisible = true">录入碳数据</el-button>
          </template>
          <el-table :data="carbonData" border stripe v-loading="loadingCarbon" :empty-text="currentSup ? '暂无碳数据' : '请先选择供应商'">
            <el-table-column prop="year" label="年" width="70" />
            <el-table-column prop="material_name" label="材料" />
            <el-table-column prop="quantity" label="数量" align="right" />
            <el-table-column prop="unit" label="单位" width="70" />
            <el-table-column prop="emission_factor" label="因子" align="right" width="90" />
            <el-table-column prop="emission" label="碳排(tCO₂)" align="right" />
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ row }"><el-button link type="danger" @click="removeCarbon(row)">删除</el-button></template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="supVisible" :title="supEditing ? '编辑供应商' : '新增供应商'" width="440px">
      <el-form :model="supForm" label-width="90px">
        <el-form-item label="名称"><el-input v-model="supForm.name" /></el-form-item>
        <el-form-item label="信用代码"><el-input v-model="supForm.credit_code" /></el-form-item>
        <el-form-item label="类别"><el-input v-model="supForm.category" /></el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="supForm.risk_level" style="width:100%"><el-option label="低" value="低" /><el-option label="中" value="中" /><el-option label="高" value="高" /></el-select>
        </el-form-item>
        <el-form-item label="地址"><el-input v-model="supForm.address" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="supVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSup">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="carbonVisible" title="录入碳数据" width="440px">
      <el-form :model="carbonForm" label-width="90px">
        <el-form-item label="年份"><el-input v-model.number="carbonForm.year" type="number" /></el-form-item>
        <el-form-item label="材料名称"><el-input v-model="carbonForm.material_name" /></el-form-item>
        <el-form-item label="数量"><el-input v-model.number="carbonForm.quantity" type="number" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="carbonForm.unit" /></el-form-item>
        <el-form-item label="排放因子"><el-input v-model.number="carbonForm.emission_factor" type="number" /></el-form-item>
        <el-form-item label="数据来源"><el-input v-model="carbonForm.data_source" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="carbonVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCarbon">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import {
  listSuppliers, createSupplier, updateSupplier, deleteSupplier,
  listSupplierCarbon, createSupplierCarbon, deleteSupplierCarbon
} from '@/api'

const suppliers = ref([]); const loadingSup = ref(false)
const currentSup = ref(null)
const carbonData = ref([]); const loadingCarbon = ref(false)
const supVisible = ref(false); const supEditing = ref(false)
const supForm = reactive({ id: null, name: '', credit_code: '', category: '原材料', risk_level: '中', address: '' })
const carbonVisible = ref(false)
const carbonForm = reactive({ year: new Date().getFullYear(), material_name: '', quantity: 0, unit: '', emission_factor: 0, data_source: '供应商申报' })

async function loadSuppliers() {
  loadingSup.value = true
  try { const res = await listSuppliers({ page: 1, page_size: 200 }); suppliers.value = res.items || [] } finally { loadingSup.value = false }
}
async function onSup(row) {
  if (!row) return
  currentSup.value = row; await loadCarbon()
}
async function loadCarbon() {
  if (!currentSup.value) return
  loadingCarbon.value = true
  try { const res = await listSupplierCarbon({ page: 1, page_size: 200, supplier_id: currentSup.value.id }); carbonData.value = res.items || [] } finally { loadingCarbon.value = false }
}
function openSup(row) { supEditing.value = !!row; Object.assign(supForm, row || { id: null, name: '', credit_code: '', category: '原材料', risk_level: '中', address: '' }); supVisible.value = true }
async function saveSup() {
  if (!supForm.name) return ElMessage.warning('请输入名称')
  if (supEditing.value) await updateSupplier(supForm.id, { ...supForm }); else await createSupplier({ ...supForm })
  ElMessage.success('已保存'); supVisible.value = false; loadSuppliers()
}
async function removeSup(row) {
  await ElMessageBox.confirm(`删除供应商「${row.name}」？`, '提示', { type: 'warning' }).then(async () => { await deleteSupplier(row.id); ElMessage.success('已删除'); loadSuppliers() }).catch(() => {})
}
async function saveCarbon() {
  if (!currentSup.value) return
  await createSupplierCarbon({ supplier_id: currentSup.value.id, ...carbonForm })
  ElMessage.success('已录入'); carbonVisible.value = false; loadCarbon(); loadSuppliers()
}
async function removeCarbon(row) {
  await ElMessageBox.confirm('删除该碳数据？', '提示', { type: 'warning' }).then(async () => { await deleteSupplierCarbon(row.id); ElMessage.success('已删除'); loadCarbon(); loadSuppliers() }).catch(() => {})
}
onMounted(loadSuppliers)
</script>
