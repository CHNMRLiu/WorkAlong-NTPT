<template>
  <div class="page">
    <PageHeader title="能流桑基图" subtitle="展示能源输入→转换→分配→利用→损失的全过程流向">
      <template #actions>
        <el-button type="success" size="small" :loading="building" @click="autoBuild">从能耗数据自动生成</el-button>
      </template>
    </PageHeader>

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card class="panel">
          <template #header><span class="panel__title">能流节点</span>
            <el-button style="float:right" type="primary" size="small" @click="nodeVisible = true">新增节点</el-button>
          </template>
          <el-table :data="nodes" border stripe :empty-text="'暂无节点'">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="node_type" label="类型" width="80" />
            <el-table-column label="操作" width="60" align="center">
              <template #default="{ row }"><el-button link type="danger" @click="removeNode(row)">删</el-button></template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="panel" style="margin-top:16px">
          <template #header><span class="panel__title">能流连接</span>
            <el-button style="float:right" type="primary" size="small" @click="linkVisible = true">新增连接</el-button>
          </template>
          <el-table :data="links" border stripe :empty-text="'暂无连接'">
            <el-table-column label="来源" width="90"><template #default="{ row }">{{ nodeName(row.source_node_id) }}</template></el-table-column>
            <el-table-column label="去向" width="90"><template #default="{ row }">{{ nodeName(row.target_node_id) }}</template></el-table-column>
            <el-table-column prop="flow_value" label="流量" align="right" />
            <el-table-column prop="loss_rate" label="损失率" align="right" width="80" />
            <el-table-column label="操作" width="60" align="center">
              <template #default="{ row }"><el-button link type="danger" @click="removeLink(row)">删</el-button></template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="17">
        <ChartCard title="能流桑基图" :option="sankeyOption" :height="520" />
      </el-col>
    </el-row>

    <el-dialog v-model="nodeVisible" title="新增节点" width="420px">
      <el-form :model="nodeForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="nodeForm.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="nodeForm.node_type" style="width:100%">
            <el-option label="输入" value="输入" /><el-option label="转换" value="转换" />
            <el-option label="分配" value="分配" /><el-option label="利用" value="利用" /><el-option label="损失" value="损失" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序"><el-input v-model.number="nodeForm.sort_order" type="number" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="nodeVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNode">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="linkVisible" title="新增连接" width="420px">
      <el-form :model="linkForm" label-width="80px">
        <el-form-item label="来源节点">
          <el-select v-model="linkForm.source_node_id" style="width:100%">
            <el-option v-for="n in nodes" :key="n.id" :label="n.name" :value="n.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="去向节点">
          <el-select v-model="linkForm.target_node_id" style="width:100%">
            <el-option v-for="n in nodes" :key="n.id" :label="n.name" :value="n.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="流量"><el-input v-model.number="linkForm.flow_value" type="number" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="linkForm.unit" placeholder="如 kWh" /></el-form-item>
        <el-form-item label="损失率%"><el-input v-model.number="linkForm.loss_rate" type="number" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="linkVisible = false">取消</el-button>
        <el-button type="primary" @click="saveLink">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import ChartCard from '@/components/ChartCard.vue'
import { listFlowNodes, createFlowNode, deleteFlowNode, listFlowLinks, createFlowLink, deleteFlowLink, autoBuildFlow } from '@/api'

const nodes = ref([])
const links = ref([])
const building = ref(false)

const nodeVisible = ref(false)
const nodeForm = reactive({ name: '', node_type: '输入', sort_order: 0 })
const linkVisible = ref(false)
const linkForm = reactive({ source_node_id: null, target_node_id: null, flow_value: 0, unit: 'kWh', loss_rate: 0 })

function nodeName(id) { const n = nodes.value.find(x => x.id === id); return n ? n.name : `#${id}` }

async function load() {
  nodes.value = await listFlowNodes()
  links.value = await listFlowLinks()
}

const sankeyOption = computed(() => {
  const data = nodes.value.map(n => ({ name: n.name, itemStyle: { color: '#0071E3' } }))
  const linkData = links.value.map(l => ({
    source: nodeName(l.source_node_id),
    target: nodeName(l.target_node_id),
    value: Number(l.flow_value || 0)
  }))
  return {
    tooltip: { trigger: 'item', triggerOn: 'mousemove' },
    series: [{
      type: 'sankey', emphasis: { focus: 'adjacency' },
      nodeWidth: 16, nodeGap: 14,
      data, links: linkData,
      lineStyle: { color: 'gradient', curveness: 0.5, opacity: 0.5 },
      label: { color: '#1D1D1F', fontSize: 12 }
    }]
  }
})

async function saveNode() {
  if (!nodeForm.name) return ElMessage.warning('请输入名称')
  await createFlowNode({ ...nodeForm }); ElMessage.success('已保存'); nodeVisible.value = false; load()
}
async function removeNode(row) {
  await ElMessageBox.confirm(`删除节点「${row.name}」？`, '提示', { type: 'warning' })
    .then(async () => { await deleteFlowNode(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
async function saveLink() {
  if (!linkForm.source_node_id || !linkForm.target_node_id) return ElMessage.warning('请选择节点')
  await createFlowLink({ ...linkForm }); ElMessage.success('已保存'); linkVisible.value = false; load()
}
async function removeLink(row) {
  await ElMessageBox.confirm('删除该连接？', '提示', { type: 'warning' })
    .then(async () => { await deleteFlowLink(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}

async function autoBuild() {
  try {
    await ElMessageBox.confirm('将基于2026年读数数据自动重建能流图，清空现有节点与连接，是否继续？', '自动生成', { type: 'info' })
  } catch { return }
  building.value = true
  try {
    const res = await autoBuildFlow(2026)
    if (res.code === 0) {
      ElMessage.success(res.message || '生成成功')
      await load()
    } else {
      ElMessage.warning(res.message || '生成失败')
    }
  } finally {
    building.value = false
  }
}

onMounted(load)
</script>
