<template>
  <div class="layout">
    <aside class="layout__side">
      <div class="layout__logo">
        <img class="layout__logo-img" src="/assets/logo.png" alt="长沙水泵厂">
        <span class="layout__logo-text">长泵能碳管理系统</span>
      </div>
      <el-scrollbar class="layout__menu">
        <template v-for="group in menu" :key="group.title">
          <div class="layout__group">{{ group.title }}</div>
          <div
            v-for="item in group.items"
            :key="item.name"
            class="layout__menu-item"
            :class="{ 'is-active': isActive(item), 'is-disabled': !item.to }"
            @click="go(item)"
          >
            <span>{{ item.label }}</span>
          </div>
        </template>
      </el-scrollbar>
    </aside>

    <div class="layout__main">
      <header class="layout__header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item v-for="(b, i) in breadcrumb" :key="i">{{ b }}</el-breadcrumb-item>
        </el-breadcrumb>
        <div class="layout__user">
          <el-dropdown @command="onCommand">
            <span class="layout__user-trigger">
              <el-avatar :size="28" style="background:#0071E3">{{ userInitial }}</el-avatar>
              <span class="layout__user-name">{{ userStore.name }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="change">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="layout__content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="pwdVisible" title="修改密码" width="420px" append-to-body>
      <el-form ref="pwdRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPwd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { changePassword } from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const userInitial = computed(() => (userStore.name || '管').slice(0, 1))

// 完整菜单结构（顺序与规范一致，所有模块均已开发并可直接跳转）
const menu = [
  { title: '', items: [
    { label: '首页看板', name: 'dashboard', to: { name: 'dashboard' } },
    { label: '数据大屏', name: 'screen', to: { name: 'screen' } }
  ]},
  { title: '能源消费', items: [
    { label: '综合能耗', name: 'energy-comprehensive', to: { name: 'energy-comprehensive' } },
    { label: '单元统计', name: 'energy-unit-stat', to: { name: 'energy-unit-stat' } },
    { label: '计量查询', name: 'energy-meter-query', to: { name: 'energy-meter-query' } },
    { label: '单元查询', name: 'energy-unit-query', to: { name: 'energy-unit-query' } },
    { label: '能效统计', name: 'energy-efficiency', to: { name: 'energy-efficiency' } },
    { label: '生产数据', name: 'energy-production', to: { name: 'energy-production' } },
    { label: '录接数据', name: 'energy-manual-entry', to: { name: 'energy-manual-entry' } }
  ]},
  { title: '能源分析', items: [
    { label: '计量对标', name: 'analysis-meter-compare', to: { name: 'analysis-meter-compare' } },
    { label: '计量环比', name: 'analysis-meter-ratio', to: { name: 'analysis-meter-ratio' } },
    { label: '单元对标', name: 'analysis-unit-compare', to: { name: 'analysis-unit-compare' } },
    { label: '单元环比', name: 'analysis-unit-ratio', to: { name: 'analysis-unit-ratio' } }
  ]},
  { title: '能效对标', items: [
    { label: '能效测评', name: 'efficiency-assessment', to: { name: 'efficiency-assessment' } }
  ]},
  { title: '能流分析', items: [
    { label: '能流桑基图', name: 'energy-flow', to: { name: 'energy-flow' } },
    { label: '能效平衡', name: 'energy-balance', to: { name: 'energy-balance' } }
  ]},
  { title: '预算管理', items: [
    { label: '用能预算', name: 'budget-energy', to: { name: 'budget-energy' } },
    { label: '碳排放预算', name: 'budget-carbon', to: { name: 'budget-carbon' } }
  ]},
  { title: '碳排放', items: [
    { label: '碳排放核算', name: 'carbon-accounting', to: { name: 'carbon-accounting' } },
    { label: '碳排统计', name: 'carbon-statistics', to: { name: 'carbon-statistics' } },
    { label: '碳排报告', name: 'carbon-report', to: { name: 'carbon-report' } },
    { label: '产品碳足迹', name: 'carbon-footprint', to: { name: 'carbon-footprint' } },
    { label: '供应链碳管理', name: 'carbon-supply-chain', to: { name: 'carbon-supply-chain' } },
    { label: '碳核查支撑', name: 'carbon-verification', to: { name: 'carbon-verification' } },
    { label: '碳核算存证', name: 'carbon-evidence', to: { name: 'carbon-evidence' } },
    { label: '碳资产管理', name: 'carbon-assets', to: { name: 'carbon-assets' } },
    { label: '配额管理', name: 'carbon-quota', to: { name: 'carbon-quota' } }
  ]},
  { title: '系统管理', items: [
    { label: '企业信息', name: 'system-organization', to: { name: 'system-organization' } },
    { label: '能源类型管理', name: 'system-energy-type', to: { name: 'system-energy-type' } },
    { label: '用能单元管理', name: 'system-unit-manage', to: { name: 'system-unit-manage' } },
    { label: '表计管理', name: 'system-meter-manage', to: { name: 'system-meter-manage' } },
    { label: '产品管理', name: 'system-product-manage', to: { name: 'system-product-manage' } },
    { label: '排放源管理', name: 'system-source-manage', to: { name: 'system-source-manage' } },
    { label: '碳因子管理', name: 'system-factor-manage', to: { name: 'system-factor-manage' } },
    { label: '操作日志', name: 'system-logs', to: { name: 'system-logs' } }
  ]}
]

function isActive(item) {
  return route.name === item.name
}
function go(item) {
  if (!item.to) {
    ElMessage.info('该模块将在后续步骤开发')
    return
  }
  router.push(item.to)
}

const breadcrumb = computed(() => {
  const map = {
    'dashboard': ['首页看板'],
    'screen': ['数据大屏'],
    'system-organization': ['系统管理', '企业信息'],
    'system-energy-type': ['系统管理', '能源类型管理'],
    'system-unit-manage': ['系统管理', '用能单元管理'],
    'system-meter-manage': ['系统管理', '表计管理'],
    'system-product-manage': ['系统管理', '产品管理'],
    'system-source-manage': ['系统管理', '排放源管理'],
    'system-factor-manage': ['系统管理', '碳因子管理'],
    'system-logs': ['系统管理', '操作日志'],
    'energy-comprehensive': ['能源消费', '综合能耗'],
    'energy-unit-stat': ['能源消费', '单元统计'],
    'energy-meter-query': ['能源消费', '计量查询'],
    'energy-unit-query': ['能源消费', '单元查询'],
    'energy-efficiency': ['能源消费', '能效统计'],
    'energy-production': ['能源消费', '生产数据'],
    'energy-manual-entry': ['能源消费', '录接数据'],
    'analysis-meter-compare': ['能源分析', '计量对标'],
    'analysis-meter-ratio': ['能源分析', '计量环比'],
    'analysis-unit-compare': ['能源分析', '单元对标'],
    'analysis-unit-ratio': ['能源分析', '单元环比'],
    'efficiency-assessment': ['能效对标', '能效测评'],
    'energy-flow': ['能流分析', '能流桑基图'],
    'energy-balance': ['能流分析', '能效平衡'],
    'budget-energy': ['预算管理', '用能预算'],
    'budget-carbon': ['预算管理', '碳排放预算'],
    'carbon-accounting': ['碳排放', '碳排放核算'],
    'carbon-statistics': ['碳排放', '碳排统计'],
    'carbon-report': ['碳排放', '碳排报告'],
    'carbon-footprint': ['碳排放', '产品碳足迹'],
    'carbon-supply-chain': ['碳排放', '供应链碳管理'],
    'carbon-verification': ['碳排放', '碳核查支撑'],
    'carbon-evidence': ['碳排放', '碳核算存证'],
    'carbon-assets': ['碳排放', '碳资产管理'],
    'carbon-quota': ['碳排放', '配额管理']
  }
  return map[route.name] || ['首页看板']
})

// 修改密码
const pwdVisible = ref(false)
const pwdRef = ref(null)
const pwdForm = ref({ old_password: '', new_password: '' })
const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [{ required: true, min: 6, message: '新密码至少 6 位', trigger: 'blur' }]
}

function onCommand(cmd) {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' })
      .then(() => {
        userStore.logout()
        router.push('/login')
      }).catch(() => {})
  } else if (cmd === 'change') {
    pwdForm.value = { old_password: '', new_password: '' }
    pwdVisible.value = true
  }
}

async function submitPwd() {
  await pwdRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await changePassword(pwdForm.value)
      ElMessage.success('密码已修改，请重新登录')
      pwdVisible.value = false
      userStore.logout()
      router.push('/login')
    } catch (e) {}
  })
}
</script>

<style scoped>
.layout { display: flex; height: 100vh; background: var(--c-bg-2); }
.layout__side {
  width: 240px; background: #fff; border-right: 1px solid var(--c-border-light);
  display: flex; flex-direction: column;
}
.layout__logo {
  display: flex; flex-direction: column; align-items: flex-start; gap: 8px;
  padding: 16px 20px 14px; font-size: 15px; font-weight: 600; color: var(--c-text);
}
.layout__logo-img { width: 100%; max-width: 200px; height: auto; object-fit: contain; }
.layout__logo-text { font-size: 15px; font-weight: 600; line-height: 1.3; }
.layout__menu { flex: 1; padding: 8px 12px 20px; }
.layout__group {
  font-size: 12px; color: var(--c-text-3); padding: 14px 12px 6px; font-weight: 500;
}
.layout__group:first-child { padding-top: 4px; }
.layout__menu-item {
  display: flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: 8px;
  font-size: 14px; color: var(--c-text); cursor: pointer; margin-bottom: 2px;
  transition: background 0.2s ease;
}
.layout__menu-item:hover { background: var(--c-bg-2); }
.layout__menu-item.is-active { background: #E8F1FF; color: var(--c-brand); font-weight: 500; }
.layout__menu-item.is-disabled { color: var(--c-text-3); cursor: not-allowed; opacity: 0.6; }
.layout__menu-item.is-disabled:hover { background: transparent; }

.layout__main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.layout__header {
  height: 56px; background: #fff; border-bottom: 1px solid var(--c-border-light);
  display: flex; align-items: center; justify-content: space-between; padding: 0 24px;
}
.layout__user-trigger { display: flex; align-items: center; gap: 8px; cursor: pointer; outline: none; }
.layout__user-name { font-size: 14px; color: var(--c-text); }
.layout__content { flex: 1; overflow: auto; }
</style>
