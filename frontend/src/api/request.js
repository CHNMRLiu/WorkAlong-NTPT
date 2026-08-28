import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截：注入 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => Promise.reject(error))

// 响应拦截：统一解析 {code, message, data}
request.interceptors.response.use((resp) => {
  const body = resp.data
  // 非统一格式（如直接返回对象）透传
  if (body && typeof body === 'object' && 'code' in body) {
    if (body.code === 0) {
      return body.data
    } else {
      ElMessage.error(body.message || '操作失败')
      return Promise.reject(new Error(body.message))
    }
  }
  return body
}, (error) => {
  const status = error.response?.status
  if (status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    ElMessage.error('登录已过期，请重新登录')
    if (router.currentRoute.value.name !== 'login') {
      router.push('/login')
    }
  } else {
    const msg = error.response?.data?.detail || error.response?.data?.message || '网络错误'
    ElMessage.error(msg)
  }
  return Promise.reject(error)
})

export default request
