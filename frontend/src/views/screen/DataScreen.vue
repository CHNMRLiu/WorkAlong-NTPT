<template>
  <div class="screen">
    <header class="screen__header">
      <div class="screen__title">能碳管理数据大屏</div>
      <div class="screen__sub">{{ orgName }} · {{ year }} 年度实时监测</div>
      <div class="screen__right">
        <span class="screen__clock">{{ clock }}</span>
        <el-button size="small" @click="refresh">手动刷新</el-button>
        <el-button size="small" @click="$router.push('/dashboard')">返回管理端</el-button>
      </div>
    </header>

    <div class="screen__stats">
      <div class="screen__stat" v-for="s in statCards" :key="s.label">
        <div class="screen__stat-value">{{ s.value }}<span class="screen__stat-unit">{{ s.unit }}</span></div>
        <div class="screen__stat-label">{{ s.label }}</div>
      </div>
    </div>

    <div class="screen__grid">
      <div class="screen__panel">
        <div class="screen__panel-title">碳排放月度趋势</div>
        <div ref="trendEl" class="screen__chart"></div>
      </div>
      <div class="screen__panel">
        <div class="screen__panel-title">能源消费结构</div>
        <div ref="structEl" class="screen__chart"></div>
      </div>
      <div class="screen__panel">
        <div class="screen__panel-title">碳排放范围占比</div>
        <div ref="scopeEl" class="screen__chart"></div>
      </div>
      <div class="screen__panel">
        <div class="screen__panel-title">用能单元碳排放排行</div>
        <div ref="rankEl" class="screen__chart"></div>
      </div>
      <div class="screen__panel screen__panel--wide">
        <div class="screen__panel-title">最新录入数据</div>
        <div class="screen__recent">
          <div class="screen__recent-row screen__recent-head">
            <span>时间</span><span>表计</span><span>能耗</span><span>碳排(tCO₂)</span>
          </div>
          <div v-for="(r, i) in recent" :key="i" class="screen__recent-row" :class="{ 'is-flash': r.carbon > anomalyThreshold }">
            <span>{{ r.time }}</span><span>{{ r.meter }}</span>
            <span>{{ fmt(r.consumption) }}</span><span>{{ fmt(r.carbon, 4) }}</span>
          </div>
          <div v-if="!recent.length" class="screen__empty">暂无录入数据</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDashboardSummary, getCarbonTrend, getEnergyStructure, getUnitRanking, getScopeBreakdown, getRecentEntries } from '@/api'

const year = new Date().getFullYear()
const orgName = ref('')
const clock = ref('')
const anomalyThreshold = 100
const summary = reactive({ total_carbon: 0, total_standard_coal: 0, total_cost: 0, total_consumption: 0, carbon_intensity_value: 0, energy_per_value: 0 })
const trend = ref([])
const structure = ref([])
const ranking = ref([])
const scope = ref([])
const recent = ref([])

const statCards = computed(() => [
  { label: '总碳排放(tCO₂)', value: fmt(summary.total_carbon) },
  { label: '综合能耗(kgce)', value: fmt(summary.total_standard_coal) },
  { label: '总能耗', value: fmt(summary.total_consumption) },
  { label: '能源费用(元)', value: fmt(summary.total_cost) },
  { label: '碳产值强度', value: fmt(summary.carbon_intensity_value, 4) },
  { label: '单位产值能耗', value: fmt(summary.energy_per_value, 4) }
])

function fmt(v, d = 2) { if (v == null || isNaN(v)) return '0'; return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d }) }

// 图表实例
const trendEl = ref(null); const structEl = ref(null); const scopeEl = ref(null); const rankEl = ref(null)
const charts = {}
const palette = ['#0A84FF', '#30D158', '#FFD60A', '#BF5AF2', '#FF375F', '#64D2FF', '#FF9F0A', '#FF453A']

const axisCommon = { axisLine: { lineStyle: { color: 'rgba(255,255,255,0.25)' } }, axisLabel: { color: 'rgba(255,255,255,0.7)' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } } }

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' }, grid: { left: 50, right: 20, top: 30, bottom: 30 },
  xAxis: { type: 'category', data: trend.value.map(t => t.month), ...axisCommon },
  yAxis: { type: 'value', name: 'tCO₂', ...axisCommon },
  series: [{ type: 'line', smooth: true, data: trend.value.map(t => t.emission),
    lineStyle: { width: 2, color: '#0A84FF' }, itemStyle: { color: '#0A84FF' }, areaStyle: { color: 'rgba(10,132,255,0.18)' } }]
}))
const structOption = computed(() => ({
  tooltip: { trigger: 'item' }, legend: { bottom: 0, textStyle: { color: 'rgba(255,255,255,0.7)' } },
  series: [{ type: 'pie', radius: ['42%', '70%'], avoidLabelOverlap: true, label: { color: '#fff' }, labelLine: { lineStyle: { color: 'rgba(255,255,255,0.4)' } },
    data: structure.value.map((s, i) => ({ name: s.name, value: s.value, itemStyle: { color: palette[i % palette.length] } })) }]
}))
const scopeOption = computed(() => ({
  tooltip: { trigger: 'item' }, legend: { bottom: 0, textStyle: { color: 'rgba(255,255,255,0.7)' } },
  series: [{ type: 'pie', radius: ['42%', '70%'],
    data: scope.value.map((s, i) => ({ name: s.name, value: s.value, itemStyle: { color: palette[i % palette.length] } })) }]
}))
const rankOption = computed(() => ({
  tooltip: { trigger: 'axis' }, grid: { left: 90, right: 30, top: 20, bottom: 30 },
  xAxis: { type: 'value', ...axisCommon },
  yAxis: { type: 'category', data: ranking.value.map(r => r.name).reverse(), ...axisCommon },
  series: [{ type: 'bar', data: ranking.value.map(r => r.value).reverse(), barWidth: '45%',
    itemStyle: { color: '#30D158', borderRadius: [0, 4, 4, 0] } }]
}))

function initCharts() {
  charts.trend = echarts.init(trendEl.value); charts.struct = echarts.init(structEl.value)
  charts.scope = echarts.init(scopeEl.value); charts.rank = echarts.init(rankEl.value)
  charts.trend.setOption(trendOption.value)
  charts.struct.setOption(structOption.value)
  charts.scope.setOption(scopeOption.value)
  charts.rank.setOption(rankOption.value)
}
function refreshCharts() {
  charts.trend?.setOption(trendOption.value, true)
  charts.struct?.setOption(structOption.value, true)
  charts.scope?.setOption(scopeOption.value, true)
  charts.rank?.setOption(rankOption.value, true)
}
function onResize() { Object.values(charts).forEach(c => c && c.resize()) }

async function refresh() {
  const [s, t, st, r, sc, re] = await Promise.all([
    getDashboardSummary({ year }), getCarbonTrend({ year }), getEnergyStructure({ year }),
    getUnitRanking({ year, dimension: 'carbon' }), getScopeBreakdown({ year }), getRecentEntries({ limit: 12 })
  ])
  Object.assign(summary, s); orgName.value = s.org_name
  trend.value = t; structure.value = st; ranking.value = r; scope.value = sc; recent.value = re
  refreshCharts()
}

let clockTimer = null
let dataTimer = null
function tick() { const d = new Date(); clock.value = d.toLocaleString('zh-CN', { hour12: false }) }

onMounted(async () => {
  await nextTick(); initCharts(); window.addEventListener('resize', onResize); tick(); clockTimer = setInterval(tick, 1000)
  await refresh(); dataTimer = setInterval(refresh, 5 * 60 * 1000)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  clearInterval(clockTimer); clearInterval(dataTimer)
  Object.values(charts).forEach(c => c && c.dispose())
})
</script>

<style scoped>
.screen { min-height: 100vh; background: radial-gradient(1200px 600px at 50% -10%, #1c2b4a 0%, #0b1020 60%, #060912 100%); color: #fff; padding: 18px 22px; }
.screen__header { display: flex; align-items: center; gap: 16px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.screen__title { font-size: 26px; font-weight: 700; letter-spacing: 1px; }
.screen__sub { font-size: 13px; color: rgba(255,255,255,0.6); }
.screen__right { margin-left: auto; display: flex; align-items: center; gap: 14px; }
.screen__clock { font-size: 14px; color: rgba(255,255,255,0.7); font-variant-numeric: tabular-nums; }
.screen__stats { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin: 16px 0; }
.screen__stat { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 16px; text-align: center; }
.screen__stat-value { font-size: 24px; font-weight: 700; color: #fff; font-variant-numeric: tabular-nums; }
.screen__stat-unit { font-size: 12px; color: rgba(255,255,255,0.5); margin-left: 4px; }
.screen__stat-label { font-size: 12px; color: rgba(255,255,255,0.6); margin-top: 6px; }
.screen__grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.screen__panel { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 14px; }
.screen__panel--wide { grid-column: span 2; }
.screen__panel-title { font-size: 15px; font-weight: 600; margin-bottom: 10px; color: rgba(255,255,255,0.9); }
.screen__chart { width: 100%; height: 280px; }
.screen__recent { max-height: 260px; overflow: auto; }
.screen__recent-row { display: grid; grid-template-columns: 1.4fr 1fr 1fr 1fr; padding: 8px 4px; font-size: 13px; color: rgba(255,255,255,0.8); border-bottom: 1px solid rgba(255,255,255,0.06); }
.screen__recent-head { color: rgba(255,255,255,0.5); font-size: 12px; }
.screen__recent-row.is-flash { color: #FF453A; animation: flash 1.2s infinite; font-weight: 600; }
.screen__empty { text-align: center; color: rgba(255,255,255,0.4); padding: 30px; }
@keyframes flash { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
</style>
