<template>
  <div class="page">
    <PageHeader title="碳因子管理" subtitle="维护碳排放因子库（来源 IPCC / 生态环境部等）">
      <template #actions><el-button type="primary" @click="openAdd">新增因子</el-button></template>
    </PageHeader>
    <div class="app-card">
      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="搜索名称" clearable style="width:220px" @keyup.enter="load" />
        <el-button @click="load">查询</el-button>
      </div>
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="因子值" width="140" align="right">
          <template #default="{ row }">{{ Number(row.factor_value || 0).toLocaleString('zh-CN', { maximumFractionDigits: 6 }) }}</template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="140" />
        <el-table-column prop="source" label="来源" width="160" />
        <el-table-column prop="effective_date" label="生效日期" width="120" />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next"
        :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
    </div>

    <el-dialog v-model="visible" :title="editing ? '编辑因子' : '新增因子'" width="440px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="因子值" prop="factor_value"><el-input v-model.number="form.factor_value" type="number" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" placeholder="如 kgCO2/kWh" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="form.source" placeholder="如 IPCC / 生态环境部" /></el-form-item>
        <el-form-item label="生效日期"><el-date-picker v-model="form.effective_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
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
import { listCarbonFactors, createCarbonFactor, updateCarbonFactor, deleteCarbonFactor } from '@/api'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(100)
const keyword = ref('')
const loading = ref(false)
const visible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref(null)
const form = reactive({ name: '', factor_value: 0, unit: '', source: '', effective_date: '' })
const rules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }], factor_value: [{ required: true, message: '请输入因子值', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try { const res = await listCarbonFactors({ page: page.value, page_size: pageSize.value, keyword: keyword.value }); list.value = res.items; total.value = res.total } catch (e) {} finally { loading.value = false }
}
function resetForm() { Object.assign(form, { name: '', factor_value: 0, unit: '', source: '', effective_date: '' }) }
function openAdd() { editing.value = false; resetForm(); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try { if (editing.value) await updateCarbonFactor(form.id, { ...form, id: undefined }); else await createCarbonFactor(form); ElMessage.success('已保存'); visible.value = false; load() } catch (e) {} finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' }).then(async () => { await deleteCarbonFactor(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(load)
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; }</style>
