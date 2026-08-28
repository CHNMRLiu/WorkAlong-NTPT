<template>
  <div class="page">
    <PageHeader title="碳排放核算" subtitle="按排放源录入活动数据，自动计算各范围碳排放（范围1/2/3）" />

    <el-card class="panel">
      <div class="filter-bar">
        <el-select v-model="year" placeholder="年份" style="width:120px" @change="load">
          <el-option v-for="y in yearOptions" :key="y" :label="y + ' 年'" :value="y" />
        </el-select>
        <el-select v-model="scope" clearable placeholder="范围" style="width:120px" @change="load">
          <el-option label="范围1" value="范围1" /><el-option label="范围2" value="范围2" /><el-option label="范围3" value="范围3" />
        </el-select>
        <el-button type="primary" @click="openAdd">新增核算</el-button>
      </div>
      <el-table :data="list" border stripe v-loading="loading" :empty-text="'暂无核算'">
        <el-table-column prop="year" label="年" width="70" />
        <el-table-column prop="month" label="月" width="60" />
        <el-table-column label="排放源" width="160"><template #default="{ row }">{{ srcName(row.source_id) }}</template></el-table-column>
        <el-table-column prop="activity_data" label="活动数据" align="right" />
        <el-table-column prop="unit" label="单位" width="90" />
        <el-table-column prop="emission_factor" label="排放因子" align="right" width="100" />
        <el-table-column prop="emission" label="排放量(tCO₂)" align="right" />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <el-table-column label="存证状态" width="92" align="center">
          <template #default="{ row }">
            <el-tag :type="(row.evidence_status || '未存证') === '已存证' ? 'success' : 'info'">{{ row.evidence_status || '未存证' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="存证" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link :disabled="(row.evidence_status || '未存证') === '已存证'" @click="openEvidence(row)">
              {{ (row.evidence_status || '未存证') === '已存证' ? '已存证' : '一键存证' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
    </el-card>

    <el-dialog v-model="visible" :title="editing ? '编辑核算' : '新增核算'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="排放源" prop="source_id">
          <el-select v-model="form.source_id" style="width:100%">
            <el-option v-for="s in sources" :key="s.id" :label="`${s.name}（${s.scope}）`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="年份" prop="year"><el-input v-model.number="form.year" type="number" /></el-form-item>
        <el-form-item label="月份" prop="month"><el-input v-model.number="form.month" type="number" /></el-form-item>
        <el-form-item label="活动数据" prop="activity_data"><el-input v-model.number="form.activity_data" type="number" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" placeholder="如 kWh、t、km" /></el-form-item>
        <el-form-item label="排放因子"><el-input v-model.number="form.emission_factor" type="number" placeholder="kgCO₂/单位" /></el-form-item>
        <el-form-item label="数据来源"><el-input v-model="form.data_source" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 一键存证弹窗（联动碳核算记录） -->
    <el-dialog v-model="eviVisible" title="一键存证" width="480px">
      <el-descriptions :column="2" border size="small" class="evi-desc">
        <el-descriptions-item label="年">{{ eviForm.year }}</el-descriptions-item>
        <el-descriptions-item label="月">{{ eviForm.month }}</el-descriptions-item>
        <el-descriptions-item label="排放源">{{ eviForm.source_name }}</el-descriptions-item>
        <el-descriptions-item label="范围">{{ eviForm.scope }}</el-descriptions-item>
        <el-descriptions-item label="排放量(tCO₂)" :span="2">{{ eviForm.emission }}</el-descriptions-item>
      </el-descriptions>
      <el-form ref="eviRef" :model="eviForm" label-width="92px" style="margin-top:16px">
        <el-form-item label="存证链/平台"><el-input v-model="eviForm.chain_platform" placeholder="如 长安链 / 蚂蚁链 / 公信宝" /></el-form-item>
        <el-form-item label="存证哈希"><el-input v-model="eviForm.evidence_hash" placeholder="链上交易哈希（可选）" /></el-form-item>
        <el-form-item label="上链时间"><el-date-picker v-model="eviForm.tx_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="eviForm.status" style="width:100%">
            <el-option label="待上链" value="待上链" />
            <el-option label="已上链" value="已上链" />
            <el-option label="校验通过" value="校验通过" />
            <el-option label="校验失败" value="校验失败" />
          </el-select>
        </el-form-item>
        <el-form-item label="存证人"><el-input v-model="eviForm.operator" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="eviForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="eviVisible = false">取消</el-button>
        <el-button type="primary" :loading="eviSaving" @click="saveEvidence">确认存证</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import { listAccounting, createAccounting, updateAccounting, deleteAccounting, listEmissionSources, createEvidence } from '@/api'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(50); const loading = ref(false)
const year = ref(new Date().getFullYear()); const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - i)
const scope = ref('')
const sources = ref([]); const srcMap = ref({}); const scopeMap = ref({})
const visible = ref(false); const editing = ref(false); const saving = ref(false); const formRef = ref(null)
const eviVisible = ref(false); const eviSaving = ref(false); const eviRef = ref(null)
const eviForm = reactive({ accounting_id: null, year: '', month: '', source_name: '', scope: '', emission: 0, chain_platform: '', evidence_hash: '', tx_time: null, status: '已上链', operator: '', remark: '' })
const form = reactive({ id: null, source_id: null, year: new Date().getFullYear(), month: new Date().getMonth() + 1, activity_data: 0, unit: '', emission_factor: 0, data_source: '' })
const rules = {
  source_id: [{ required: true, message: '请选择排放源', trigger: 'change' }],
  year: [{ required: true, message: '请输入年份', trigger: 'blur' }],
  month: [{ required: true, message: '请输入月份', trigger: 'blur' }],
  activity_data: [{ required: true, message: '请输入活动数据', trigger: 'blur' }]
}
const srcName = (id) => srcMap.value[id] || `源#${id}`

async function load() {
  loading.value = true
  try {
    const res = await listAccounting({ page: page.value, page_size: pageSize.value, year: year.value, scope: scope.value || undefined })
    list.value = res.items || []; total.value = res.total || 0
  } finally { loading.value = false }
}
function openAdd() { editing.value = false; Object.assign(form, { id: null, source_id: null, year: year.value, month: new Date().getMonth() + 1, activity_data: 0, unit: '', emission_factor: 0, data_source: '' }); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editing.value) await updateAccounting(form.id, { ...form }); else await createAccounting({ ...form })
      ElMessage.success('已保存'); visible.value = false; load()
    } finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm('删除该核算记录？', '提示', { type: 'warning' }).then(async () => { await deleteAccounting(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
function openEvidence(row) {
  Object.assign(eviForm, {
    accounting_id: row.id, year: row.year, month: row.month,
    source_name: srcName(row.source_id), scope: scopeMap.value[row.source_id] || '',
    emission: row.emission, chain_platform: '', evidence_hash: '', tx_time: null,
    status: '已上链', operator: '', remark: '',
  })
  eviVisible.value = true
}
async function saveEvidence() {
  eviSaving.value = true
  try {
    await createEvidence({
      accounting_id: eviForm.accounting_id,
      chain_platform: eviForm.chain_platform,
      evidence_hash: eviForm.evidence_hash,
      tx_time: eviForm.tx_time,
      status: eviForm.status,
      operator: eviForm.operator,
      remark: eviForm.remark,
    })
    ElMessage.success('存证成功，已生成存证编号')
    eviVisible.value = false
    load()
  } finally { eviSaving.value = false }
}
onMounted(async () => {
  const s = await listEmissionSources(); sources.value = s.items || s
  srcMap.value = Object.fromEntries(sources.value.map(x => [x.id, `${x.name}（${x.scope}）`]))
  scopeMap.value = Object.fromEntries(sources.value.map(x => [x.id, x.scope]))
  load()
})
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; } .filter-bar { display: flex; gap: 12px; margin-bottom: 14px; } .evi-desc { margin-bottom: 4px; }</style>
