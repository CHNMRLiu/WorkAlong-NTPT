import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  // 数据大屏：顶级路由，全屏展示（无侧边栏布局）
  { path: '/screen', name: 'screen', component: () => import('@/views/screen/DataScreen.vue'), meta: { title: '数据大屏' } },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      // 看板
      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '首页看板' } },

      // 系统管理
      { path: 'system/organization', name: 'system-organization', component: () => import('@/views/system/Organization.vue'), meta: { title: '企业信息' } },
      { path: 'system/energy-type', name: 'system-energy-type', component: () => import('@/views/system/EnergyType.vue'), meta: { title: '能源类型' } },
      { path: 'system/unit-manage', name: 'system-unit-manage', component: () => import('@/views/system/UnitManage.vue'), meta: { title: '用能单元' } },
      { path: 'system/meter-manage', name: 'system-meter-manage', component: () => import('@/views/system/MeterManage.vue'), meta: { title: '表计' } },
      { path: 'system/product-manage', name: 'system-product-manage', component: () => import('@/views/system/ProductManage.vue'), meta: { title: '产品' } },
      { path: 'system/source-manage', name: 'system-source-manage', component: () => import('@/views/system/SourceManage.vue'), meta: { title: '排放源' } },
      { path: 'system/factor-manage', name: 'system-factor-manage', component: () => import('@/views/system/FactorManage.vue'), meta: { title: '碳因子' } },
      { path: 'system/logs', name: 'system-logs', component: () => import('@/views/system/Logs.vue'), meta: { title: '操作日志' } },

      // 能源消费
      { path: 'energy/comprehensive', name: 'energy-comprehensive', component: () => import('@/views/energy/Comprehensive.vue'), meta: { title: '综合能耗' } },
      { path: 'energy/unit-stat', name: 'energy-unit-stat', component: () => import('@/views/energy/UnitStat.vue'), meta: { title: '单元统计' } },
      { path: 'energy/meter-query', name: 'energy-meter-query', component: () => import('@/views/energy/MeterQuery.vue'), meta: { title: '计量查询' } },
      { path: 'energy/unit-query', name: 'energy-unit-query', component: () => import('@/views/energy/UnitQuery.vue'), meta: { title: '单元查询' } },
      { path: 'energy/efficiency', name: 'energy-efficiency', component: () => import('@/views/energy/EfficiencyStat.vue'), meta: { title: '能效统计' } },
      { path: 'energy/production', name: 'energy-production', component: () => import('@/views/energy/Production.vue'), meta: { title: '生产数据' } },
      { path: 'energy/manual-entry', name: 'energy-manual-entry', component: () => import('@/views/energy/ManualEntry.vue'), meta: { title: '录接数据' } },

      // 能源分析
      { path: 'analysis/meter-compare', name: 'analysis-meter-compare', component: () => import('@/views/analysis/MeterCompare.vue'), meta: { title: '计量对标' } },
      { path: 'analysis/meter-ratio', name: 'analysis-meter-ratio', component: () => import('@/views/analysis/MeterTrend.vue'), meta: { title: '计量环比' } },
      { path: 'analysis/unit-compare', name: 'analysis-unit-compare', component: () => import('@/views/analysis/UnitCompare.vue'), meta: { title: '单元对标' } },
      { path: 'analysis/unit-ratio', name: 'analysis-unit-ratio', component: () => import('@/views/analysis/UnitTrend.vue'), meta: { title: '单元环比' } },

      // 能效测评
      { path: 'efficiency/assessment', name: 'efficiency-assessment', component: () => import('@/views/measure/EnergyMeasure.vue'), meta: { title: '能效测评' } },

      // 能流分析
      { path: 'energy-flow', name: 'energy-flow', component: () => import('@/views/energyflow/EnergyFlow.vue'), meta: { title: '能流桑基图' } },
      { path: 'energy-balance', name: 'energy-balance', component: () => import('@/views/optimize/EfficiencyBalance.vue'), meta: { title: '能效平衡' } },

      // 预算管理
      { path: 'budget/energy', name: 'budget-energy', component: () => import('@/views/budget/EnergyBudget.vue'), meta: { title: '用能预算' } },
      { path: 'budget/carbon', name: 'budget-carbon', component: () => import('@/views/budget/CarbonBudget.vue'), meta: { title: '碳排放预算' } },

      // 碳排放
      { path: 'carbon/accounting', name: 'carbon-accounting', component: () => import('@/views/carbon/CarbonAccounting.vue'), meta: { title: '碳排放核算' } },
      { path: 'carbon/statistics', name: 'carbon-statistics', component: () => import('@/views/carbon/CarbonStat.vue'), meta: { title: '碳排统计' } },
      { path: 'carbon/report', name: 'carbon-report', component: () => import('@/views/carbon/CarbonReport.vue'), meta: { title: '碳排报告' } },
      { path: 'carbon/footprint', name: 'carbon-footprint', component: () => import('@/views/carbon/CarbonFootprint.vue'), meta: { title: '产品碳足迹' } },
      { path: 'carbon/supply-chain', name: 'carbon-supply-chain', component: () => import('@/views/carbon/SupplyChain.vue'), meta: { title: '供应链碳管理' } },
      { path: 'carbon/verification', name: 'carbon-verification', component: () => import('@/views/carbon/CarbonVerify.vue'), meta: { title: '碳核查支撑' } },
      { path: 'carbon/evidence', name: 'carbon-evidence', component: () => import('@/views/carbon/CarbonEvidence.vue'), meta: { title: '碳核算存证' } },
      { path: 'carbon/assets', name: 'carbon-assets', component: () => import('@/views/carbon/CarbonAsset.vue'), meta: { title: '碳资产管理' } },
      { path: 'carbon/quota', name: 'carbon-quota', component: () => import('@/views/carbon/CarbonQuota.vue'), meta: { title: '配额管理' } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token || localStorage.getItem('token')
  if (to.meta.public) {
    next()
  } else if (!token) {
    next('/login')
  } else {
    if (!userStore.token) userStore.setToken(token)
    next()
  }
})

export default router
