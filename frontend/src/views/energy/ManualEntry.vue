<template>
  <div class="page">
    <PageHeader title="录接数据" subtitle="手工录入表计读数与能源消耗数据，系统自动折算费用 / 标准煤 / 碳排放" />

    <el-tabs v-model="activeTab" class="apple-tabs">
      <!-- ========== 表计读数 ========== -->
      <el-tab-pane label="表计读数" name="reading">
        <div class="filter-bar">
          <el-select v-model="readingFilter.meter_id" placeholder="选择表计" clearable filterable style="width:220px"
                     @change="loadReadings">
            <el-option v-for="m in meters" :key="m.id" :label="`${m.name}（${m.code}）`" :value="m.id" />
          </el-select>
          <el-date-picker v-model="readingFilter.start" type="date" placeholder="起始日期" value-format="YYYY-MM-DD"
                          style="width:160px" @change="loadReadings" />
          <el-date-picker v-model="readingFilter.end" type="date" placeholder="结束日期" value-format="YYYY-MM-DD"
                          style="width:160px" @change="loadReadings" />
          <el-button type="primary" @click="openReadingDialog()">新增读数</el-button>
        </div>

        <el-table :data="readings" v-loading="readingLoading" border stripe class="apple-table">
          <el-table-column type="index" label="#" width="55" align="center" />
          <el-table-column prop="reading_time" label="读数时间" min-width="160" />
          <el-table-column label="表计" min-width="160">
            <template #default="{ row }">{{ meterName(row.meter_id) }}</template>
          </el-table-column>
          <el-table-column prop="last_reading" label="上期读数" width="110" align="right" />
          <el-table-column prop="current_reading" label="本期读数" width="110" align="right" />
          <el-table-column prop="consumption" label="消耗量" width="120" align="right">
            <template #default="{ row }">{{ fmt(row.consumption) }}</template>
          </el-table-column>
          <el-table-column prop="cost" label="费用(元)" width="120" align="right">
            <template #default="{ row }">{{ fmt(row.cost) }}</template>
          </el-table-column>
          <el-table-column prop="standard_coal" label="标准煤(t)" width="120" align="right">
            <template #default="{ row }">{{ fmt(row.standard_coal) }}</template>
          </el-table-column>
          <el-table-column prop="carbon_emission" label="碳排放(tCO₂)" width="130" align="right">
            <template #default="{ row }">{{ fmt(row.carbon_emission) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openReadingDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="removeReading(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="readingPage" :page-size="readingPageSize" :total="readingTotal"
                       layout="total, prev, pager, next" class="apple-pager" @current-change="loadReadings" />
      </el-tab-pane>

      <!-- ========== 手工录入 ========== -->
      <el-tab-pane label="手工录入" name="manual">
        <div class="filter-bar">
          <el-select v-model="manualFilter.unit_id" placeholder="选择用能单元" clearable filterable style="width:200px"
                     @change="loadManuals">
            <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
          <el-date-picker v-model="manualFilter.start" type="date" placeholder="起始" value-format="YYYY-MM-DD"
                          style="width:150px" @change="loadManuals" />
          <el-date-picker v-model="manualFilter.end" type="date" placeholder="结束" value-format="YYYY-MM-DD"
                          style="width:150px" @change="loadManuals" />
          <el-button type="primary" @click="openManualDialog()">新增录入</el-button>
        </div>

        <el-table :data="manuals" v-loading="manualLoading" border stripe class="apple-table">
          <el-table-column type="index" label="#" width="55" align="center" />
          <el-table-column prop="entry_date" label="录入日期" min-width="160" />
          <el-table-column label="能源类型" min-width="120">
            <template #default="{ row }">{{ energyName(row.energy_type_id) }}</template>
          </el-table-column>
          <el-table-column label="用能单元" min-width="140">
            <template #default="{ row }">{{ unitName(row.unit_id) }}</template>
          </el-table-column>
          <el-table-column prop="consumption" label="消耗量" width="120" align="right">
            <template #default="{ row }">{{ fmt(row.consumption) }}</template>
          </el-table-column>
          <el-table-column prop="cost" label="费用(元)" width="120" align="right">
            <template #default="{ row }">{{ fmt(row.cost) }}</template>
          </el-table-column>
          <el-table-column prop="standard_coal" label="标准煤(t)" width="120" align="right">
            <template #default="{ row }">{{ fmt(row.standard_coal) }}</template>
          </el-table-column>
          <el-table-column prop="carbon_emission" label="碳排放(tCO₂)" width="130" align="right">
            <template #default="{ row }">{{ fmt(row.carbon_emission) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openManualDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="removeManual(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="manualPage" :page-size="manualPageSize" :total="manualTotal"
                       layout="total, prev, pager, next" class="apple-pager" @current-change="loadManuals" />
      </el-tab-pane>
    </el-tabs>

    <!-- 表计读数弹窗 -->
    <el-dialog v-model="readingVisible" :title="readingForm.id ? '编辑读数' : '新增读数'" width="480px" append-to-body>
      <el-form ref="readingRef" :model="readingForm" :rules="readingRules" label-width="92px">
        <el-form-item label="表计" prop="meter_id">
          <el-select v-model="readingForm.meter_id" placeholder="选择表计" filterable style="width:100%">
            <el-option v-for="m in meters" :key="m.id" :label="`${m.name}（${m.code}）`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="读数时间" prop="reading_time">
          <el-date-picker v-model="readingForm.reading_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="上期读数" prop="last_reading">
          <el-input-number v-model="readingForm.last_reading" :precision="2" :step="1" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="本期读数" prop="current_reading">
          <el-input-number v-model="readingForm.current_reading" :precision="2" :step="1" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="单价(元)" prop="unit_price">
          <el-input-number v-model="readingForm.unit_price" :precision="2" :min="0" :step="0.1" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="记录人">
          <el-input v-model="readingForm.recorder" placeholder="选填" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="readingForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="readingVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitReading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 手工录入弹窗 -->
    <el-dialog v-model="manualVisible" :title="manualForm.id ? '编辑录入' : '新增录入'" width="480px" append-to-body>
      <el-form ref="manualRef" :model="manualForm" :rules="manualRules" label-width="92px">
        <el-form-item label="能源类型" prop="energy_type_id">
          <el-select v-model="manualForm.energy_type_id" placeholder="选择能源类型" filterable style="width:100%">
            <el-option v-for="e in energyTypes" :key="e.id" :label="`${e.name}（${e.unit}）`" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用能单元" prop="unit_id">
          <el-select v-model="manualForm.unit_id" placeholder="选择单元" filterable style="width:100%">
            <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联表计">
          <el-select v-model="manualForm.meter_id" placeholder="选填" filterable clearable style="width:100%">
            <el-option v-for="m in meters" :key="m.id" :label="`${m.name}（${m.code}）`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="录入日期" prop="entry_date">
          <el-date-picker v-model="manualForm.entry_date" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="消耗量" prop="consumption">
          <el-input-number v-model="manualForm.consumption" :precision="4" :min="0" :step="1" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="单价(元)">
          <el-input-number v-model="manualForm.unit_price" :precision="2" :min="0" :step="0.1" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="数据来源">
          <el-input v-model="manualForm.data_source" placeholder="如：手工录入" />
        </el-form-item>
        <el-form-item label="记录人">
          <el-input v-model="manualForm.recorder" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="manualForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="manualVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitManual">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import {
  listMeters, listEnergyTypes, listEnergyUnits,
  listMeterReadings, createMeterReading, updateMeterReading, deleteMeterReading,
  listManualEntries, createManualEntry, updateManualEntry, deleteManualEntry
} from '@/api'

const fmt = (v) => (v == null ? '0' : Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 4 }))

const activeTab = ref('reading')

// 基础下拉
const meters = ref([])
const energyTypes = ref([])
const units = ref([])
const meterMap = ref({})
const energyMap = ref({})
const unitMap = ref({})
const meterName = (id) => meterMap.value[id] || `表计#${id}`
const energyName = (id) => energyMap.value[id] || `能源#${id}`
const unitName = (id) => unitMap.value[id] || `单元#${id}`

async function loadBasics() {
  const [m, e, u] = await Promise.all([listMeters(), listEnergyTypes(), listEnergyUnits()])
  meters.value = m.items || m || []
  energyTypes.value = e.items || e || []
  units.value = u.items || u || []
  meterMap.value = Object.fromEntries(meters.value.map(x => [x.id, `${x.name}（${x.code}）`]))
  energyMap.value = Object.fromEntries(energyTypes.value.map(x => [x.id, x.name]))
  unitMap.value = Object.fromEntries(units.value.map(x => [x.id, x.name]))
}

// ============ 表计读数 ============
const readings = ref([])
const readingLoading = ref(false)
const readingPage = ref(1)
const readingPageSize = ref(50)
const readingTotal = ref(0)
const readingFilter = reactive({ meter_id: null, start: '', end: '' })

async function loadReadings() {
  readingLoading.value = true
  try {
    const res = await listMeterReadings({
      page: readingPage.value, page_size: readingPageSize.value,
      meter_id: readingFilter.meter_id || undefined,
      start: readingFilter.start || undefined, end: readingFilter.end || undefined
    })
    readings.value = res.items || []
    readingTotal.value = res.total || 0
  } finally { readingLoading.value = false }
}

const readingVisible = ref(false)
const saving = ref(false)
const readingRef = ref(null)
const readingForm = ref({ id: null, meter_id: null, reading_time: '', last_reading: 0, current_reading: 0, unit_price: 0, recorder: '', remark: '' })
const readingRules = {
  meter_id: [{ required: true, message: '请选择表计', trigger: 'change' }],
  reading_time: [{ required: true, message: '请选择读数时间', trigger: 'change' }],
  current_reading: [{ required: true, message: '请输入本期读数', trigger: 'blur' }]
}

function openReadingDialog(row) {
  readingForm.value = row
    ? { ...row }
    : { id: null, meter_id: null, reading_time: '', last_reading: 0, current_reading: 0, unit_price: 0, recorder: '', remark: '' }
  readingVisible.value = true
}

async function submitReading() {
  await readingRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const f = { ...readingForm.value }
      if (f.id) { await updateMeterReading(f.id, f) } else { await createMeterReading(f) }
      ElMessage.success('已保存')
      readingVisible.value = false
      loadReadings()
    } finally { saving.value = false }
  })
}

async function removeReading(row) {
  await ElMessageBox.confirm('确定删除该读数记录？', '提示', { type: 'warning' })
  await deleteMeterReading(row.id); ElMessage.success('已删除'); loadReadings()
}

// ============ 手工录入 ============
const manuals = ref([])
const manualLoading = ref(false)
const manualPage = ref(1)
const manualPageSize = ref(50)
const manualTotal = ref(0)
const manualFilter = reactive({ unit_id: null, start: '', end: '' })

async function loadManuals() {
  manualLoading.value = true
  try {
    const res = await listManualEntries({
      page: manualPage.value, page_size: manualPageSize.value,
      unit_id: manualFilter.unit_id || undefined,
      start: manualFilter.start || undefined, end: manualFilter.end || undefined
    })
    manuals.value = res.items || []
    manualTotal.value = res.total || 0
  } finally { manualLoading.value = false }
}

const manualVisible = ref(false)
const manualRef = ref(null)
const manualForm = ref({ id: null, energy_type_id: null, unit_id: null, meter_id: null, entry_date: '', consumption: 0, unit_price: 0, data_source: '手工录入', recorder: '', remark: '' })
const manualRules = {
  energy_type_id: [{ required: true, message: '请选择能源类型', trigger: 'change' }],
  unit_id: [{ required: true, message: '请选择用能单元', trigger: 'change' }],
  entry_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  consumption: [{ required: true, message: '请输入消耗量', trigger: 'blur' }]
}

function openManualDialog(row) {
  manualForm.value = row
    ? { ...row }
    : { id: null, energy_type_id: null, unit_id: null, meter_id: null, entry_date: '', consumption: 0, unit_price: 0, data_source: '手工录入', recorder: '', remark: '' }
  manualVisible.value = true
}

async function submitManual() {
  await manualRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const f = { ...manualForm.value }
      if (f.id) { await updateManualEntry(f.id, f) } else { await createManualEntry(f) }
      ElMessage.success('已保存')
      manualVisible.value = false
      loadManuals()
    } finally { saving.value = false }
  })
}

async function removeManual(row) {
  await ElMessageBox.confirm('确定删除该录入记录？', '提示', { type: 'warning' })
  await deleteManualEntry(row.id); ElMessage.success('已删除'); loadManuals()
}

onMounted(() => { loadBasics(); loadReadings(); loadManuals() })
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
.apple-tabs :deep(.el-tabs__header) { margin-bottom: 18px; }
.apple-tabs :deep(.el-tabs__item.is-active) { color: var(--c-brand); font-weight: 600; }
.apple-tabs :deep(.el-tabs__active-bar) { background: var(--c-brand); }
.apple-table { border-radius: 12px; overflow: hidden; box-shadow: var(--c-shadow-card); }
.apple-pager { margin-top: 16px; justify-content: flex-end; }
</style>
