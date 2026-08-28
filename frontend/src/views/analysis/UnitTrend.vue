<template>
  <div class="page">
    <PageHeader title="单元环比" subtitle="同一用能单元本期与上期的能耗指标环比变化" />

    <el-card class="panel">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="单元" required>
          <el-select v-model="unitId" filterable placeholder="选择单元" style="width:180px">
            <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
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
        <el-form-item label="本期">
          <el-date-picker v-model="curRange" type="daterange" value-format="YYYY-MM-DDTHH:mm:ss"
            start-placeholder="开始" end-placeholder="结束" style="width:300px" />
        </el-form-item>
        <el-form-item label="上期">
          <el-date-picker v-model="lastRange" type="daterange" value-format="YYYY-MM-DDTHH:mm:ss"
            start-placeholder="开始" end-placeholder="结束" style="width:300px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="run">开始环比</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="stat-row" v-if="result">
      <StatCard :label="`本期 · ${dimLabel}`" :value="fmt(result.current)" :unit="unit" />
      <StatCard :label="`上期 · ${dimLabel}`" :value="fmt(result.last)" :unit="unit" />
      <StatCard label="增减量" :value="fmt(result.diff)" :unit="unit" :hint="result.diff >= 0 ? '本期上升' : '本期下降'" />
      <StatCard label="环比" :value="fmt(result.ratio)" unit="%" :hint="result.ratio >= 0 ? '上升' : '下降'" />
    </div>

    <ChartCard v-if="result" title="本期 vs 上期" :option="compareOption" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import { listEnergyUnits, ratioEnergy } from '@/api'

const units = ref([])
const unitId = ref(null)
const dimension = ref('carbon')
const curRange = ref(null)
const lastRange = ref(null)
const result = ref(null)

const dimLabel = computed(() => ({ energy: '能耗', cost: '费用', coal: '标准煤', carbon: '碳排放' }[dimension.value]))
const unit = computed(() => ({ energy: 'kWh', cost: '元', coal: 'kgce', carbon: 'tCO₂' }[dimension.value]))

function fmt(v, d = 2) {
  if (v === null || v === undefined || isNaN(v)) return '0'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d })
}

async function run() {
  if (!unitId.value) return ElMessage.warning('请选择单元')
  if (!curRange.value || curRange.value.length !== 2) return ElMessage.warning('请选择本期周期')
  if (!lastRange.value || lastRange.value.length !== 2) return ElMessage.warning('请选择上期周期')
  const r = await ratioEnergy({
    target_id: unitId.value, dimension: dimension.value, mode: 'unit',
    current_start: curRange.value[0], current_end: curRange.value[1],
    last_start: lastRange.value[0], last_end: lastRange.value[1]
  })
  result.value = r
}

const compareOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 70, right: 30, top: 40, bottom: 30 },
  xAxis: { type: 'category', data: ['上期', '本期'] },
  yAxis: { type: 'value', name: unit.value },
  series: [{ name: dimLabel.value, type: 'bar', barWidth: '40%',
    data: [+Number(result.value.last).toFixed(2), +Number(result.value.current).toFixed(2)],
    itemStyle: { color: '#0071E3', borderRadius: [4, 4, 0, 0] } }]
}))

onMounted(() => { listEnergyUnits().then(r => { units.value = r.items || r }) })
</script>
