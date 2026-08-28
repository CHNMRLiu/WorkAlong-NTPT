<template>
  <div class="page">
    <PageHeader title="能源类型管理" subtitle="定义能源种类、折标煤系数与碳排放因子（计算口径基准）">
      <template #actions>
        <el-button type="primary" @click="openAdd">新增能源类型</el-button>
      </template>
    </PageHeader>

    <div class="app-card">
      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="搜索名称" clearable style="width:220px" @keyup.enter="load" />
        <el-button @click="load">查询</el-button>
      </div>
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="unit" label="单位" width="80" />
        <el-table-column label="折标煤系数" width="120" align="right">
          <template #default="{ row }">{{ fmt(row.standard_coal_coefficient, 6) }}</template>
        </el-table-column>
        <el-table-column label="碳排放因子" width="120" align="right">
          <template #default="{ row }">{{ fmt(row.carbon_factor, 6) }}</template>
        </el-table-column>
        <el-table-column label="默认单价(元)" width="120" align="right">
          <template #default="{ row }">{{ fmt(row.default_price, 2) }}</template>
        </el-table-column>
        <el-table-column label="外购电" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_purchased_electricity ? 'info' : 'default'" size="small">
              {{ row.is_purchased_electricity ? '是' : '否' }}
            </el-tag>
          </template>
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

    <el-dialog v-model="visible" :title="editing ? '编辑能源类型' : '新增能源类型'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="form.code" :disabled="editing" placeholder="唯一编码，如 electricity" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.unit" />
        </el-form-item>
        <el-form-item label="折标煤系数">
          <el-input v-model.number="form.standard_coal_coefficient" type="number" />
        </el-form-item>
        <el-form-item label="碳排放因子">
          <el-input v-model.number="form.carbon_factor" type="number" />
        </el-form-item>
        <el-form-item label="默认单价(元)">
          <el-input v-model.number="form.default_price" type="number" />
        </el-form-item>
        <el-form-item label="是否外购电">
          <el-switch v-model="form.is_purchased_electricity" />
        </el-form-item>
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
import { listEnergyTypes, createEnergyType, updateEnergyType, deleteEnergyType } from '@/api'

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
const form = reactive({
  code: '', name: '', unit: 'kWh', standard_coal_coefficient: 0,
  carbon_factor: 0, default_price: 0, is_purchased_electricity: false
})
const rules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

function fmt(v, d) {
  return Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d })
}

async function load() {
  loading.value = true
  try {
    const res = await listEnergyTypes({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    list.value = res.items
    total.value = res.total
  } catch (e) {} finally { loading.value = false }
}

function resetForm() {
  Object.assign(form, {
    code: '', name: '', unit: 'kWh', standard_coal_coefficient: 0,
    carbon_factor: 0, default_price: 0, is_purchased_electricity: false
  })
}
function openAdd() { editing.value = false; resetForm(); visible.value = true }
function openEdit(row) {
  editing.value = true
  Object.assign(form, row)
  visible.value = true
}
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editing.value) {
        await updateEnergyType(form.id, { ...form, id: undefined })
      } else {
        await createEnergyType(form)
      }
      ElMessage.success('已保存')
      visible.value = false
      load()
    } catch (e) {} finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' })
    .then(async () => {
      await deleteEnergyType(row.id)
      ElMessage.success('已删除')
      load()
    }).catch(() => {})
}

onMounted(load)
</script>

<style scoped>
.pager { margin-top: 16px; justify-content: flex-end; }
</style>
