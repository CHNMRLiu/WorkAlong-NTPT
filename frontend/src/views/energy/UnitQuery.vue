<template>
  <div class="page">
    <PageHeader title="单元查询" subtitle="查看指定用能单元的能耗构成、费用、标准煤与碳排放汇总" />

    <div class="filter-bar">
      <el-select v-model="unitId" placeholder="请选择用能单元" filterable style="width:240px" @change="loadData">
        <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
      </el-select>
      <el-date-picker v-model="start" type="date" placeholder="起始" value-format="YYYY-MM-DD" style="width:150px" @change="loadData" />
      <el-date-picker v-model="end" type="date" placeholder="结束" value-format="YYYY-MM-DD" style="width:150px" @change="loadData" />
      <el-button type="primary" @click="loadData">查询</el-button>
    </div>

    <el-alert v-if="!unitId" title="请先选择用能单元" type="info" :closable="false" style="margin-bottom:16px" />
    <el-empty v-else-if="!loading && !summary.items.length" description="该单元暂无数据" />

    <template v-else>
      <div class="stat-row" v-if="!loading">
        <StatCard label="总消耗量" :value="fmt(summary.total_consumption)" />
        <StatCard label="总费用(元)" :value="fmt(summary.total_cost)" />
        <StatCard label="总标准煤(t)" :value="fmt(summary.total_standard_coal)" />
        <StatCard label="总碳排放(tCO₂)" :value="fmt(summary.total_carbon)" />
      </div>
      <div class="chart-grid">
        <ChartCard title="单元碳排放构成" :option="pieOption" />
        <ChartCard title="单元能源结构" :option="barOption" />
      </div>
      <el-table :data="summary.items" border stripe class="apple-table" style="margin-top:18px">
        <el-table-column type="index" label="#" width="55" align="center" />
        <el-table-column prop="energy_type" label="能源类型" min-width="140" />
        <el-table-column prop="unit" label="单位" width="90" align="center" />
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
        <el-table-column prop="ratio" label="碳排占比" width="100" align="right">
          <template #default="{ row }">{{ row.ratio }}%</template>
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
import { listEnergyUnits, getComprehensive } from '@/api'

const fmt = (v) => (v == null ? '0' : Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 4 }))

const units = ref([])
const unitId = ref(null)
const start = ref('')
const end = ref('')
const loading = ref(false)
const summary = reactive({ total_consumption: 0, total_cost: 0, total_standard_coal: 0, total_carbon: 0, energy_type_count: 0, items: [] })

async function loadBasics() {
  const u = await listEnergyUnits()
  units.value = u.items || u || []
}

async function loadData() {
  if (!unitId.value) return
  loading.value = true
  try {
    const res = await getComprehensive({
      unit_id: unitId.value,
      start: start.value || undefined, end: end.value || undefined
    })
    Object.assign(summary, res)
  } finally { loading.value = false }
}

const pieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} tCO₂ ({d}%)' },
  legend: { bottom: 0, type: 'scroll' },
  series: [{
    type: 'pie', radius: ['42%', '68%'], center: ['50%', '46%'],
    itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
    label: { formatter: '{b}\n{d}%' },
    data: summary.items.map(i => ({ name: i.energy_type, value: Number((i.carbon_emission || 0).toFixed(4)) }))
  }]
}))

const barOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 60, right: 20, top: 30, bottom: 50 },
  xAxis: { type: 'category', data: summary.items.map(i => i.energy_type), axisLabel: { interval: 0, rotate: 20 } },
  yAxis: { type: 'value', name: '标准煤(t)' },
  series: [{
    type: 'bar', barWidth: '46%', itemStyle: { color: '#5856D6', borderRadius: [6, 6, 0, 0] },
    data: summary.items.map(i => Number((i.standard_coal || 0).toFixed(4)))
  }]
}))

onMounted(loadBasics)
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 18px; }
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 18px; }
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.apple-table { border-radius: 12px; overflow: hidden; box-shadow: var(--c-shadow-card); }
</style>
