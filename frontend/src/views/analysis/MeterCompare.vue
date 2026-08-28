<template>
  <div class="page">
    <PageHeader title="计量对标" subtitle="两个表计在选定周期、选定维度下的能耗指标对比" />

    <el-card class="panel">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="表计 A" required>
          <el-select v-model="aId" filterable placeholder="选择表计" style="width:180px">
            <el-option v-for="m in meters" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="表计 B" required>
          <el-select v-model="bId" filterable placeholder="选择表计" style="width:180px">
            <el-option v-for="m in meters" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="维度">
          <el-select v-model="dimension" style="width:130px">
            <el-option label="能耗" value="energy" />
            <el-option label="费用" value="cost" />
            <el-option label="标准煤" value="coal" />
            <el-option label="碳排放" value="carbon" />
          </el-select>
        </el-form-item>
        <el-form-item label="周期">
          <el-date-picker v-model="range" type="daterange" value-format="YYYY-MM-DDTHH:mm:ss"
            start-placeholder="开始" end-placeholder="结束" style="width:300px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="run">开始对标</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="stat-row" v-if="result">
      <StatCard :label="`A · ${dimLabel}`" :value="fmt(result.a_value)" :unit="unit" />
      <StatCard :label="`B · ${dimLabel}`" :value="fmt(result.b_value)" :unit="unit" />
      <StatCard label="差值 (A-B)" :value="fmt(result.diff)" :unit="unit" :hint="result.diff >= 0 ? 'A 更高' : 'B 更高'" />
      <StatCard label="差异率" :value="fmt(result.diff_rate)" unit="%" :hint="result.diff_rate >= 0 ? 'A 高于 B' : 'A 低于 B'" />
    </div>

    <ChartCard v-if="result" title="月度对比" :option="compareOption" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import { listMeters, compareEnergy, getMeterQuery } from '@/api'

const meters = ref([])
const aId = ref(null)
const bId = ref(null)
const dimension = ref('carbon')
const range = ref(null)
const result = ref(null)
const seriesA = ref([])
const seriesB = ref([])

const dimLabel = computed(() => ({ energy: '能耗', cost: '费用', coal: '标准煤', carbon: '碳排放' }[dimension.value]))
const unit = computed(() => ({ energy: 'kWh', cost: '元', coal: 'kgce', carbon: 'tCO₂' }[dimension.value]))
const field = computed(() => ({ energy: 'consumption', cost: 'cost', coal: 'standard_coal', carbon: 'carbon_emission' }[dimension.value]))

function fmt(v, d = 2) {
  if (v === null || v === undefined || isNaN(v)) return '0'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d })
}

async function run() {
  if (!aId.value || !bId.value) return ElMessage.warning('请选择两个表计')
  if (!range.value || range.value.length !== 2) return ElMessage.warning('请选择周期')
  const [start, end] = range.value
  const r = await compareEnergy({ type_a: aId.value, type_b: bId.value, dimension: dimension.value, mode: 'meter', start, end })
  result.value = r
  const [ra, rb] = await Promise.all([
    getMeterQuery({ meter_id: aId.value, period: 'month', start, end }),
    getMeterQuery({ meter_id: bId.value, period: 'month', start, end })
  ])
  seriesA.value = ra.items || []
  seriesB.value = rb.items || []
}

const compareOption = computed(() => {
  const months = [...new Set([...seriesA.value.map(x => x.period), ...seriesB.value.map(x => x.period)])].sort()
  const f = field.value
  const pick = (arr, m) => { const it = arr.find(x => x.period === m); return it ? Number(it[f] || 0) : 0 }
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['A 月度', 'B 月度'] },
    grid: { left: 70, right: 30, top: 50, bottom: 40 },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', name: unit.value },
    series: [
      { name: 'A 月度', type: 'bar', data: months.map(m => +pick(seriesA.value, m).toFixed(2)) },
      { name: 'B 月度', type: 'bar', data: months.map(m => +pick(seriesB.value, m).toFixed(2)) }
    ]
  }
})

onMounted(() => { listMeters().then(r => { meters.value = r.items || r }) })
</script>
