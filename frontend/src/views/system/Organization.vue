<template>
  <div class="page">
    <PageHeader title="企业信息" subtitle="维护企业基础档案，碳报告将自动带入" />
    <div class="app-card" style="max-width:640px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="企业名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入企业名称" />
        </el-form-item>
        <el-form-item label="统一社会信用代码">
          <el-input v-model="form.credit_code" placeholder="如 91110000XXXXXXXXXX" />
        </el-form-item>
        <el-form-item label="所属行业">
          <el-input v-model="form.industry" placeholder="如 制造业" />
        </el-form-item>
        <el-form-item label="注册地址">
          <el-input v-model="form.address" placeholder="请输入地址" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="企业规模">
          <el-input v-model="form.scale" placeholder="如 大型" />
        </el-form-item>
        <el-form-item label="成立日期">
          <el-date-picker v-model="form.established_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">保存</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import { getOrganization, updateOrganization } from '@/api'

const formRef = ref(null)
const loading = ref(false)
const form = reactive({
  name: '', credit_code: '', industry: '', address: '', contact: '', phone: '', scale: '', established_date: ''
})
const rules = { name: [{ required: true, message: '请输入企业名称', trigger: 'blur' }] }

onMounted(async () => {
  try {
    const data = await getOrganization()
    Object.assign(form, data)
  } catch (e) {}
})

async function onSubmit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await updateOrganization(form)
      ElMessage.success('已保存')
    } catch (e) {} finally { loading.value = false }
  })
}
</script>
