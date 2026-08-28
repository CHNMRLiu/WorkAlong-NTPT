<template>
  <div class="page">
    <PageHeader title="单元统计" subtitle="按周期统计各用能单元的能源消耗、费用、标准煤与碳排放趋势" />

    <div class="filter-bar">
      <el-select v-model="unitId" placeholder="选择用能单元" clearable filterable style="width:220px" @change="loadData">
        <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
      </el-select>
      <el-select v-model="period" style="width:120px" @change="loadData">
        <el-option label="按日" value="day" /><el-option label="按月" value="month" /><el-option label="按年" value="year" />
      </el-select>
      <el-date-picker v-model="start" type="date" placeholder="起始" value-format="YYYY-MM-DD" style="width:150px" @change="loadData" />
      <el-date-picker v-model="end" type="date" placeholder="结束" value-format="YYYY-MM-DD" style="width:150px" @change="loadData" />
      <el-button type="primary" @click="loadData">查询</el-button>
    </div>

    <el-empty v-if="!loading && !items.length" description="暂无数据" />

    <template v-else>
      <ChartCard title="单元能耗趋势" :option="lineOption" :height="340" />
      <div class="stat-row" v-if="!loading">
        <StatCard label="总消耗量" :value="fmt(total.consumption)" />
        <StatCard label="总费用(元)" :value="fmt(total.cost)" />
        <StatCard label="总标准煤(t)" :value="fmt(total.standard_coal)" />
        <StatCard label="总碳排放(tCO₂)" :value="fmt(total.carbon_emission)" />
      </div>
      <el-table :data="items" border stripe class="apple-table" style="margin-top:18px">
        <el-table-column prop="period" label="周期" width="120" />
        <el-table-column prop="consumption" label="消耗量" width="130" align="right">
          <template #default="{ row }">{{ fmt(row.consumption) }}</template>
        </el-table-column>
        <el-table-column prop="cost" label="费用(元)" width="130" align="right">
          <template #default="{ row }">{{ fmt(row.cost) }}</template>
        </el-table-column>
        <el-table-column prop="standard_coal" label="标准煤(t)" width="130" align="right">
          <template #default="{ row }">{{ fmt(row.standard_coal) }}</template>
        </el-table-column>
        <el-table-column prop="carbon_emission" label="碳排放(tCO₂)" width="140" align="right">
          <template #default="{ row }">{{ fmt(row.carbon_emission) }}</template>
        </el-table-column>
      </el-table>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import { listEnergyUnits, getUnitStat } from '@/api'

const fmt = (v) => (v == null ? '0' : Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 4 }))

const units = ref([])
const unitId = ref(null)
const period = ref('month')
const start = ref('')
const end = ref('')
const loading = ref(false)
const items = ref([])
const total = reactive({ consumption: 0, cost: 0, standard_coal: 0, carbon_emission: 0 })

async function loadBasics() {
  const u = await listEnergyUnits()
  units.value = u.items || u || []
}

async function loadData() {
  loading.value = true
  try {
    const res = await getUnitStat({
      unit_id: unitId.value || undefined, period: period.value,
      start: start.value || undefined, end: end.value || undefined
    })
    items.value = res.items || []
    Object.assign(total, res.total || {})
  } finally { loading.value = false }
}

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['消耗量', '碳排放'], bottom: 0 },
  grid: { left: 70, right: 70, top: 30, bottom: 50 },
  xAxis: { type: 'category', data: items.value.map(i => i.period), boundaryGap: false },
  yAxis: [
    { type: 'value', name: '消耗量' },
    { type: 'value', name: 'tCO₂' }
  ],
  series: [
    { name: '消耗量', type: 'line', smooth: true, data: items.value.map(i => Number((i.consumption || 0).toFixed(4))), itemStyle: { color: '#0071E3' } },
    { name: '碳排放', type: 'line', smooth: true, yAxisIndex: 1, data: items.value.map(i => Number((i.carbon_emission || 0).toFixed(6))), itemStyle: { color: '#34C759' } }
  ]
}))

onMounted(() => { loadBasics(); loadData() })
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 18px; }
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 18px; }
.apple-table { border-radius: 12px; overflow: hidden; box-shadow: var(--c-shadow-card); }
</style>
