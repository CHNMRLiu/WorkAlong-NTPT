<template>
  <div class="page">
    <PageHeader title="产品碳足迹" subtitle="核算产品全生命周期碳排放（原料→生产→运输→使用→回收）" />

    <el-card class="panel">
      <div class="filter-bar">
        <el-button type="primary" @click="openAdd">新增核算</el-button>
        <el-button type="success" :loading="allocating" @click="allocate">按产量分摊公司排放</el-button>
        <span class="tip">依据「碳排放核算」总排放与「生产数据」各产品产量，自动生成各产品的生产碳排</span>
      </div>
      <el-table :data="list" border stripe v-loading="loading" :empty-text="'暂无足迹'">
        <el-table-column label="产品" width="140"><template #default="{ row }">{{ prodName(row.product_id) }}</template></el-table-column>
        <el-table-column prop="functional_unit" label="功能单位" width="110" />
        <el-table-column prop="boundary" label="边界" width="120" />
        <el-table-column prop="raw_material" label="原料(kgCO₂)" align="right" />
        <el-table-column prop="production" label="生产(kgCO₂)" align="right" />
        <el-table-column prop="transport" label="运输(kgCO₂)" align="right" />
        <el-table-column prop="use_phase" label="使用(kgCO₂)" align="right" />
        <el-table-column prop="disposal" label="回收(kgCO₂)" align="right" />
        <el-table-column prop="total" label="合计(kgCO₂)" align="right" />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
    </el-card>

    <el-dialog v-model="visible" :title="editing ? '编辑足迹' : '新增足迹'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="产品" prop="product_id">
          <el-select v-model="form.product_id" style="width:100%">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="功能单位"><el-input v-model="form.functional_unit" placeholder="如 1件/1吨" /></el-form-item>
        <el-form-item label="核算边界">
          <el-select v-model="form.boundary" style="width:100%">
            <el-option label="从摇篮到大门" value="从摇篮到大门" /><el-option label="从摇篮到坟墓" value="从摇篮到坟墓" /><el-option label="从大门到大门" value="从大门到大门" />
          </el-select>
        </el-form-item>
        <el-form-item label="原料碳排"><el-input v-model.number="form.raw_material" type="number" /></el-form-item>
        <el-form-item label="生产碳排"><el-input v-model.number="form.production" type="number" /></el-form-item>
        <el-form-item label="运输碳排"><el-input v-model.number="form.transport" type="number" /></el-form-item>
        <el-form-item label="使用碳排"><el-input v-model.number="form.use_phase" type="number" /></el-form-item>
        <el-form-item label="回收处理"><el-input v-model.number="form.disposal" type="number" /></el-form-item>
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
import { listFootprints, createFootprint, updateFootprint, deleteFootprint, listProducts, autoAllocateFootprint } from '@/api'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(50); const loading = ref(false)
const allocating = ref(false)
const products = ref([]); const prodMap = ref({})
const visible = ref(false); const editing = ref(false); const saving = ref(false); const formRef = ref(null)
const form = reactive({ id: null, product_id: null, functional_unit: '', boundary: '从摇篮到大门', raw_material: 0, production: 0, transport: 0, use_phase: 0, disposal: 0 })
const rules = { product_id: [{ required: true, message: '请选择产品', trigger: 'change' }] }
const prodName = (id) => prodMap.value[id] || `产品#${id}`

async function load() {
  loading.value = true
  try { const res = await listFootprints({ page: page.value, page_size: pageSize.value }); list.value = res.items || []; total.value = res.total || 0 } finally { loading.value = false }
}
function openAdd() { editing.value = false; Object.assign(form, { id: null, product_id: null, functional_unit: '', boundary: '从摇篮到大门', raw_material: 0, production: 0, transport: 0, use_phase: 0, disposal: 0 }); visible.value = true }
function openEdit(row) { editing.value = true; Object.assign(form, row); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try { if (editing.value) await updateFootprint(form.id, { ...form }); else await createFootprint({ ...form }); ElMessage.success('已保存'); visible.value = false; load() } finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm('删除该足迹？', '提示', { type: 'warning' }).then(async () => { await deleteFootprint(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
async function allocate() {
  allocating.value = true
  try {
    const res = await autoAllocateFootprint(new Date().getFullYear())
    ElMessage.success(res.message || '已按产量分摊'); load()
  } catch (e) { ElMessage.error('分摊失败：请先录入生产数据') } finally { allocating.value = false }
}
onMounted(async () => { const p = await listProducts(); products.value = p.items || p; prodMap.value = Object.fromEntries(products.value.map(x => [x.id, x.name])); load() })
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; } .filter-bar { display: flex; gap: 12px; margin-bottom: 14px; align-items: center; } .tip { font-size: 12px; color: #8A8A8E; }</style>
