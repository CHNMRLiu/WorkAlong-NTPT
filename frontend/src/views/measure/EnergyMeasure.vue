<template>
  <div class="page">
    <PageHeader title="能效测评" subtitle="设置能效指标基准，录入能耗与产量，自动计算单位产品能耗与达标等级" />

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card class="panel">
          <template #header><span class="panel__title">能效指标</span>
            <el-button style="float:right" type="primary" size="small" @click="openIndicator">新增指标</el-button>
          </template>
          <el-table :data="indicators" border stripe v-loading="loadingInd" :empty-text="'暂无指标'">
            <el-table-column prop="name" label="指标名称" />
            <el-table-column prop="benchmark_value" label="基准值" align="right" width="100" />
            <el-table-column prop="target_value" label="目标值" align="right" width="100" />
            <el-table-column prop="unit" label="单位" width="90" />
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ row }">
                <el-button link type="danger" @click="removeIndicator(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card class="panel">
          <template #header><span class="panel__title">测评录入</span></template>
          <el-form :inline="true" @submit.prevent>
            <el-form-item label="指标" required>
              <el-select v-model="form.indicator_id" placeholder="选择指标" style="width:160px">
                <el-option v-for="i in indicators" :key="i.id" :label="i.name" :value="i.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="统计日期" required>
              <el-date-picker v-model="form.stat_date" type="date" value-format="YYYY-MM-DDTHH:mm:ss" style="width:170px" />
            </el-form-item>
            <el-form-item label="能耗量" required>
              <el-input v-model.number="form.energy_consumption" type="number" style="width:120px" />
            </el-form-item>
            <el-form-item label="产量" required>
              <el-input v-model.number="form.output" type="number" style="width:120px" />
            </el-form-item>
            <el-form-item label="基准值">
              <el-input v-model.number="form.benchmark_value" type="number" style="width:120px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="submit">计算测评</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="panel" style="margin-top:16px">
          <template #header><span class="panel__title">测评记录</span></template>
          <el-table :data="assessments" border stripe v-loading="loadingAst" :empty-text="'暂无记录'">
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="stat_date" label="日期" width="120" />
            <el-table-column prop="energy_consumption" label="能耗" align="right" />
            <el-table-column prop="output" label="产量" align="right" />
            <el-table-column prop="actual_value" label="单位能耗" align="right" />
            <el-table-column prop="benchmark_value" label="基准" align="right" />
            <el-table-column prop="deviation" label="偏差%" align="right" />
            <el-table-column prop="level" label="等级" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.level === '达标' ? 'success' : (row.level === '优秀' ? 'primary' : 'danger')">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ row }"><el-button link type="danger" @click="removeAssessment(row)">删除</el-button></template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="indVisible" :title="indEditing ? '编辑指标' : '新增指标'" width="440px">
      <el-form ref="indRef" :model="indForm" :rules="indRules" label-width="90px">
        <el-form-item label="名称" prop="name"><el-input v-model="indForm.name" /></el-form-item>
        <el-form-item label="基准值"><el-input v-model.number="indForm.benchmark_value" type="number" /></el-form-item>
        <el-form-item label="目标值"><el-input v-model.number="indForm.target_value" type="number" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="indForm.unit" placeholder="如 kgce/t" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="indVisible = false">取消</el-button>
        <el-button type="primary" @click="saveIndicator">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import {
  listIndicators, createIndicator, deleteIndicator,
  listAssessments, createAssessment, deleteAssessment
} from '@/api'

const indicators = ref([])
const assessments = ref([])
const loadingInd = ref(false)
const loadingAst = ref(false)
const saving = ref(false)

const form = reactive({ indicator_id: null, stat_date: '', energy_consumption: 0, output: 0, benchmark_value: 0 })

const indVisible = ref(false)
const indEditing = ref(false)
const indRef = ref(null)
const indForm = reactive({ id: null, name: '', benchmark_value: 0, target_value: 0, unit: '' })
const indRules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }

async function loadIndicators() {
  loadingInd.value = true
  try { indicators.value = await listIndicators() } finally { loadingInd.value = false }
}
async function loadAssessments() {
  loadingAst.value = true
  try {
    const res = await listAssessments({ page: 1, page_size: 200 })
    assessments.value = res.items || []
  } finally { loadingAst.value = false }
}

function openIndicator() { indEditing.value = false; Object.assign(indForm, { id: null, name: '', benchmark_value: 0, target_value: 0, unit: '' }); indVisible.value = true }
async function saveIndicator() {
  await indRef.value.validate(async (valid) => {
    if (!valid) return
    await createIndicator({ ...indForm, id: undefined })
    ElMessage.success('已保存'); indVisible.value = false; loadIndicators()
  })
}
async function removeIndicator(row) {
  await ElMessageBox.confirm(`删除指标「${row.name}」？`, '提示', { type: 'warning' })
    .then(async () => { await deleteIndicator(row.id); ElMessage.success('已删除'); loadIndicators() }).catch(() => {})
}
async function submit() {
  if (!form.indicator_id) return ElMessage.warning('请选择指标')
  if (!form.stat_date) return ElMessage.warning('请选择日期')
  saving.value = true
  try {
    await createAssessment({ ...form })
    ElMessage.success('测评完成'); loadAssessments()
  } finally { saving.value = false }
}
async function removeAssessment(row) {
  await ElMessageBox.confirm('删除该测评记录？', '提示', { type: 'warning' })
    .then(async () => { await deleteAssessment(row.id); ElMessage.success('已删除'); loadAssessments() }).catch(() => {})
}

onMounted(() => { loadIndicators(); loadAssessments() })
</script>
