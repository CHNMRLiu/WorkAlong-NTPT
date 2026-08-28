"""Pydantic Schema（数据校验 / 接口出入参）。

每个业务表提供：Create（新增入参）、Update（修改入参，全部可选）、Response（出参，from_attributes）。
数值字段统一用 float 在 JSON 层传输，数据库层用 Decimal 精确存储。
"""
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# ====================== 基础表 ======================

class UserCreate(BaseModel):
    username: str
    password: str
    name: Optional[str] = "管理员"
    role: Optional[str] = "admin"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    credit_code: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    scale: Optional[str] = None
    established_date: Optional[date] = None

class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    credit_code: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    scale: Optional[str] = None
    established_date: Optional[date] = None


class EnergyTypeCreate(BaseModel):
    code: str
    name: str
    unit: Optional[str] = "kWh"
    standard_coal_coefficient: Optional[float] = 0
    carbon_factor: Optional[float] = 0
    default_price: Optional[float] = 0
    is_purchased_electricity: Optional[bool] = False
    is_active: Optional[bool] = True
    sort_order: Optional[int] = 0

class EnergyTypeUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    standard_coal_coefficient: Optional[float] = None
    carbon_factor: Optional[float] = None
    default_price: Optional[float] = None
    is_purchased_electricity: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class EnergyTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    unit: Optional[str] = None
    standard_coal_coefficient: float = 0
    carbon_factor: float = 0
    default_price: float = 0
    is_purchased_electricity: bool = False
    is_active: bool = True
    sort_order: int = 0


class EnergyUnitCreate(BaseModel):
    code: str
    name: str
    parent_id: Optional[int] = None
    level: Optional[int] = 1
    area: Optional[str] = None
    responsible_person: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = True
    sort_order: Optional[int] = 0

class EnergyUnitUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    area: Optional[str] = None
    responsible_person: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class EnergyUnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    parent_id: Optional[int] = None
    level: int = 1
    area: Optional[str] = None
    responsible_person: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class MeterCreate(BaseModel):
    code: str
    name: str
    energy_type_id: int
    unit_id: int
    meter_type: Optional[str] = "电能表"
    installation_location: Optional[str] = None
    rated_voltage: Optional[str] = None
    current_ratio: Optional[str] = None
    voltage_ratio: Optional[str] = None
    accuracy: Optional[str] = None
    install_date: Optional[date] = None
    is_active: Optional[bool] = True
    remark: Optional[str] = None

class MeterUpdate(BaseModel):
    name: Optional[str] = None
    energy_type_id: Optional[int] = None
    unit_id: Optional[int] = None
    meter_type: Optional[str] = None
    installation_location: Optional[str] = None
    rated_voltage: Optional[str] = None
    current_ratio: Optional[str] = None
    voltage_ratio: Optional[str] = None
    accuracy: Optional[str] = None
    install_date: Optional[date] = None
    is_active: Optional[bool] = None
    remark: Optional[str] = None

class MeterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    energy_type_id: int
    unit_id: int
    meter_type: Optional[str] = None
    installation_location: Optional[str] = None
    rated_voltage: Optional[str] = None
    current_ratio: Optional[str] = None
    voltage_ratio: Optional[str] = None
    accuracy: Optional[str] = None
    install_date: Optional[date] = None
    is_active: bool = True
    remark: Optional[str] = None


class ProductCreate(BaseModel):
    code: str
    name: str
    unit: Optional[str] = "件"
    output_unit: Optional[str] = "吨"
    is_active: Optional[bool] = True
    sort_order: Optional[int] = 0

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    output_unit: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    unit: Optional[str] = None
    output_unit: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class SystemConfigCreate(BaseModel):
    config_key: str
    config_value: Optional[str] = ""
    config_group: Optional[str] = ""
    description: Optional[str] = ""

class SystemConfigUpdate(BaseModel):
    config_value: Optional[str] = None
    config_group: Optional[str] = None
    description: Optional[str] = None

class SystemConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    config_key: str
    config_value: Optional[str] = None
    config_group: Optional[str] = None
    description: Optional[str] = None


# ====================== 能源业务表 ======================

class MeterReadingCreate(BaseModel):
    meter_id: int
    reading_time: datetime
    last_reading: Optional[float] = 0
    current_reading: float
    unit_price: Optional[float] = 0
    recorder: Optional[str] = ""
    remark: Optional[str] = ""

class MeterReadingUpdate(BaseModel):
    reading_time: Optional[datetime] = None
    last_reading: Optional[float] = None
    current_reading: Optional[float] = None
    unit_price: Optional[float] = None
    recorder: Optional[str] = None
    remark: Optional[str] = None

class MeterReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    meter_id: int
    reading_time: datetime
    last_reading: float = 0
    current_reading: float = 0
    consumption: float = 0
    unit_price: float = 0
    cost: float = 0
    standard_coal: float = 0
    carbon_emission: float = 0
    recorder: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None


class ManualEntryCreate(BaseModel):
    energy_type_id: int
    unit_id: int
    meter_id: Optional[int] = None
    entry_date: datetime
    consumption: float
    unit_price: Optional[float] = 0
    data_source: Optional[str] = "手工录入"
    recorder: Optional[str] = ""
    remark: Optional[str] = ""

class ManualEntryUpdate(BaseModel):
    entry_date: Optional[datetime] = None
    consumption: Optional[float] = None
    unit_price: Optional[float] = None
    data_source: Optional[str] = None
    recorder: Optional[str] = None
    remark: Optional[str] = None

class ManualEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    energy_type_id: int
    unit_id: int
    meter_id: Optional[int] = None
    entry_date: datetime
    consumption: float = 0
    unit_price: float = 0
    cost: float = 0
    standard_coal: float = 0
    carbon_emission: float = 0
    data_source: Optional[str] = None
    recorder: Optional[str] = None
    remark: Optional[str] = None


class ProductionDataCreate(BaseModel):
    product_id: int
    unit_id: Optional[int] = None
    stat_date: datetime
    output: float
    output_unit: Optional[str] = "吨"
    output_value: Optional[float] = 0
    period: Optional[str] = "月"
    remark: Optional[str] = ""

class ProductionDataUpdate(BaseModel):
    product_id: Optional[int] = None
    unit_id: Optional[int] = None
    stat_date: Optional[datetime] = None
    output: Optional[float] = None
    output_unit: Optional[str] = None
    output_value: Optional[float] = None
    period: Optional[str] = None
    remark: Optional[str] = None

class ProductionDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    unit_id: Optional[int] = None
    stat_date: datetime
    output: float = 0
    output_unit: Optional[str] = None
    output_value: float = 0
    period: Optional[str] = None
    remark: Optional[str] = None


class EfficiencyIndicatorCreate(BaseModel):
    name: str
    energy_type_id: Optional[int] = None
    benchmark_value: Optional[float] = 0
    target_value: Optional[float] = 0
    unit: Optional[str] = ""
    is_active: Optional[bool] = True
    sort_order: Optional[int] = 0

class EfficiencyIndicatorUpdate(BaseModel):
    name: Optional[str] = None
    energy_type_id: Optional[int] = None
    benchmark_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class EfficiencyIndicatorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    energy_type_id: Optional[int] = None
    benchmark_value: float = 0
    target_value: float = 0
    unit: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class EfficiencyAssessmentCreate(BaseModel):
    indicator_id: int
    stat_date: datetime
    energy_consumption: float
    output: float
    benchmark_value: Optional[float] = 0
    remark: Optional[str] = ""

class EfficiencyAssessmentUpdate(BaseModel):
    stat_date: Optional[datetime] = None
    energy_consumption: Optional[float] = None
    output: Optional[float] = None
    benchmark_value: Optional[float] = None
    remark: Optional[str] = None

class EfficiencyAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    indicator_id: int
    stat_date: datetime
    energy_consumption: float = 0
    output: float = 0
    actual_value: float = 0
    benchmark_value: float = 0
    deviation: float = 0
    level: Optional[str] = None
    remark: Optional[str] = None


class EnergyFlowNodeCreate(BaseModel):
    name: str
    node_type: Optional[str] = "输入"
    sort_order: Optional[int] = 0
    remark: Optional[str] = ""

class EnergyFlowNodeUpdate(BaseModel):
    name: Optional[str] = None
    node_type: Optional[str] = None
    sort_order: Optional[int] = None
    remark: Optional[str] = None

class EnergyFlowNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    node_type: Optional[str] = None
    sort_order: int = 0
    remark: Optional[str] = None


class EnergyFlowLinkCreate(BaseModel):
    source_node_id: int
    target_node_id: int
    flow_value: float
    unit: Optional[str] = "kWh"
    loss_rate: Optional[float] = 0
    remark: Optional[str] = ""

class EnergyFlowLinkUpdate(BaseModel):
    source_node_id: Optional[int] = None
    target_node_id: Optional[int] = None
    flow_value: Optional[float] = None
    unit: Optional[str] = None
    loss_rate: Optional[float] = None
    remark: Optional[str] = None

class EnergyFlowLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_node_id: int
    target_node_id: int
    flow_value: float = 0
    unit: Optional[str] = None
    loss_rate: float = 0
    remark: Optional[str] = None


class EnergyBudgetCreate(BaseModel):
    year: int
    month: Optional[int] = None
    energy_type_id: int
    unit_id: Optional[int] = None
    budget_value: Optional[float] = 0
    actual_value: Optional[float] = 0
    unit_consumption: Optional[float] = 0
    planned_output: Optional[float] = 0
    source_type: Optional[str] = "手工填写"
    remark: Optional[str] = ""

class EnergyBudgetUpdate(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    energy_type_id: Optional[int] = None
    unit_id: Optional[int] = None
    budget_value: Optional[float] = None
    actual_value: Optional[float] = None
    unit_consumption: Optional[float] = None
    planned_output: Optional[float] = None
    source_type: Optional[str] = None
    remark: Optional[str] = None

class EnergyBudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    year: int
    month: Optional[int] = None
    energy_type_id: int
    unit_id: Optional[int] = None
    budget_value: float = 0
    actual_value: float = 0
    unit_consumption: float = 0
    planned_output: float = 0
    source_type: Optional[str] = None
    remark: Optional[str] = None


class CarbonBudgetCreate(BaseModel):
    year: int
    month: Optional[int] = None
    unit_id: Optional[int] = None
    budget_carbon: Optional[float] = 0
    actual_carbon: Optional[float] = 0
    carbon_intensity: Optional[float] = 0
    intensity_type: Optional[str] = "产值强度"
    planned_output: Optional[float] = 0
    remark: Optional[str] = ""

class CarbonBudgetUpdate(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    unit_id: Optional[int] = None
    budget_carbon: Optional[float] = None
    actual_carbon: Optional[float] = None
    carbon_intensity: Optional[float] = None
    intensity_type: Optional[str] = None
    planned_output: Optional[float] = None
    remark: Optional[str] = None

class CarbonBudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    year: int
    month: Optional[int] = None
    unit_id: Optional[int] = None
    budget_carbon: float = 0
    actual_carbon: float = 0
    carbon_intensity: float = 0
    intensity_type: Optional[str] = None
    planned_output: float = 0
    remark: Optional[str] = None


# ====================== 碳业务表 ======================

class CarbonFactorCreate(BaseModel):
    name: str
    factor_value: Optional[float] = 0
    unit: Optional[str] = "kgCO2e/单位"
    source: Optional[str] = ""
    effective_date: Optional[date] = None
    is_active: Optional[bool] = True
    sort_order: Optional[int] = 0

class CarbonFactorUpdate(BaseModel):
    name: Optional[str] = None
    factor_value: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    effective_date: Optional[date] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class CarbonFactorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    factor_value: float = 0
    unit: Optional[str] = None
    source: Optional[str] = None
    effective_date: Optional[date] = None
    is_active: bool = True
    sort_order: int = 0


class EmissionSourceCreate(BaseModel):
    code: str
    name: str
    scope: Optional[str] = "范围1"
    category: Optional[str] = ""
    carbon_factor_id: Optional[int] = None
    is_active: Optional[bool] = True
    sort_order: Optional[int] = 0
    remark: Optional[str] = ""

class EmissionSourceUpdate(BaseModel):
    name: Optional[str] = None
    scope: Optional[str] = None
    category: Optional[str] = None
    carbon_factor_id: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    remark: Optional[str] = None

class EmissionSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    scope: Optional[str] = None
    category: Optional[str] = None
    carbon_factor_id: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0
    remark: Optional[str] = None


class CarbonAccountingCreate(BaseModel):
    source_id: int
    year: int
    month: int
    activity_data: float
    unit: Optional[str] = ""
    emission_factor: Optional[float] = 0
    data_source: Optional[str] = ""
    remark: Optional[str] = ""

class CarbonAccountingUpdate(BaseModel):
    source_id: Optional[int] = None
    year: Optional[int] = None
    month: Optional[int] = None
    activity_data: Optional[float] = None
    unit: Optional[str] = None
    emission_factor: Optional[float] = None
    data_source: Optional[str] = None
    remark: Optional[str] = None

class CarbonAccountingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_id: int
    year: int
    month: int
    activity_data: float = 0
    unit: Optional[str] = None
    emission_factor: float = 0
    emission: float = 0
    data_source: Optional[str] = None
    evidence_status: Optional[str] = None
    remark: Optional[str] = None


class CarbonReportCreate(BaseModel):
    year: int
    measures: Optional[str] = ""
    next_plan: Optional[str] = ""
    report_date: Optional[date] = None
    status: Optional[str] = "草稿"

class CarbonReportUpdate(BaseModel):
    measures: Optional[str] = None
    next_plan: Optional[str] = None
    report_date: Optional[date] = None
    status: Optional[str] = None

class CarbonReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    year: int
    total_emission: float = 0
    scope1: float = 0
    scope2: float = 0
    scope3: float = 0
    intensity_value: float = 0
    product_intensity: float = 0
    per_capita: float = 0
    measures: Optional[str] = None
    next_plan: Optional[str] = None
    report_date: Optional[date] = None
    status: Optional[str] = None


class ProductFootprintCreate(BaseModel):
    product_id: int
    functional_unit: Optional[str] = ""
    boundary: Optional[str] = "从摇篮到大门"
    raw_material: Optional[float] = 0
    production: Optional[float] = 0
    transport: Optional[float] = 0
    use_phase: Optional[float] = 0
    disposal: Optional[float] = 0
    assessment_date: Optional[date] = None
    data_source: Optional[str] = ""

class ProductFootprintUpdate(BaseModel):
    functional_unit: Optional[str] = None
    boundary: Optional[str] = None
    raw_material: Optional[float] = None
    production: Optional[float] = None
    transport: Optional[float] = None
    use_phase: Optional[float] = None
    disposal: Optional[float] = None
    assessment_date: Optional[date] = None
    data_source: Optional[str] = None

class ProductFootprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    functional_unit: Optional[str] = None
    boundary: Optional[str] = None
    raw_material: float = 0
    production: float = 0
    transport: float = 0
    use_phase: float = 0
    disposal: float = 0
    total: float = 0
    assessment_date: Optional[date] = None
    data_source: Optional[str] = None


class SupplierCreate(BaseModel):
    name: str
    credit_code: Optional[str] = ""
    contact_person: Optional[str] = ""
    phone: Optional[str] = ""
    category: Optional[str] = "原材料"
    risk_level: Optional[str] = "中"
    address: Optional[str] = ""

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    credit_code: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    category: Optional[str] = None
    risk_level: Optional[str] = None
    address: Optional[str] = None

class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    credit_code: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    category: Optional[str] = None
    risk_level: Optional[str] = None
    address: Optional[str] = None
    total_emission: float = 0


class SupplierCarbonDataCreate(BaseModel):
    supplier_id: int
    year: int
    material_name: Optional[str] = ""
    quantity: float
    unit: Optional[str] = ""
    emission_factor: Optional[float] = 0
    data_source: Optional[str] = "供应商申报"

class SupplierCarbonDataUpdate(BaseModel):
    year: Optional[int] = None
    material_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    emission_factor: Optional[float] = None
    data_source: Optional[str] = None

class SupplierCarbonDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_id: int
    year: int
    material_name: Optional[str] = None
    quantity: float = 0
    unit: Optional[str] = None
    emission_factor: float = 0
    emission: float = 0
    data_source: Optional[str] = None


class CarbonVerificationCreate(BaseModel):
    year: int
    verification_agency: Optional[str] = ""
    verifier: Optional[str] = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reported_emission: Optional[float] = 0
    verified_emission: Optional[float] = 0
    status: Optional[str] = "待核查"
    conclusion: Optional[str] = ""
    evidence_hash: Optional[str] = ""

class CarbonVerificationUpdate(BaseModel):
    verification_agency: Optional[str] = None
    verifier: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reported_emission: Optional[float] = None
    verified_emission: Optional[float] = None
    status: Optional[str] = None
    conclusion: Optional[str] = None
    evidence_hash: Optional[str] = None

class CarbonVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    year: int
    verification_agency: Optional[str] = None
    verifier: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reported_emission: float = 0
    verified_emission: float = 0
    status: Optional[str] = None
    conclusion: Optional[str] = None
    evidence_hash: Optional[str] = None


class CarbonEvidenceCreate(BaseModel):
    accounting_id: int
    evidence_hash: Optional[str] = ""
    chain_platform: Optional[str] = ""
    tx_time: Optional[datetime] = None
    status: Optional[str] = "已上链"
    operator: Optional[str] = ""
    remark: Optional[str] = ""

class CarbonEvidenceUpdate(BaseModel):
    evidence_hash: Optional[str] = None
    chain_platform: Optional[str] = None
    tx_time: Optional[datetime] = None
    status: Optional[str] = None
    operator: Optional[str] = None
    remark: Optional[str] = None

class CarbonEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    accounting_id: int
    year: int
    month: int
    scope: Optional[str] = None
    source_name: Optional[str] = None
    emission: float = 0
    evidence_no: str
    evidence_hash: Optional[str] = None
    chain_platform: Optional[str] = None
    tx_time: Optional[datetime] = None
    status: Optional[str] = None
    operator: Optional[str] = None
    remark: Optional[str] = None


class CarbonAssetCreate(BaseModel):
    asset_type: Optional[str] = "配额"
    year: int
    project_name: Optional[str] = ""
    quantity: float
    used_quantity: Optional[float] = 0
    acquisition_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = "有效"

class CarbonAssetUpdate(BaseModel):
    asset_type: Optional[str] = None
    year: Optional[int] = None
    project_name: Optional[str] = None
    quantity: Optional[float] = None
    used_quantity: Optional[float] = None
    acquisition_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = None

class CarbonAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_type: Optional[str] = None
    year: int
    project_name: Optional[str] = None
    quantity: float = 0
    used_quantity: float = 0
    acquisition_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = None


class QuotaRecordCreate(BaseModel):
    trade_date: Optional[date] = None
    trade_type: Optional[str] = "买入"
    quantity: float
    price: Optional[float] = 0
    market: Optional[str] = "全国碳市场"
    remark: Optional[str] = ""

class QuotaRecordUpdate(BaseModel):
    trade_date: Optional[date] = None
    trade_type: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    market: Optional[str] = None
    remark: Optional[str] = None

class QuotaRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trade_date: Optional[date] = None
    trade_type: Optional[str] = None
    quantity: float = 0
    price: float = 0
    total_amount: float = 0
    market: Optional[str] = None
    remark: Optional[str] = None


# ====================== 日志表 ======================

class OperationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    module: Optional[str] = None
    action: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None


# ====================== 复合/聚合响应（用于统计接口） ======================

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
