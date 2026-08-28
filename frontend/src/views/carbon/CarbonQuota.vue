<template>
  <div class="page">
    <PageHeader title="配额管理" subtitle="记录碳配额买入 / 卖出交易，跟踪持仓成本" />

    <el-card class="panel">
      <div class="filter-bar">
        <el-button type="primary" @click="openAdd">新增交易</el-button>
      </div>
      <el-table :data="list" border stripe v-loading="loading" :empty-text="'暂无交易'">
        <el-table-column prop="trade_date" label="交易日期" width="120" />
        <el-table-column prop="trade_type" label="类型" width="80">
          <template #default="{ row }"><el-tag :type="row.trade_type === '买入' ? 'success' : 'danger'">{{ row.trade_type }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="market" label="市场" width="120" />
        <el-table-column prop="quantity" label="数量(tCO₂)" align="right" />
        <el-table-column prop="price" label="单价(元)" align="right" />
        <el-table-column prop="total_amount" label="金额(元)" align="right" />
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        <el-table-column label="操作" width="70" align="center">
          <template #default="{ row }"><el-button link type="danger" @click="remove(row)">删除</el-button></template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
    </el-card>

    <el-dialog v-model="visible" title="新增配额交易" width="440px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="交易类型">
          <el-select v-model="form.trade_type" style="width:100%"><el-option label="买入" value="买入" /><el-option label="卖出" value="卖出" /></el-select>
        </el-form-item>
        <el-form-item label="交易日期"><el-date-picker v-model="form.trade_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="市场"><el-input v-model="form.market" /></el-form-item>
        <el-form-item label="数量(tCO₂)" prop="quantity"><el-input v-model.number="form.quantity" type="number" /></el-form-item>
        <el-form-item label="单价(元)"><el-input v-model.number="form.price" type="number" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" /></el-form-item>
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
import { listQuotaRecords, createQuotaRecord, deleteQuotaRecord } from '@/api'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(50); const loading = ref(false)
const visible = ref(false); const saving = ref(false); const formRef = ref(null)
const form = reactive({ id: null, trade_date: '', trade_type: '买入', quantity: 0, price: 0, market: '全国碳市场', remark: '' })
const rules = { quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try { const res = await listQuotaRecords({ page: page.value, page_size: pageSize.value }); list.value = res.items || []; total.value = res.total || 0 } finally { loading.value = false }
}
function openAdd() { Object.assign(form, { id: null, trade_date: '', trade_type: '买入', quantity: 0, price: 0, market: '全国碳市场', remark: '' }); visible.value = true }
async function save() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try { await createQuotaRecord({ ...form }); ElMessage.success('已保存'); visible.value = false; load() } finally { saving.value = false }
  })
}
async function remove(row) {
  await ElMessageBox.confirm('删除该交易？', '提示', { type: 'warning' }).then(async () => { await deleteQuotaRecord(row.id); ElMessage.success('已删除'); load() }).catch(() => {})
}
onMounted(load)
</script>
<style scoped>.pager { margin-top: 16px; justify-content: flex-end; } .filter-bar { display: flex; gap: 12px; margin-bottom: 14px; }</style>
