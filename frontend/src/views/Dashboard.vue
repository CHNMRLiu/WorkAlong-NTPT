<template>
  <div class="page">
    <PageHeader :title="`${orgName} · 能碳看板`" :subtitle="`${year} 年度概览`" />

    <div class="dash-cards">
      <div class="dash-card" @click="go('carbon-statistics')"><StatCard label="总碳排放" :value="fmt(summary.total_carbon, 2)" unit="tCO₂e" /></div>
      <div class="dash-card" @click="go('energy-comprehensive')"><StatCard label="综合能耗(标煤)" :value="fmt(summary.total_standard_coal, 2)" unit="kgce" /></div>
      <div class="dash-card" @click="go('energy-meter-query')"><StatCard label="总能耗" :value="fmt(summary.total_consumption, 2)" unit="" /></div>
      <div class="dash-card" @click="go('energy-comprehensive')"><StatCard label="总能源费用" :value="fmt(summary.total_cost, 2)" unit="元" /></div>
    </div>

    <div class="dash-cards dash-cards--sm">
      <div class="dash-card" @click="go('carbon-report')"><StatCard label="碳排放产值强度" :value="fmt(summary.carbon_intensity_value, 4)" unit="tCO₂e/万元" /></div>
      <div class="dash-card" @click="go('energy-efficiency')"><StatCard label="单位产值能耗" :value="fmt(summary.energy_per_value, 4)" unit="kgce/万元" /></div>
      <div class="dash-card" @click="go('energy-production')"><StatCard label="总产量" :value="fmt(summary.total_output, 2)" /></div>
      <div class="dash-card" @click="go('energy-production')"><StatCard label="总产值" :value="fmt(summary.total_output_value, 2)" unit="元" /></div>
    </div>

    <el-row :gutter="16">
      <el-col :span="12">
        <ChartCard title="碳排放月度趋势" :option="trendOption" :height="320" />
      </el-col>
      <el-col :span="12">
        <ChartCard title="能源消费结构" :option="structureOption" :height="320" />
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <ChartCard title="碳排放范围占比" :option="scopeOption" :height="300" />
      </el-col>
      <el-col :span="12">
        <ChartCard title="用能单元能耗排行" :option="rankOption" :height="300" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import { getDashboardSummary, getCarbonTrend, getEnergyStructure, getUnitRanking, getScopeBreakdown } from '@/api'

const router = useRouter()
function go(name) { router.push({ name }) }

const year = new Date().getFullYear()
const orgName = ref('')
const summary = ref({
  total_carbon: 0, total_standard_coal: 0, total_consumption: 0, total_cost: 0,
  carbon_intensity_value: 0, energy_per_value: 0, total_output: 0, total_output_value: 0
})
const trend = ref([])
const structure = ref([])
const ranking = ref([])
const scope = ref([])

function fmt(v, d = 2) {
  const n = Number(v || 0)
  return n.toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d })
}

const basePalette = ['#0071E3', '#34C759', '#FF9500', '#AF52DE', '#FF2D55', '#5AC8FA', '#FFCC00', '#FF3B30']

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: trend.value.map(t => t.month), axisLine: { lineStyle: { color: '#D2D2D7' } }, axisLabel: { color: '#6E6E73' } },
  yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#E8E8ED' } }, axisLabel: { color: '#6E6E73' } },
  series: [{
    type: 'line', smooth: true, data: trend.value.map(t => t.emission),
    lineStyle: { width: 2, color: '#0071E3' }, itemStyle: { color: '#0071E3' },
    areaStyle: { color: 'rgba(0,113,227,0.08)' }
  }]
}))

const structureOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#6E6E73' } },
  series: [{
    type: 'pie', radius: ['45%', '70%'], avoidLabelOverlap: true,
    label: { show: false }, labelLine: { show: false },
    data: structure.value.map((s, i) => ({ name: s.name, value: s.value, itemStyle: { color: basePalette[i % basePalette.length] } }))
  }]
}))

const scopeOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#6E6E73' } },
  series: [{
    type: 'pie', radius: ['45%', '70%'],
    data: scope.value.map((s, i) => ({ name: s.name, value: s.value, itemStyle: { color: basePalette[i % basePalette.length] } }))
  }]
}))

const rankOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#E8E8ED' } }, axisLabel: { color: '#6E6E73' } },
  yAxis: { type: 'category', data: ranking.value.map(r => r.name).reverse(), axisLine: { lineStyle: { color: '#D2D2D7' } }, axisLabel: { color: '#6E6E73' } },
  series: [{
    type: 'bar', data: ranking.value.map(r => r.value).reverse(), barWidth: '40%',
    itemStyle: { color: '#0071E3', borderRadius: [0, 4, 4, 0] }
  }]
}))

onMounted(async () => {
  try {
    const s = await getDashboardSummary({ year })
    summary.value = s
    orgName.value = s.org_name
    trend.value = await getCarbonTrend({ year })
    structure.value = await getEnergyStructure({ year })
    ranking.value = await getUnitRanking({ year, dimension: 'carbon' })
    scope.value = await getScopeBreakdown({ year })
  } catch (e) {}
})
</script>

<style scoped>
.dash-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.dash-cards--sm { grid-template-columns: repeat(4, 1fr); }
.dash-card { cursor: pointer; transition: transform .12s ease, box-shadow .12s ease; }
.dash-card:hover { transform: translateY(-2px); }
</style>
