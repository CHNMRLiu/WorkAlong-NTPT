import request from './request'

// ============ 认证 ============
export const login = (data) => request.post('/auth/login', data)
export const getMe = () => request.get('/auth/me')
export const changePassword = (data) => request.post('/auth/change-password', data)
export const listUsers = () => request.get('/auth/users')

// ============ 系统管理 ============
export const getOrganization = () => request.get('/system/organization')
export const updateOrganization = (data) => request.put('/system/organization', data)

export const listEnergyTypes = (params) => request.get('/system/energy-types', { params })
export const createEnergyType = (data) => request.post('/system/energy-types', data)
export const updateEnergyType = (id, data) => request.put(`/system/energy-types/${id}`, data)
export const deleteEnergyType = (id) => request.delete(`/system/energy-types/${id}`)

export const listEnergyUnits = (params) => request.get('/system/energy-units', { params })
export const createEnergyUnit = (data) => request.post('/system/energy-units', data)
export const updateEnergyUnit = (id, data) => request.put(`/system/energy-units/${id}`, data)
export const deleteEnergyUnit = (id) => request.delete(`/system/energy-units/${id}`)

export const listMeters = (params) => request.get('/system/meters', { params })
export const createMeter = (data) => request.post('/system/meters', data)
export const updateMeter = (id, data) => request.put(`/system/meters/${id}`, data)
export const deleteMeter = (id) => request.delete(`/system/meters/${id}`)

export const listProducts = (params) => request.get('/system/products', { params })
export const createProduct = (data) => request.post('/system/products', data)
export const updateProduct = (id, data) => request.put(`/system/products/${id}`, data)
export const deleteProduct = (id) => request.delete(`/system/products/${id}`)

export const listEmissionSources = (params) => request.get('/system/emission-sources', { params })
export const createEmissionSource = (data) => request.post('/system/emission-sources', data)
export const updateEmissionSource = (id, data) => request.put(`/system/emission-sources/${id}`, data)
export const deleteEmissionSource = (id) => request.delete(`/system/emission-sources/${id}`)

export const listCarbonFactors = (params) => request.get('/system/carbon-factors', { params })
export const createCarbonFactor = (data) => request.post('/system/carbon-factors', data)
export const updateCarbonFactor = (id, data) => request.put(`/system/carbon-factors/${id}`, data)
export const deleteCarbonFactor = (id) => request.delete(`/system/carbon-factors/${id}`)

export const listLogs = (params) => request.get('/system/logs', { params })
export const upsertConfig = (data) => request.post('/system/configs', data)

// ============ 能源消费 ============
export const listMeterReadings = (params) => request.get('/energy/meter-readings', { params })
export const createMeterReading = (data) => request.post('/energy/meter-readings', data)
export const updateMeterReading = (id, data) => request.put(`/energy/meter-readings/${id}`, data)
export const deleteMeterReading = (id) => request.delete(`/energy/meter-readings/${id}`)

export const listManualEntries = (params) => request.get('/energy/manual-entries', { params })
export const createManualEntry = (data) => request.post('/energy/manual-entries', data)
export const updateManualEntry = (id, data) => request.put(`/energy/manual-entries/${id}`, data)
export const deleteManualEntry = (id) => request.delete(`/energy/manual-entries/${id}`)

export const listProduction = (params) => request.get('/energy/production', { params })
export const createProduction = (data) => request.post('/energy/production', data)
export const updateProduction = (id, data) => request.put(`/energy/production/${id}`, data)
export const deleteProduction = (id) => request.delete(`/energy/production/${id}`)

export const listIndicators = () => request.get('/energy/efficiency-indicators')
export const createIndicator = (data) => request.post('/energy/efficiency-indicators', data)
export const deleteIndicator = (id) => request.delete(`/energy/efficiency-indicators/${id}`)

export const listAssessments = (params) => request.get('/energy/efficiency-assessments', { params })
export const createAssessment = (data) => request.post('/energy/efficiency-assessments', data)
export const deleteAssessment = (id) => request.delete(`/energy/efficiency-assessments/${id}`)

export const listFlowNodes = () => request.get('/energy/flow-nodes')
export const createFlowNode = (data) => request.post('/energy/flow-nodes', data)
export const deleteFlowNode = (id) => request.delete(`/energy/flow-nodes/${id}`)
export const listFlowLinks = () => request.get('/energy/flow-links')
export const createFlowLink = (data) => request.post('/energy/flow-links', data)
export const deleteFlowLink = (id) => request.delete(`/energy/flow-links/${id}`)
export const autoBuildFlow = (year) => request.post(`/energy/flow-auto-build${year ? `?year=${year}` : ''}`)

export const listEnergyBudgets = (params) => request.get('/energy/energy-budgets', { params })
export const createEnergyBudget = (data) => request.post('/energy/energy-budgets', data)
export const updateEnergyBudget = (id, data) => request.put(`/energy/energy-budgets/${id}`, data)
export const deleteEnergyBudget = (id) => request.delete(`/energy/energy-budgets/${id}`)

export const listCarbonBudgets = (params) => request.get('/energy/carbon-budgets', { params })
export const createCarbonBudget = (data) => request.post('/energy/carbon-budgets', data)
export const updateCarbonBudget = (id, data) => request.put(`/energy/carbon-budgets/${id}`, data)
export const deleteCarbonBudget = (id) => request.delete(`/energy/carbon-budgets/${id}`)
export const getEnergyBudgetActual = (params) => request.get('/energy/budgets/actual', { params })

export const getComprehensive = (params) => request.get('/energy/comprehensive', { params })
export const getUnitStat = (params) => request.get('/energy/unit-stat', { params })
export const getMeterQuery = (params) => request.get('/energy/meter-query', { params })
export const compareEnergy = (params) => request.get('/energy/compare', { params })
export const ratioEnergy = (params) => request.get('/energy/ratio', { params })

// ============ 碳排放 ============
export const listAccounting = (params) => request.get('/carbon/accounting', { params })
export const createAccounting = (data) => request.post('/carbon/accounting', data)
export const updateAccounting = (id, data) => request.put(`/carbon/accounting/${id}`, data)
export const deleteAccounting = (id) => request.delete(`/carbon/accounting/${id}`)

export const getCarbonStatistics = (params) => request.get('/carbon/statistics', { params })
export const listReports = () => request.get('/carbon/reports')
export const generateReport = (data) => request.post('/carbon/reports/generate', data)
export const updateReport = (id, data) => request.put(`/carbon/reports/${id}`, data)

export const listFootprints = (params) => request.get('/carbon/footprints', { params })
export const createFootprint = (data) => request.post('/carbon/footprints', data)
export const updateFootprint = (id, data) => request.put(`/carbon/footprints/${id}`, data)
export const deleteFootprint = (id) => request.delete(`/carbon/footprints/${id}`)
export const autoAllocateFootprint = (year) => request.post(`/carbon/footprints/auto-allocate${year ? `?year=${year}` : ''}`)

export const getSupplyChainSummary = (params) => request.get('/carbon/supply-chain/summary', { params })
export const getCarbonBudgetActual = (params) => request.get('/carbon/budgets/actual', { params })
export const getCarbonAssetBalance = (params) => request.get('/carbon/assets/balance', { params })

export const listSuppliers = (params) => request.get('/carbon/suppliers', { params })
export const createSupplier = (data) => request.post('/carbon/suppliers', data)
export const updateSupplier = (id, data) => request.put(`/carbon/suppliers/${id}`, data)
export const deleteSupplier = (id) => request.delete(`/carbon/suppliers/${id}`)

export const listSupplierCarbon = (params) => request.get('/carbon/supplier-carbon-data', { params })
export const createSupplierCarbon = (data) => request.post('/carbon/supplier-carbon-data', data)
export const deleteSupplierCarbon = (id) => request.delete(`/carbon/supplier-carbon-data/${id}`)

export const listVerifications = (params) => request.get('/carbon/verifications', { params })
export const createVerification = (data) => request.post('/carbon/verifications', data)
export const updateVerification = (id, data) => request.put(`/carbon/verifications/${id}`, data)
export const deleteVerification = (id) => request.delete(`/carbon/verifications/${id}`)

export const listAssets = (params) => request.get('/carbon/assets', { params })
export const createAsset = (data) => request.post('/carbon/assets', data)
export const updateAsset = (id, data) => request.put(`/carbon/assets/${id}`, data)
export const deleteAsset = (id) => request.delete(`/carbon/assets/${id}`)

export const listQuotaRecords = (params) => request.get('/carbon/quota-records', { params })
export const createQuotaRecord = (data) => request.post('/carbon/quota-records', data)
export const deleteQuotaRecord = (id) => request.delete(`/carbon/quota-records/${id}`)

export const listEvidences = (params) => request.get('/carbon/evidences', { params })
export const createEvidence = (data) => request.post('/carbon/evidences', data)
export const updateEvidence = (id, data) => request.put(`/carbon/evidences/${id}`, data)
export const deleteEvidence = (id) => request.delete(`/carbon/evidences/${id}`)

// ============ 看板 / 大屏 ============
export const getDashboardSummary = (params) => request.get('/dashboard/summary', { params })
export const getCarbonTrend = (params) => request.get('/dashboard/carbon-trend', { params })
export const getEnergyStructure = (params) => request.get('/dashboard/energy-structure', { params })
export const getUnitRanking = (params) => request.get('/dashboard/unit-ranking', { params })
export const getScopeBreakdown = (params) => request.get('/dashboard/scope-breakdown', { params })
export const getRecentEntries = (params) => request.get('/dashboard/recent', { params })
