<template>
  <div class="page">
    <PageHeader title="碳核查支撑" subtitle="记录年度碳核查过程与结论，留存存证信息" />

    <el-card class="panel">
      <div class="filter-bar">
        <el-button type="primary" @click="openAdd">新增核查</el-button>
      </div>
      <el-table :data="list" border stripe v-loading="loading" :empty-text="'暂无核查'">
        <el-table-column prop="year" label="年" width="70" />
        <el-table-column prop="verification_agency" label="核查机构" />
        <el-table-column prop="verifier" label="核查员" width="100" />
        <el-table-column prop="reported_emission" label="报告量(tCO₂)" align="right" width="120" />
        <el-table-column prop="verified_emission" label="核查量(tCO₂)" align="right" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }"><el-tag :type="row.status === '已核查' ? 'success' : 'warning'">{{ row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="conclusion" label="结论" show-overflow-tooltip />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
    </el-card>

    <el-dialog v-model="visible" :title="editing ? '编辑核查' : '新增核查'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="年份" prop="year"><el-input v-model.number="form.year" type="number" /></el-form-item>
        <el-form-item label="核查机构"><el-input v-model="form.verification_agency" /></el-form-item>
        <el-form-item label="核查员"><el-input v-model="form.verifier" /></el-form-item>
        <el-form-item label="开始日期"><el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="结束日期"><el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="报告排放量"><el-input v-model.number="form.reported_emission" type="number" /></el-form-item>
        <el-form-item label="核查排放量"><el-input v-model.number="form.verified_emission" type="number" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width:100%"><el-option label="待核查" value="待核查" /><el-option label="核查中" value="核查中" /><el-option label="已核查" value="已核查" /></el-select>
        </el-form-item>
        <el-form-item label="结论"><el-input v-model="form.conclusion" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="存证哈希"><el-input v-model="form.evidence_hash" placeholder="链上存证哈希（可选）" /></el-form-item>
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
import { listVerifications, createVerification, updateVerification, deleteVerification } from '@/api'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(50); const loading = ref(false)
const visible = ref(false); const editing = ref(false); const saving = ref(false); const formRef = ref(null)
const form = reactive({ id: null, year: new Date().getFullYear(), verification_agency: '', verifier: '', start_date: null, end_date: null, reported_emission: 0, verified_emission: 0, status: '待核查', conclusion: '', evidence_hash: '' })
const rules = { year: [{ required: true, message: '请输入年份', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try { const res = await listVerifications({ page: page.value, page_size: pageSize.value }); list.value = res.items || []; total.value = res.total || 0 } finally { loading.value = false }
}
function openAdd() { editing.value = false; Object.assign(form, { id: null, year: new Date().getFullYear(), verification_agency: '', verifier: '', start_date: null, end_date: null, reported_emission: 0, verified_emission: 0, status: '待核查', conclusion: '', evidence_hash: '' }); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try { if (editing.value) await updateVerification(form.id, { ...form }); else await createVerification({ ...form }); ElMessage.success('已保存'); visible.value = false; load() } finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm('删除该核查记录？', '提示', { type: 'warning' }).then(async () => { await deleteVerification(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(load)
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; } .filter-bar { display: flex; gap: 12px; margin-bottom: 14px; }</style>
