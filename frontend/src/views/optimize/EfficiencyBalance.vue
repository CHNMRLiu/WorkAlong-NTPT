<template>
  <div class="page">
    <PageHeader title="能效平衡" subtitle="基于能流连接分析能源输入、有效利用与损失，识别节能重点环节" />

    <div class="stat-row" v-if="balance.total > 0">
      <StatCard label="能源总输入" :value="fmt(balance.total)" unit="kWh" />
      <StatCard label="有效利用" :value="fmt(balance.utilized)" unit="kWh" :hint="`占比 ${utilRate}%`" />
      <StatCard label="损失量" :value="fmt(balance.loss)" unit="kWh" :hint="`占比 ${lossRate}%`" />
      <StatCard label="能源利用效率" :value="fmt(utilRate)" unit="%" />
    </div>

    <el-row :gutter="16">
      <el-col :span="14">
        <ChartCard title="各环节输入 / 输出流量" :option="barOption" :height="360" />
      </el-col>
      <el-col :span="10">
        <el-card class="panel">
          <template #header><span class="panel__title">节点流量平衡</span></template>
          <el-table :data="nodeBalance" border stripe :empty-text="'暂无数据'">
            <el-table-column prop="name" label="节点" />
            <el-table-column prop="inflow" label="输入" align="right" />
            <el-table-column prop="outflow" label="输出" align="right" />
            <el-table-column label="盈亏" align="right">
              <template #default="{ row }">
                <span :style="{ color: row.inflow - row.outflow >= 0 ? '#34C759' : '#FF3B30' }">{{ fmt(row.inflow - row.outflow) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-alert v-if="balance.total === 0" type="info" :closable="false" title="请先在「能流桑基图」中维护节点与连接数据" style="margin-top:16px" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import { listFlowNodes, listFlowLinks } from '@/api'

const nodes = ref([])
const links = ref([])

function fmt(v, d = 2) {
  if (v === null || v === undefined || isNaN(v)) return '0'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d })
}

const balance = computed(() => {
  const nodeType = Object.fromEntries(nodes.value.map(n => [n.id, n.node_type]))
  let total = 0, loss = 0
  for (const l of links.value) {
    const sv = Number(l.flow_value || 0)
    const st = nodeType[l.source_node_id]
    if (st === '输入' || st === '转换' || st === '分配') total += sv
    if (nodeType[l.target_node_id] === '损失') loss += sv
  }
  const utilized = Math.max(0, total - loss)
  return { total, loss, utilized }
})
const utilRate = computed(() => balance.value.total ? +(balance.value.utilized / balance.value.total * 100).toFixed(2) : 0)
const lossRate = computed(() => balance.value.total ? +(balance.value.loss / balance.value.total * 100).toFixed(2) : 0)

const nodeBalance = computed(() => {
  const map = {}
  for (const n of nodes.value) map[n.id] = { name: n.name, inflow: 0, outflow: 0 }
  for (const l of links.value) {
    const v = Number(l.flow_value || 0)
    if (map[l.source_node_id]) map[l.source_node_id].outflow += v
    if (map[l.target_node_id]) map[l.target_node_id].inflow += v
  }
  return Object.values(map)
})

const barOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['输入', '输出'] },
  grid: { left: 70, right: 30, top: 50, bottom: 40 },
  xAxis: { type: 'category', data: nodeBalance.value.map(x => x.name), axisLabel: { interval: 0, rotate: 20 } },
  yAxis: { type: 'value' },
  series: [
    { name: '输入', type: 'bar', data: nodeBalance.value.map(x => +x.inflow.toFixed(2)), itemStyle: { color: '#0071E3' } },
    { name: '输出', type: 'bar', data: nodeBalance.value.map(x => +x.outflow.toFixed(2)), itemStyle: { color: '#34C759' } }
  ]
}))

async function load() {
  nodes.value = await listFlowNodes()
  links.value = await listFlowLinks()
}
onMounted(load)
</script>
