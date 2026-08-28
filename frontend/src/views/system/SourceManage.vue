<template>
  <div class="page">
    <PageHeader title="排放源管理" subtitle="定义温室气体排放源及所属范围（范围1/2/3）">
      <template #actions><el-button type="primary" @click="openAdd">新增排放源</el-button></template>
    </PageHeader>
    <div class="app-card">
      <div class="filter-bar">
        <el-select v-model="scope" placeholder="按范围筛选" clearable style="width:160px" @change="load">
          <el-option label="范围1" value="范围1" /><el-option label="范围2" value="范围2" /><el-option label="范围3" value="范围3" />
        </el-select>
        <el-button @click="load">查询</el-button>
      </div>
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="code" label="编码" width="100" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="范围" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.scope === '范围1' ? 'danger' : row.scope === '范围2' ? 'warning' : 'info'" size="small">{{ row.scope }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="类别" width="120" />
        <el-table-column label="关联因子" width="140">
          <template #default="{ row }">{{ factorName(row.carbon_factor_id) }}</template>
        </el-table-column>
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

    <el-dialog v-model="visible" :title="editing ? '编辑排放源' : '新增排放源'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="编码" prop="code"><el-input v-model="form.code" :disabled="editing" /></el-form-item>
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="范围" prop="scope">
          <el-select v-model="form.scope" style="width:100%">
            <el-option label="范围1" value="范围1" /><el-option label="范围2" value="范围2" /><el-option label="范围3" value="范围3" />
          </el-select>
        </el-form-item>
        <el-form-item label="类别"><el-input v-model="form.category" /></el-form-item>
        <el-form-item label="关联碳因子">
          <el-select v-model="form.carbon_factor_id" clearable style="width:100%">
            <el-option v-for="f in factors" :key="f.id" :label="f.name" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
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
import { listEmissionSources, createEmissionSource, updateEmissionSource, deleteEmissionSource, listCarbonFactors } from '@/api'

const list = ref([])
const factors = ref([])
const factorMap = ref({})
const total = ref(0)
const page = ref(1)
const pageSize = ref(100)
const scope = ref('')
const loading = ref(false)
const visible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref(null)
const form = reactive({ code: '', name: '', scope: '范围1', category: '', carbon_factor_id: null, remark: '' })
const rules = { code: [{ required: true, message: '请输入编码', trigger: 'blur' }], name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }
function factorName(id) { return factorMap.value[id] || '—' }

async function load() {
  loading.value = true
  try { const res = await listEmissionSources({ page: page.value, page_size: pageSize.value, scope: scope.value }); list.value = res.items; total.value = res.total } catch (e) {} finally { loading.value = false }
}
async function loadFactors() {
  const f = await listCarbonFactors({ page: 1, page_size: 200 })
  factors.value = f.items
  factorMap.value = Object.fromEntries(f.items.map(x => [x.id, x.name]))
}
function resetForm() { Object.assign(form, { code: '', name: '', scope: '范围1', category: '', carbon_factor_id: null, remark: '' }) }
function openAdd() { editing.value = false; resetForm(); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try { if (editing.value) await updateEmissionSource(form.id, { ...form, id: undefined }); else await createEmissionSource(form); ElMessage.success('已保存'); visible.value = false; load() } catch (e) {} finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' }).then(async () => { await deleteEmissionSource(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(() => { loadFactors(); load() })
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; }</style>
