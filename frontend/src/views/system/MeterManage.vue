<template>
  <div class="page">
    <PageHeader title="表计管理" subtitle="计量器具台账，绑定能源类型与用能单元">
      <template #actions><el-button type="primary" @click="openAdd">新增表计</el-button></template>
    </PageHeader>
    <div class="app-card">
      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="搜索名称/编码" clearable style="width:220px" @keyup.enter="load" />
        <el-button @click="load">查询</el-button>
      </div>
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="能源类型" width="100">
          <template #default="{ row }">{{ etName(row.energy_type_id) }}</template>
        </el-table-column>
        <el-table-column label="用能单元" width="120">
          <template #default="{ row }">{{ unitName(row.unit_id) }}</template>
        </el-table-column>
        <el-table-column prop="meter_type" label="类型" width="90" />
        <el-table-column prop="installation_location" label="安装位置" />
        <el-table-column prop="accuracy" label="精度" width="80" />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next"
        :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
    </div>

    <el-dialog v-model="visible" :title="editing ? '编辑表计' : '新增表计'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="编码" prop="code"><el-input v-model="form.code" :disabled="editing" /></el-form-item>
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="能源类型" prop="energy_type_id">
          <el-select v-model="form.energy_type_id" style="width:100%">
            <el-option v-for="e in energyTypes" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用能单元" prop="unit_id">
          <el-select v-model="form.unit_id" style="width:100%">
            <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="表计类型"><el-input v-model="form.meter_type" /></el-form-item>
        <el-form-item label="安装位置"><el-input v-model="form.installation_location" /></el-form-item>
        <el-form-item label="精度"><el-input v-model="form.accuracy" /></el-form-item>
        <el-form-item label="安装日期">
          <el-date-picker v-model="form.install_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
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
import { listMeters, createMeter, updateMeter, deleteMeter, listEnergyTypes, listEnergyUnits } from '@/api'

const list = ref([])
const energyTypes = ref([])
const units = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(100)
const keyword = ref('')
const loading = ref(false)
const visible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref(null)
const form = reactive({ code: '', name: '', energy_type_id: null, unit_id: null, meter_type: '电能表', installation_location: '', accuracy: '', install_date: '', remark: '' })
const rules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  energy_type_id: [{ required: true, message: '请选择能源类型', trigger: 'change' }],
  unit_id: [{ required: true, message: '请选择用能单元', trigger: 'change' }]
}
const etMap = ref({}); const unitMap = ref({})
function etName(id) { return etMap.value[id] || '—' }
function unitName(id) { return unitMap.value[id] || '—' }

async function load() {
  loading.value = true
  try {
    const res = await listMeters({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    list.value = res.items; total.value = res.total
  } catch (e) {} finally { loading.value = false }
}
async function loadMeta() {
  const et = await listEnergyTypes({ page: 1, page_size: 200 })
  energyTypes.value = et.items
  etMap.value = Object.fromEntries(et.items.map(e => [e.id, e.name]))
  const u = await listEnergyUnits({ page: 1, page_size: 200 })
  units.value = u.items
  unitMap.value = Object.fromEntries(u.items.map(x => [x.id, x.name]))
}
function resetForm() { Object.assign(form, { code: '', name: '', energy_type_id: null, unit_id: null, meter_type: '电能表', installation_location: '', accuracy: '', install_date: '', remark: '' }) }
function openAdd() { editing.value = false; resetForm(); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editing.value) await updateMeter(form.id, { ...form, id: undefined })
      else await createMeter(form)
      ElMessage.success('已保存'); visible.value = false; load()
    } catch (e) {} finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' })
    .then(async () => { await deleteMeter(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(() => { loadMeta(); load() })
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; }</style>
