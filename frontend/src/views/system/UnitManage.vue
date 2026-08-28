<template>
  <div class="page">
    <PageHeader title="用能单元管理" subtitle="支持层级结构（如 厂区 > 车间 > 产线）">
      <template #actions><el-button type="primary" @click="openAdd">新增单元</el-button></template>
    </PageHeader>
    <div class="app-card">
      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="搜索名称" clearable style="width:220px" @keyup.enter="load" />
        <el-button @click="load">查询</el-button>
      </div>
      <el-table :data="list" v-loading="loading" border stripe row-key="id" default-expand-all :tree-props="{ children: 'children' }">
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="area" label="区域" width="140" />
        <el-table-column prop="responsible_person" label="责任人" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
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

    <el-dialog v-model="visible" :title="editing ? '编辑单元' : '新增单元'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="编码" prop="code"><el-input v-model="form.code" :disabled="editing" /></el-form-item>
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="上级单元">
          <el-select v-model="form.parent_id" clearable placeholder="无（顶级）" style="width:100%">
            <el-option v-for="u in flatUnits" :key="u.id" :label="u.name" :value="u.id" :disabled="u.id === form.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="区域"><el-input v-model="form.area" /></el-form-item>
        <el-form-item label="责任人"><el-input v-model="form.responsible_person" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
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
import { listEnergyUnits, createEnergyUnit, updateEnergyUnit, deleteEnergyUnit } from '@/api'

const list = ref([])
const flatUnits = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(100)
const keyword = ref('')
const loading = ref(false)
const visible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref(null)
const form = reactive({ code: '', name: '', parent_id: null, area: '', responsible_person: '', phone: '' })
const rules = { code: [{ required: true, message: '请输入编码', trigger: 'blur' }], name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try {
    const res = await listEnergyUnits({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    list.value = buildTree(res.items)
    flatUnits.value = res.items
    total.value = res.total
  } catch (e) {} finally { loading.value = false }
}
function buildTree(items) {
  const map = {}; const roots = []
  items.forEach(i => { map[i.id] = { ...i, children: [] } })
  items.forEach(i => {
    if (i.parent_id && map[i.parent_id]) map[i.parent_id].children.push(map[i.id])
    else roots.push(map[i.id])
  })
  return roots
}
function resetForm() { Object.assign(form, { code: '', name: '', parent_id: null, area: '', responsible_person: '', phone: '' }) }
function openAdd() { editing.value = false; resetForm(); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editing.value) await updateEnergyUnit(form.id, { ...form, id: undefined })
      else await createEnergyUnit(form)
      ElMessage.success('已保存'); visible.value = false; load()
    } catch (e) {} finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' })
    .then(async () => { await deleteEnergyUnit(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(load)
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; }</style>
