<template>
  <div class="page">
    <PageHeader title="生产数据" subtitle="录入产品产量与产值，是能效统计与单位产品能耗计算的基础" />

    <div class="filter-bar">
      <el-select v-model="filter.product_id" placeholder="选择产品" clearable filterable style="width:220px" @change="loadData">
        <el-option v-for="p in products" :key="p.id" :label="`${p.name}（${p.code}）`" :value="p.id" />
      </el-select>
      <el-date-picker v-model="filter.start" type="date" placeholder="起始" value-format="YYYY-MM-DD" style="width:150px" @change="loadData" />
      <el-date-picker v-model="filter.end" type="date" placeholder="结束" value-format="YYYY-MM-DD" style="width:150px" @change="loadData" />
      <el-button type="primary" @click="openDialog()">新增生产数据</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border stripe class="apple-table">
      <el-table-column type="index" label="#" width="55" align="center" />
      <el-table-column prop="stat_date" label="统计日期" min-width="160" />
      <el-table-column label="产品" min-width="150">
        <template #default="{ row }">{{ productName(row.product_id) }}</template>
      </el-table-column>
      <el-table-column label="用能单元" min-width="140">
        <template #default="{ row }">{{ row.unit_id ? unitName(row.unit_id) : '—' }}</template>
      </el-table-column>
      <el-table-column prop="output" label="产量" width="130" align="right">
        <template #default="{ row }">{{ fmt(row.output) }} {{ row.output_unit }}</template>
      </el-table-column>
      <el-table-column prop="output_value" label="产值(元)" width="140" align="right">
        <template #default="{ row }">{{ fmt(row.output_value) }}</template>
      </el-table-column>
      <el-table-column prop="period" label="周期" width="90" align="center" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
                   layout="total, prev, pager, next" class="apple-pager" @current-change="loadData" />

    <el-dialog v-model="visible" :title="form.id ? '编辑生产数据' : '新增生产数据'" width="480px" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-form-item label="产品" prop="product_id">
          <el-select v-model="form.product_id" placeholder="选择产品" filterable style="width:100%">
            <el-option v-for="p in products" :key="p.id" :label="`${p.name}（${p.code}）`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用能单元">
          <el-select v-model="form.unit_id" placeholder="选填" filterable clearable style="width:100%">
            <el-option v-for="u in units" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="统计日期" prop="stat_date">
          <el-date-picker v-model="form.stat_date" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="产量" prop="output">
          <el-input-number v-model="form.output" :precision="2" :min="0" :step="1" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="产量单位">
          <el-input v-model="form.output_unit" placeholder="如：吨" style="width:100%" />
        </el-form-item>
        <el-form-item label="产值(元)">
          <el-input-number v-model="form.output_value" :precision="2" :min="0" :step="1000" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="周期">
          <el-select v-model="form.period" style="width:100%">
            <el-option label="月" value="月" /><el-option label="季" value="季" /><el-option label="年" value="年" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import { listProducts, listEnergyUnits, listProduction, createProduction, updateProduction, deleteProduction } from '@/api'

const fmt = (v) => (v == null ? '0' : Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 2 }))

const products = ref([])
const units = ref([])
const productMap = ref({})
const unitMap = ref({})
const productName = (id) => productMap.value[id] || `产品#${id}`
const unitName = (id) => unitMap.value[id] || `单元#${id}`

const rows = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const filter = reactive({ product_id: null, start: '', end: '' })

async function loadBasics() {
  const [p, u] = await Promise.all([listProducts(), listEnergyUnits()])
  products.value = p.items || p || []
  units.value = u.items || u || []
  productMap.value = Object.fromEntries(products.value.map(x => [x.id, x.name]))
  unitMap.value = Object.fromEntries(units.value.map(x => [x.id, x.name]))
}

async function loadData() {
  loading.value = true
  try {
    const res = await listProduction({
      page: page.value, page_size: pageSize.value,
      product_id: filter.product_id || undefined,
      start: filter.start || undefined, end: filter.end || undefined
    })
    rows.value = res.items || []
    total.value = res.total || 0
  } finally { loading.value = false }
}

const visible = ref(false)
const saving = ref(false)
const formRef = ref(null)
const form = ref({ id: null, product_id: null, unit_id: null, stat_date: '', output: 0, output_unit: '吨', output_value: 0, period: '月', remark: '' })
const rules = {
  product_id: [{ required: true, message: '请选择产品', trigger: 'change' }],
  stat_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  output: [{ required: true, message: '请输入产量', trigger: 'blur' }]
}

function openDialog(row) {
  form.value = row
    ? { ...row }
    : { id: null, product_id: null, unit_id: null, stat_date: '', output: 0, output_unit: '吨', output_value: 0, period: '月', remark: '' }
  visible.value = true
}

async function submit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const f = { ...form.value }
      if (f.id) { await updateProduction(f.id, f) } else { await createProduction(f) }
      ElMessage.success('已保存'); visible.value = false; loadData()
    } finally { saving.value = false }
  })
}

async function remove(row) {
  await ElMessageBox.confirm('确定删除该生产数据？', '提示', { type: 'warning' })
  await deleteProduction(row.id); ElMessage.success('已删除'); loadData()
}

onMounted(() => { loadBasics(); loadData() })
</script>

<style scoped>
.filter-bar { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
.apple-table { border-radius: 12px; overflow: hidden; box-shadow: var(--c-shadow-card); }
.apple-pager { margin-top: 16px; justify-content: flex-end; }
</style>
