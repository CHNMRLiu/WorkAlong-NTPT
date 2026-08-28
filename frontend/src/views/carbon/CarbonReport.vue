<template>
  <div class="page">
    <PageHeader title="碳排报告" subtitle="汇总年度碳核算，生成碳排放核算报告（总量/范围/强度/明细）" />

    <el-card class="panel">
      <div class="filter-bar">
        <el-select v-model="year" placeholder="年份" style="width:120px" @change="selectYear">
          <el-option v-for="y in yearOptions" :key="y" :label="y + ' 年'" :value="y" />
        </el-select>
        <el-button type="primary" @click="genVisible = true">生成 / 更新报告</el-button>
      </div>

      <div v-if="report" class="report">
        <div class="stat-row">
          <StatCard label="排放总量" :value="fmt(report.total_emission)" unit="tCO₂" />
          <StatCard label="范围1" :value="fmt(report.scope1)" unit="tCO₂" />
          <StatCard label="范围2" :value="fmt(report.scope2)" unit="tCO₂" />
          <StatCard label="范围3" :value="fmt(report.scope3)" unit="tCO₂" />
        </div>
        <div class="stat-row">
          <StatCard label="产值强度(tCO₂/万元)" :value="fmt(report.intensity_value, 4)" />
          <StatCard label="产品强度(tCO₂/单位)" :value="fmt(report.product_intensity, 4)" />
          <StatCard label="状态" :value="report.status || '—'" />
          <StatCard label="报告日期" :value="report.report_date || '—'" />
        </div>

        <el-card class="panel" style="margin-top:16px">
          <template #header><span class="panel__title">排放明细（按排放源）</span></template>
          <el-table :data="sources" border stripe :empty-text="'暂无明细'">
            <el-table-column prop="source_name" label="排放源" />
            <el-table-column prop="scope" label="范围" width="90" />
            <el-table-column prop="activity_data" label="活动数据" align="right" />
            <el-table-column prop="unit" label="单位" width="80" />
            <el-table-column prop="emission_factor" label="因子" align="right" width="100" />
            <el-table-column prop="emission" label="排放量(tCO₂)" align="right" />
          </el-table>
        </el-card>

        <el-card class="panel" style="margin-top:16px">
          <template #header><span class="panel__title">减排措施与计划</span></template>
          <el-form label-width="90px">
            <el-form-item label="减排措施">
              <el-input v-model="measures" type="textarea" :rows="3" @change="updateText" />
            </el-form-item>
            <el-form-item label="下一步计划">
              <el-input v-model="nextPlan" type="textarea" :rows="3" @change="updateText" />
            </el-form-item>
          </el-form>
        </el-card>
      </div>
      <el-empty v-else description="该年度暂无报告，请点击「生成 / 更新报告」" />
    </el-card>

    <el-dialog v-model="genVisible" title="生成年度碳报告" width="460px">
      <el-form :model="genForm" label-width="90px">
        <el-form-item label="年份"><el-input v-model.number="genForm.year" type="number" /></el-form-item>
        <el-form-item label="报告日期"><el-date-picker v-model="genForm.report_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="减排措施"><el-input v-model="genForm.measures" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="下一步计划"><el-input v-model="genForm.next_plan" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="genVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="generate">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { listReports, generateReport, updateReport } from '@/api'

const year = ref(new Date().getFullYear()); const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - i)
const report = ref(null); const sources = ref([])
const measures = ref(''); const nextPlan = ref('')
const genVisible = ref(false); const saving = ref(false)
const genForm = reactive({ year: new Date().getFullYear(), report_date: '', measures: '', next_plan: '' })

function fmt(v, d = 2) { if (v == null || isNaN(v)) return '0'; return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d }) }

async function selectYear() {
  const reports = await listReports()
  const list = Array.isArray(reports) ? reports : (reports.list || reports.items || [])
  const r = list.find(x => x.year === year.value)
  if (r) { report.value = r; sources.value = []; measures.value = r.measures || ''; nextPlan.value = r.next_plan || '' }
  else { report.value = null; sources.value = [] }
}
async function generate() {
  saving.value = true
  try {
    genForm.year = year.value
    const res = await generateReport({ ...genForm })
    report.value = res.report; sources.value = res.sources || []
    measures.value = report.value.measures || ''; nextPlan.value = report.value.next_plan || ''
    ElMessage.success('报告已生成'); genVisible.value = false
  } finally { saving.value = false }
}
async function updateText() {
  if (!report.value) return
  try { await updateReport(report.value.id, { measures: measures.value, next_plan: nextPlan.value }); ElMessage.success('已保存') } catch (e) {}
}
onMounted(selectYear)
</script>
<style scoped>.filter-bar { display: flex; gap: 12px; margin-bottom: 14px; }</style>
