<template>
  <div class="login">
    <div class="login__card">
      <div class="login__brand">
        <img class="login__logo" src="/assets/logo.png" alt="长沙水泵厂">
        <h1 class="login__title">长泵能碳管理系统</h1>
        <p class="login__sub">Digital Energy &amp; Carbon Management</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="onSubmit" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" size="large" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" size="large" show-password placeholder="请输入密码" @keyup.enter="onSubmit" />
        </el-form-item>
        <el-button type="primary" size="large" class="login__btn" :loading="loading" @click="onSubmit">登录</el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login as loginApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

onMounted(() => { document.title = '登录 · 长泵能碳管理系统' })

async function onSubmit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await loginApi({ username: form.username, password: form.password })
      userStore.setAuth(res.token, res.user)
      ElMessage.success('登录成功')
      const redirect = route.query.redirect || '/dashboard'
      router.push(redirect)
    } catch (e) {
      // 错误已由拦截器提示
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #F5F5F7 0%, #E8F1FF 100%);
}
.login__card {
  width: 380px; background: #fff; border-radius: 16px; box-shadow: var(--shadow-pop);
  padding: 40px 32px;
}
.login__brand { text-align: center; margin-bottom: 28px; }
.login__logo { width: 280px; max-width: 100%; height: auto; object-fit: contain; margin-bottom: 8px; }
.login__title { font-size: 22px; font-weight: 600; margin: 12px 0 4px; }
.login__sub { font-size: 12px; color: var(--c-text-3); margin: 0; letter-spacing: 0.5px; }
.login__btn { width: 100%; margin-top: 8px; }
.login__hint { text-align: center; font-size: 12px; color: var(--c-text-3); margin-top: 16px; }
</style>
