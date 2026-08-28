<template>
  <div class="page">
    <PageHeader title="碳核算存证" subtitle="将碳核算记录上链存证，生成存证编号与哈希，支持查询核验" />

    <el-card class="panel">
      <div class="filter-bar">
        <el-select v-model="year" placeholder="年份" style="width:120px" @change="load">
          <el-option v-for="y in yearOptions" :key="y" :label="y + ' 年'" :value="y" />
        </el-select>
        <el-select v-model="status" placeholder="状态" clearable style="width:130px" @change="load">
          <el-option label="待上链" value="待上链" />
          <el-option label="已上链" value="已上链" />
          <el-option label="校验通过" value="校验通过" />
          <el-option label="校验失败" value="校验失败" />
        </el-select>
        <el-button type="primary" @click="openAdd">新增存证</el-button>
      </div>
      <el-table :data="list" border stripe v-loading="loading" :empty-text="'暂无存证'">
        <el-table-column prop="evidence_no" label="存证编号" width="190" />
        <el-table-column prop="year" label="年" width="64" />
        <el-table-column prop="month" label="月" width="54" />
        <el-table-column prop="scope" label="范围" width="74" />
        <el-table-column label="排放源" min-width="120"><template #default="{ row }">{{ row.source_name }}</template></el-table-column>
        <el-table-column prop="emission" label="排放量(tCO₂)" align="right" width="120" />
        <el-table-column prop="chain_platform" label="存证链/平台" min-width="120" />
        <el-table-column prop="evidence_hash" label="存证哈希" min-width="160" show-overflow-tooltip />
        <el-table-column prop="tx_time" label="上链时间" width="160" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
    </el-card>

    <el-dialog v-model="visible" :title="editing ? '编辑存证' : '新增存证'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="核算记录" prop="accounting_id" v-if="!editing">
          <el-select v-model="form.accounting_id" filterable style="width:100%" placeholder="选择碳核算记录">
            <el-option v-for="a in accountingOptions" :key="a.id" :label="`${a.year}-${a.month} ${a.source_name}（${a.scope} ${a.emission} tCO₂）`" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="存证链/平台"><el-input v-model="form.chain_platform" placeholder="如 长安链 / 蚂蚁链 / 公信宝" /></el-form-item>
        <el-form-item label="存证哈希"><el-input v-model="form.evidence_hash" placeholder="链上交易哈希（可选）" /></el-form-item>
        <el-form-item label="上链时间"><el-date-picker v-model="form.tx_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width:100%">
            <el-option label="待上链" value="待上链" />
            <el-option label="已上链" value="已上链" />
            <el-option label="校验通过" value="校验通过" />
            <el-option label="校验失败" value="校验失败" />
          </el-select>
        </el-form-item>
        <el-form-item label="存证人"><el-input v-model="form.operator" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import { listEvidences, createEvidence, updateEvidence, deleteEvidence, listAccounting } from '@/api'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(50); const loading = ref(false)
const year = ref(new Date().getFullYear()); const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - i)
const status = ref('')
const accountingOptions = ref([])
const visible = ref(false); const editing = ref(false); const saving = ref(false); const formRef = ref(null)
const form = reactive({ id: null, accounting_id: null, chain_platform: '', evidence_hash: '', tx_time: null, status: '已上链', operator: '', remark: '' })
const rules = {
  accounting_id: [{ required: true, message: '请选择核算记录', trigger: 'change' }]
}
const statusType = (s) => ({ '待上链': 'info', '已上链': 'warning', '校验通过': 'success', '校验失败': 'danger' }[s] || 'info')

async function load() {
  loading.value = true
  try {
    const res = await listEvidences({ page: page.value, page_size: pageSize.value, year: year.value, status: status.value || undefined })
    list.value = res.items || []; total.value = res.total || 0
  } finally { loading.value = false }
}
async function loadAccountingOptions() {
  const res = await listAccounting({ page: 1, page_size: 200 })
  const items = res.items || []
  accountingOptions.value = items.map(x => ({ id: x.id, year: x.year, month: x.month, source_name: x.source_name, scope: x.scope, emission: x.emission }))
}
function openAdd() { editing.value = false; Object.assign(form, { id: null, accounting_id: null, chain_platform: '', evidence_hash: '', tx_time: null, status: '已上链', operator: '', remark: '' }); visible.value = true; loadAccountingOptions() }
function openEdit(row) { editing.value = true; Object.assign(form, { ...row, accounting_id: row.accounting_id }); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const payload = { ...form }; delete payload.id
      if (editing.value) await updateEvidence(form.id, payload); else await createEvidence(payload)
      ElMessage.success('已保存'); visible.value = false; load()
    } finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm('删除该存证记录？', '提示', { type: 'warning' }).then(async () => { await deleteEvidence(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(load)
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; } .filter-bar { display: flex; gap: 12px; margin-bottom: 14px; }</style>
