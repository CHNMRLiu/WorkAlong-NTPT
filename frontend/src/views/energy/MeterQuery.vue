<template>
  <div class="page">
    <PageHeader title="计量查询" subtitle="查询单个表计在选定周期内的读数、消耗与折算情况" />

    <div class="filter-bar">
      <el-select v-model="meterId" placeholder="选择表计" filterable style="width:260px" @change="loadData">
        <el-option v-for="m in meters" :key="m.id" :label="`${m.name}（${m.code}）`" :value="m.id" />
      </el-select>
      <el-select v-model="period" style="width:120px" @change="loadData">
        <el-option label="按日" value="day" /><el-option label="按月" value="month" /><el-option label="按年" value="year" />
      </el-select>
      <el-date-picker v-model="start" type="date" placeholder="起始" value-format="YYYY-MM-DD" style="width:150px" @change="loadData" />
      <el-date-picker v-model="end" type="date" placeholder="结束" value-format="YYYY-MM-DD" style="width:150px" @change="loadData" />
      <el-button type="primary" @click="loadData">查询</el-button>
    </div>

    <el-alert v-if="!meterId" title="请先选择表计" type="info" :closable="false" style="margin-bottom:16px" />
    <el-empty v-else-if="!loading && !items.length" description="该表计暂无读数数据" />

    <template v-else>
      <ChartCard title="表计消耗与碳排放" :option="option" :height="340" />
      <el-table :data="items" border stripe class="apple-table" style="margin-top:18px">
        <el-table-column prop="period" label="周期" width="120" />
        <el-table-column prop="last_reading" label="上期读数" width="120" align="right" />
        <el-table-column prop="current_reading" label="本期读数" width="120" align="right" />
        <el-table-column prop="consumption" label="消耗量" width="130" align="right">
          <template #default="{ row }">{{ fmt(row.consumption) }}</template>
        </el-table-column>
        <el-table-column prop="cost" label="费用(元)" width="120" align="right">
          <template #default="{ row }">{{ fmt(row.cost) }}</template>
        </el-table-column>
        <el-table-column prop="standard_coal" label="标准煤(t)" width="120" align="right">
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
import { ref, computed, onMounted } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import ChartCard from '@/components/ChartCard.vue'
import { listMeters, getMeterQuery } from '@/api'

const fmt = (v) => (v == null ? '0' : Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 4 }))

const meters = ref([])
const meterId = ref(null)
const period = ref('month')
const start = ref('')
const end = ref('')
const loading = ref(false)
const items = ref([])

async function loadBasics() {
  const m = await listMeters()
  meters.value = m.items || m || []
  if (meters.value.length) { meterId.value = meters.value[0].id; loadData() }
}

async function loadData() {
  if (!meterId.value) return
  loading.value = true
  try {
    const res = await getMeterQuery({
      meter_id: meterId.value, period: period.value,
      start: start.value || undefined, end: end.value || undefined
    })
    items.value = res.items || []
  } finally { loading.value = false }
}

const option = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['消耗量', '碳排放'], bottom: 0 },
  grid: { left: 70, right: 70, top: 30, bottom: 50 },
  xAxis: { type: 'category', data: items.value.map(i => i.period) },
  yAxis: [
    { type: 'value', name: '消耗量' },
    { type: 'value', name: 'tCO₂' }
  ],
  series: [
    { name: '消耗量', type: 'bar', barWidth: '42%', itemStyle: { color: '#0071E3', borderRadius: [6, 6, 0, 0] }, data: items.value.map(i => Number((i.consumption || 0).toFixed(4))) },
    { name: '碳排放', type: 'line', smooth: true, yAxisIndex: 1, itemStyle: { color: '#34C759' }, data: items.value.map(i => Number((i.carbon_emission || 0).toFixed(6))) }
  ]
}))

onMounted(loadBasics)
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 18px; }
.apple-table { border-radius: 12px; overflow: hidden; box-shadow: var(--c-shadow-card); }
</style>
