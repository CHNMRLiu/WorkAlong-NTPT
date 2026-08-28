<template>
  <div class="page">
    <PageHeader title="用能预算" subtitle="按能源类型设定年度/月度用能预算，跟踪实际消耗" />

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
        <el-table-column label="能源类型" width="120"><template #default="{ row }">{{ etName(row.energy_type_id) }}</template></el-table-column>
        <el-table-column label="单元" width="120"><template #default="{ row }">{{ unitName(row.unit_id) }}</template></el-table-column>
        <el-table-column prop="source_type" label="来源" width="100" />
        <el-table-column prop="budget_value" label="预算量" align="right" />
        <el-table-column prop="actual_value" label="实际量" align="right" />
        <el-table-column label="执行率" align="right" width="100">
          <template #default="{ row }">{{ row.budget_value ? fmt(row.actual_value / row.budget_value * 100) + '%' : '—' }}</template>
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
        <el-form-item label="能源类型" prop="energy_type_id">
          <el-select v-model="form.energy_type_id" style="width:100%">
            <el-option v-for="e in energyTypes" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="单元">
          <el-select v-model="form.unit_id" clearable placeholder="全部" style="width:100%">
            <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源类型">
          <el-select v-model="form.source_type" style="width:100%">
            <el-option label="手工填写" value="手工填写" /><el-option label="能效指标" value="能效指标" /><el-option label="能效测评" value="能效测评" />
          </el-select>
        </el-form-item>
        <el-form-item label="预算量"><el-input v-model.number="form.budget_value" type="number" /></el-form-item>
        <el-form-item label="实际量"><el-input v-model.number="form.actual_value" type="number" /></el-form-item>
        <el-form-item label="单耗"><el-input v-model.number="form.unit_consumption" type="number" /></el-form-item>
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
import { listEnergyBudgets, createEnergyBudget, updateEnergyBudget, deleteEnergyBudget, listEnergyTypes, listEnergyUnits } from '@/api'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(50); const loading = ref(false)
const year = ref(new Date().getFullYear()); const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - i)
const energyTypes = ref([]); const units = ref([])
const etMap = ref({}); const unitMap = ref({})
const visible = ref(false); const editing = ref(false); const saving = ref(false); const formRef = ref(null)
const form = reactive({ id: null, year: new Date().getFullYear(), month: null, energy_type_id: null, unit_id: null, source_type: '手工填写', budget_value: 0, actual_value: 0, unit_consumption: 0, planned_output: 0 })
const rules = { year: [{ required: true, message: '请输入年份', trigger: 'blur' }], energy_type_id: [{ required: true, message: '请选择能源类型', trigger: 'change' }] }

const etName = (id) => etMap.value[id] || `能源#${id}`
const unitName = (id) => id ? (unitMap.value[id] || `单元#${id}`) : '全部'

function fmt(v, d = 2) { if (v == null || isNaN(v)) return '0'; return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d }) }

async function load() {
  loading.value = true
  try {
    const res = await listEnergyBudgets({ page: page.value, page_size: pageSize.value, year: year.value })
    list.value = res.items || []; total.value = res.total || 0
  } finally { loading.value = false }
}
function openAdd() { editing.value = false; Object.assign(form, { id: null, year: year.value, month: null, energy_type_id: null, unit_id: null, source_type: '手工填写', budget_value: 0, actual_value: 0, unit_consumption: 0, planned_output: 0 }); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const f = { ...form }; if (!f.month) f.month = null
      if (editing.value) await updateEnergyBudget(f.id, f); else await createEnergyBudget(f)
      ElMessage.success('已保存'); visible.value = false; load()
    } finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm('删除该预算？', '提示', { type: 'warning' }).then(async () => { await deleteEnergyBudget(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(async () => {
  const [e, u] = await Promise.all([listEnergyTypes(), listEnergyUnits()])
  energyTypes.value = e.items || e; units.value = u.items || u
  etMap.value = Object.fromEntries(energyTypes.value.map(x => [x.id, x.name]))
  unitMap.value = Object.fromEntries(units.value.map(x => [x.id, x.name]))
  load()
})
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; } .filter-bar { display: flex; gap: 12px; margin-bottom: 14px; }</style>
