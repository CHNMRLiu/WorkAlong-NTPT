<template>
  <div class="page">
    <PageHeader title="碳排统计" subtitle="按范围、排放源、月度维度统计碳排放量" />

    <el-card class="panel">
      <div class="filter-bar">
        <el-select v-model="year" placeholder="年份" style="width:120px" @change="load">
          <el-option v-for="y in yearOptions" :key="y" :label="y + ' 年'" :value="y" />
        </el-select>
        <el-select v-model="scope" clearable placeholder="范围" style="width:120px" @change="load">
          <el-option label="全部" value="全部" /><el-option label="范围1" value="范围1" /><el-option label="范围2" value="范围2" /><el-option label="范围3" value="范围3" />
        </el-select>
      </div>
    </el-card>

    <div class="stat-row">
      <StatCard label="范围1" :value="fmt(stat.scope1)" unit="tCO₂" />
      <StatCard label="范围2" :value="fmt(stat.scope2)" unit="tCO₂" />
      <StatCard label="范围3" :value="fmt(stat.scope3)" unit="tCO₂" />
      <StatCard label="合计" :value="fmt(stat.total)" unit="tCO₂" :hint="year + ' 年'" />
    </div>

    <el-row :gutter="16">
      <el-col :span="14">
        <ChartCard title="月度碳排放趋势" :option="monthlyOption" :height="320" />
      </el-col>
      <el-col :span="10">
        <ChartCard title="排放源占比" :option="sourceOption" :height="320" />
      </el-col>
    </el-row>

    <el-card class="panel" style="margin-top:16px">
      <template #header><span class="panel__title">排放源明细</span></template>
      <el-table :data="stat.sources" border stripe :empty-text="'暂无数据'">
        <el-table-column prop="name" label="排放源" />
        <el-table-column prop="scope" label="范围" width="90" />
        <el-table-column prop="emission" label="排放量(tCO₂)" align="right" />
        <el-table-column prop="ratio" label="占比%" align="right" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import { getCarbonStatistics } from '@/api'

const year = ref(new Date().getFullYear()); const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - i)
const scope = ref('全部')
const stat = ref({ scope1: 0, scope2: 0, scope3: 0, total: 0, sources: [], monthly: [] })

function fmt(v, d = 2) { if (v == null || isNaN(v)) return '0'; return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d }) }

async function load() {
  stat.value = await getCarbonStatistics({ year: year.value, scope: scope.value })
}
const monthlyOption = computed(() => ({
  tooltip: { trigger: 'axis' }, grid: { left: 60, right: 30, top: 40, bottom: 30 },
  xAxis: { type: 'category', data: stat.value.monthly.map(m => m.month) },
  yAxis: { type: 'value', name: 'tCO₂' },
  series: [{ name: '月度排放', type: 'bar', data: stat.value.monthly.map(m => +Number(m.emission || 0).toFixed(2)), itemStyle: { color: '#34C759', borderRadius: [4, 4, 0, 0] } }]
}))
const basePalette = ['#0071E3', '#34C759', '#FF9500', '#AF52DE', '#FF2D55', '#5AC8FA', '#FFCC00', '#FF3B30']
const sourceOption = computed(() => ({
  tooltip: { trigger: 'item' }, legend: { bottom: 0, type: 'scroll' },
  series: [{ type: 'pie', radius: ['40%', '68%'], avoidLabelOverlap: true, label: { show: false }, labelLine: { show: false },
    data: stat.value.sources.map((s, i) => ({ name: s.name, value: +Number(s.emission || 0).toFixed(2), itemStyle: { color: basePalette[i % basePalette.length] } })) }]
}))
onMounted(load)
</script>
<style scoped>.filter-bar { display: flex; gap: 12px; margin-bottom: 14px; }</style>
