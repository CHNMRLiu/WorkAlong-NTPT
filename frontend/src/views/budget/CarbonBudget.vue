<template>
  <div class="page">
    <PageHeader title="碳排放预算" subtitle="按产值强度 / 产品强度设定碳排放预算，跟踪实际碳排" />

    <el-card class="panel">
      <div class="filter-bar">
        <el-select v-model="year" placeholder="年份" style="width:120px" @change="load">
          <el-option v-for="y in yearOptions" :key="y" :label="y + ' 年'" :value="y" />
        </el-select>
        <el-button type="primary" @click="openAdd">新增预算</el-button>
      </div>
      <el-table :data="list" border stripe v-loading="loading" :empty-text="'暂无预算'">
        <el-table-column prop="year" label="年份" width="80" />
        <el-table-column prop="month" label="月份" width="70" />
        <el-table-column label="单元" width="120"><template #default="{ row }">{{ unitName(row.unit_id) }}</template></el-table-column>
        <el-table-column prop="intensity_type" label="强度类型" width="110" />
        <el-table-column prop="budget_carbon" label="预算碳排" align="right" />
        <el-table-column prop="actual_carbon" label="实际碳排" align="right" />
        <el-table-column prop="carbon_intensity" label="碳强度" align="right" />
        <el-table-column label="执行率" align="right" width="100">
          <template #default="{ row }">{{ row.budget_carbon ? fmt(row.actual_carbon / row.budget_carbon * 100) + '%' : '—' }}</template>
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

    <el-dialog v-model="visible" :title="editing ? '编辑预算' : '新增预算'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="年份" prop="year"><el-input v-model.number="form.year" type="number" /></el-form-item>
        <el-form-item label="月份"><el-input v-model.number="form.month" type="number" placeholder="留空表示年度" /></el-form-item>
        <el-form-item label="单元">
          <el-select v-model="form.unit_id" clearable placeholder="全部" style="width:100%">
            <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="强度类型">
          <el-select v-model="form.intensity_type" style="width:100%">
            <el-option label="产值强度" value="产值强度" /><el-option label="产品强度" value="产品强度" /><el-option label="手工填写" value="手工填写" />
          </el-select>
        </el-form-item>
        <el-form-item label="预算碳排"><el-input v-model.number="form.budget_carbon" type="number" /></el-form-item>
        <el-form-item label="实际碳排"><el-input v-model.number="form.actual_carbon" type="number" /></el-form-item>
        <el-form-item label="碳强度"><el-input v-model.number="form.carbon_intensity" type="number" /></el-form-item>
        <el-form-item label="计划产量"><el-input v-model.number="form.planned_output" type="number" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import { listCarbonBudgets, createCarbonBudget, updateCarbonBudget, deleteCarbonBudget, listEnergyUnits } from '@/api'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(50); const loading = ref(false)
const year = ref(new Date().getFullYear()); const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - i)
const units = ref([]); const unitMap = ref({})
const visible = ref(false); const editing = ref(false); const saving = ref(false); const formRef = ref(null)
const form = reactive({ id: null, year: new Date().getFullYear(), month: null, unit_id: null, intensity_type: '产值强度', budget_carbon: 0, actual_carbon: 0, carbon_intensity: 0, planned_output: 0 })
const rules = { year: [{ required: true, message: '请输入年份', trigger: 'blur' }] }

const unitName = (id) => id ? (unitMap.value[id] || `单元#${id}`) : '全部'
function fmt(v, d = 2) { if (v == null || isNaN(v)) return '0'; return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d }) }

async function load() {
  loading.value = true
  try {
    const res = await listCarbonBudgets({ page: page.value, page_size: pageSize.value, year: year.value })
    list.value = res.items || []; total.value = res.total || 0
  } finally { loading.value = false }
}
function openAdd() { editing.value = false; Object.assign(form, { id: null, year: year.value, month: null, unit_id: null, intensity_type: '产值强度', budget_carbon: 0, actual_carbon: 0, carbon_intensity: 0, planned_output: 0 }); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const f = { ...form }; if (!f.month) f.month = null
      if (editing.value) await updateCarbonBudget(f.id, f); else await createCarbonBudget(f)
      ElMessage.success('已保存'); visible.value = false; load()
    } finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm('删除该预算？', '提示', { type: 'warning' }).then(async () => { await deleteCarbonBudget(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(async () => {
  const u = await listEnergyUnits(); units.value = u.items || u
  unitMap.value = Object.fromEntries(units.value.map(x => [x.id, x.name]))
  load()
})
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; } .filter-bar { display: flex; gap: 12px; margin-bottom: 14px; }</style>
