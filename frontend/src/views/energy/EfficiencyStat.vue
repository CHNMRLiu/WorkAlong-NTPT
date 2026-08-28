<template>
  <div class="page">
    <PageHeader title="能效统计" subtitle="按周期统计单位产品能耗、单位产值能耗与碳排放强度" />

    <el-card class="panel">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="统计年份">
          <el-select v-model="year" style="width:120px" @change="load">
            <el-option v-for="y in yearOptions" :key="y" :label="y + ' 年'" :value="y" />
          </el-select>
        </el-form-item>
        <el-form-item label="用能单元">
          <el-select v-model="unitId" clearable placeholder="全部单元" style="width:180px" @change="load">
            <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="stat-row">
      <StatCard label="综合能耗" :value="fmt(totalCoal)" unit="kgce" :hint="year + ' 年'" />
      <StatCard label="单位产值能耗" :value="fmt(perValue)" unit="kgce/万元" :hint="year + ' 年'" />
      <StatCard label="单位产品碳排" :value="fmt(perProduct)" unit="tCO₂/单位" :hint="year + ' 年'" />
      <StatCard label="总产量" :value="fmt(totalOutput)" unit="t" :hint="year + ' 年'" />
    </div>

    <ChartCard title="月度单位产品能耗 / 单位产值能耗趋势" :option="trendOption" />

    <el-card class="panel">
      <template #header><span class="panel__title">月度明细</span></template>
      <el-table :data="tableData" border stripe v-loading="loading" :empty-text="'暂无数据'">
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="period" label="月份" width="120" />
        <el-table-column prop="standard_coal" label="标煤(kgce)" align="right">
          <template #default="{ row }">{{ fmt(row.standard_coal) }}</template>
        </el-table-column>
        <el-table-column prop="output" label="产量(t)" align="right">
          <template #default="{ row }">{{ fmt(row.output) }}</template>
        </el-table-column>
        <el-table-column label="单位产品能耗(kgce/t)" align="right">
          <template #default="{ row }">{{ row.output ? fmt(row.standard_coal / row.output) : '—' }}</template>
        </el-table-column>
        <el-table-column label="单位产值能耗(kgce/万元)" align="right">
          <template #default="{ row }">{{ row.output_value ? fmt(row.standard_coal / (row.output_value / 10000)) : '—' }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import { getUnitStat, listProduction, listEnergyUnits } from '@/api'

const year = ref(new Date().getFullYear())
const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - i)
const unitId = ref(null)
const units = ref([])
const loading = ref(false)
const stat = ref({ items: [] })
const production = ref([])

function fmt(v, d = 2) {
  if (v === null || v === undefined || isNaN(v)) return '0'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d })
}
function range() {
  return { start: `${year.value}-01-01T00:00:00`, end: `${year.value}-12-31T23:59:59` }
}

async function load() {
  loading.value = true
  try {
    const r = range()
    const [s, p] = await Promise.all([
      getUnitStat({ period: 'month', unit_id: unitId.value || undefined, start: r.start, end: r.end }),
      listProduction({ start: r.start, end: r.end })
    ])
    stat.value = s || { items: [] }
    production.value = p.items || []
  } finally {
    loading.value = false
  }
}

const merged = computed(() => {
  const prodMap = {}
  for (const it of production.value) {
    const k = (it.stat_date || '').slice(0, 7)
    const m = prodMap[k] || { output: 0, output_value: 0 }
    m.output += Number(it.output || 0)
    m.output_value += Number(it.output_value || 0)
    prodMap[k] = m
  }
  return (stat.value.items || []).map(it => ({
    period: it.period,
    standard_coal: it.standard_coal || 0,
    carbon: it.carbon_emission || 0,
    output: prodMap[it.period]?.output || 0,
    output_value: prodMap[it.period]?.output_value || 0
  }))
})

const totalCoal = computed(() => merged.value.reduce((s, x) => s + x.standard_coal, 0))
const totalOutput = computed(() => merged.value.reduce((s, x) => s + x.output, 0))
const totalValue = computed(() => merged.value.reduce((s, x) => s + x.output_value, 0))
const perValue = computed(() => totalValue.value ? totalCoal.value / (totalValue.value / 10000) : 0)
const perProduct = computed(() => {
  const totalCarbon = merged.value.reduce((s, x) => s + x.carbon, 0)
  return totalOutput.value ? (totalCarbon / 1000) / totalOutput.value : 0
})

const tableData = computed(() => merged.value)

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['单位产品能耗(kgce/t)', '单位产值能耗(kgce/万元)'] },
  grid: { left: 60, right: 60, top: 50, bottom: 40 },
  xAxis: { type: 'category', data: merged.value.map(x => x.period) },
  yAxis: [
    { type: 'value', name: 'kgce/t' },
    { type: 'value', name: 'kgce/万元' }
  ],
  series: [
    { name: '单位产品能耗(kgce/t)', type: 'bar', data: merged.value.map(x => x.output ? +(x.standard_coal / x.output).toFixed(2) : 0) },
    { name: '单位产值能耗(kgce/万元)', type: 'line', yAxisIndex: 1, data: merged.value.map(x => x.output_value ? +(x.standard_coal / (x.output_value / 10000)).toFixed(2) : 0) }
  ]
}))

onMounted(async () => {
  units.value = await listEnergyUnits()
  await load()
})
</script>
