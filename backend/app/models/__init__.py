"""27 张表的 SQLAlchemy 模型 —— 数字化能碳管理系统。

精度约定（见《开发决策记录.md》）：
- 金额类字段：Numeric(18, 2)
- 能耗/消耗量类字段：Numeric(18, 4)
- 碳排放类字段：Numeric(20, 6)
- 折标煤系数 / 碳排放因子：Numeric(18, 6)
时间字段统一 datetime，创建时间默认当前时间。
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from ..database import Base

# 精度别名
MONEY = Numeric(18, 2)
ENERGY = Numeric(18, 4)
CARBON = Numeric(20, 6)
COEF = Numeric(18, 6)


# ====================== 基础表（7 张） ======================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(64), nullable=False, default="管理员")
    role = Column(String(32), nullable=False, default="admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, default="示例企业")
    credit_code = Column(String(64), default="")
    industry = Column(String(64), default="")
    address = Column(String(255), default="")
    contact = Column(String(64), default="")
    phone = Column(String(32), default="")
    scale = Column(String(64), default="")
    established_date = Column(Date, nullable=True)

    def __repr__(self):
        return f"<Organization {self.name}>"


class EnergyType(Base):
    __tablename__ = "energy_types"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(64), nullable=False)
    unit = Column(String(16), default="kWh")
    # 折标煤系数：单位能源折算为标准煤（kgce / 单位），示例值来源 GB/T 2589-2020
    standard_coal_coefficient = Column(COEF, default=0)
    # 碳排放因子：单位能源碳排放（kgCO2e / 单位），来源 IPCC / 生态环境部
    carbon_factor = Column(COEF, default=0)
    # 默认单价（元 / 单位）
    default_price = Column(MONEY, default=0)
    # 是否外购电力（范围2 排放判定用）
    is_purchased_electricity = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def __repr__(self):
        return f"<EnergyType {self.name}>"


class EnergyUnit(Base):
    __tablename__ = "energy_units"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(64), nullable=False)
    parent_id = Column(Integer, ForeignKey("energy_units.id"), nullable=True)
    level = Column(Integer, default=1)
    area = Column(String(128), default="")
    responsible_person = Column(String(64), default="")
    phone = Column(String(32), default="")
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    parent = relationship("EnergyUnit", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<EnergyUnit {self.name}>"


class Meter(Base):
    __tablename__ = "meters"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(64), nullable=False)
    energy_type_id = Column(Integer, ForeignKey("energy_types.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("energy_units.id"), nullable=False)
    meter_type = Column(String(32), default="电能表")
    installation_location = Column(String(128), default="")
    rated_voltage = Column(String(32), default="")
    current_ratio = Column(String(32), default="")
    voltage_ratio = Column(String(32), default="")
    accuracy = Column(String(32), default="")
    install_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    remark = Column(String(255), default="")

    energy_type = relationship("EnergyType")
    unit = relationship("EnergyUnit")

    def __repr__(self):
        return f"<Meter {self.name}>"


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(64), nullable=False)
    unit = Column(String(16), default="件")
    output_unit = Column(String(16), default="吨")
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def __repr__(self):
        return f"<Product {self.name}>"


class SystemConfig(Base):
    __tablename__ = "system_configs"
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(64), unique=True, index=True, nullable=False)
    config_value = Column(String(255), default="")
    config_group = Column(String(64), default="")
    description = Column(String(255), default="")

    def __repr__(self):
        return f"<SystemConfig {self.config_key}>"


# ====================== 能源业务表（9 张） ======================

class MeterReading(Base):
    __tablename__ = "meter_readings"
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=False)
    reading_time = Column(DateTime, nullable=False)
    last_reading = Column(ENERGY, default=0)
    current_reading = Column(ENERGY, default=0)
    consumption = Column(ENERGY, default=0)
    unit_price = Column(MONEY, default=0)
    cost = Column(MONEY, default=0)
    standard_coal = Column(ENERGY, default=0)
    carbon_emission = Column(CARBON, default=0)
    recorder = Column(String(64), default="")
    remark = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    meter = relationship("Meter")

    def __repr__(self):
        return f"<MeterReading meter={self.meter_id} {self.reading_time}>"


class ManualEntry(Base):
    __tablename__ = "manual_entries"
    id = Column(Integer, primary_key=True, index=True)
    energy_type_id = Column(Integer, ForeignKey("energy_types.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("energy_units.id"), nullable=False)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=True)
    entry_date = Column(DateTime, nullable=False)
    consumption = Column(ENERGY, default=0)
    unit_price = Column(MONEY, default=0)
    cost = Column(MONEY, default=0)
    standard_coal = Column(ENERGY, default=0)
    carbon_emission = Column(CARBON, default=0)
    data_source = Column(String(64), default="手工录入")
    recorder = Column(String(64), default="")
    remark = Column(String(255), default="")

    energy_type = relationship("EnergyType")
    unit = relationship("EnergyUnit")
    meter = relationship("Meter")

    def __repr__(self):
        return f"<ManualEntry {self.entry_date}>"


class ProductionData(Base):
    __tablename__ = "production_data"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("energy_units.id"), nullable=True)
    stat_date = Column(DateTime, nullable=False)
    output = Column(ENERGY, default=0)
    output_unit = Column(String(16), default="吨")
    output_value = Column(MONEY, default=0)
    period = Column(String(16), default="月")  # 日/月/年
    remark = Column(String(255), default="")

    product = relationship("Product")
    unit = relationship("EnergyUnit")

    def __repr__(self):
        return f"<ProductionData {self.stat_date}>"


class EfficiencyIndicator(Base):
    __tablename__ = "efficiency_indicators"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    energy_type_id = Column(Integer, ForeignKey("energy_types.id"), nullable=True)
    benchmark_value = Column(ENERGY, default=0)
    target_value = Column(ENERGY, default=0)
    unit = Column(String(32), default="")
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    energy_type = relationship("EnergyType")

    def __repr__(self):
        return f"<EfficiencyIndicator {self.name}>"


class EfficiencyAssessment(Base):
    __tablename__ = "efficiency_assessments"
    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("efficiency_indicators.id"), nullable=False)
    stat_date = Column(DateTime, nullable=False)
    energy_consumption = Column(ENERGY, default=0)
    output = Column(ENERGY, default=0)
    actual_value = Column(ENERGY, default=0)
    benchmark_value = Column(ENERGY, default=0)
    deviation = Column(Numeric(10, 2), default=0)  # 偏差率 %
    level = Column(String(16), default="合格")  # 领先/先进/合格/落后
    remark = Column(String(255), default="")

    indicator = relationship("EfficiencyIndicator")

    def __repr__(self):
        return f"<EfficiencyAssessment {self.stat_date}>"


class EnergyFlowNode(Base):
    __tablename__ = "energy_flow_nodes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    # 节点类型：输入/转换/分配/利用/损失
    node_type = Column(String(16), default="输入")
    sort_order = Column(Integer, default=0)
    remark = Column(String(255), default="")

    def __repr__(self):
        return f"<EnergyFlowNode {self.name}>"


class EnergyFlowLink(Base):
    __tablename__ = "energy_flow_links"
    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("energy_flow_nodes.id"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("energy_flow_nodes.id"), nullable=False)
    flow_value = Column(ENERGY, default=0)
    unit = Column(String(16), default="kWh")
    loss_rate = Column(Numeric(10, 2), default=0)
    remark = Column(String(255), default="")

    source_node = relationship("EnergyFlowNode", foreign_keys=[source_node_id])
    target_node = relationship("EnergyFlowNode", foreign_keys=[target_node_id])

    def __repr__(self):
        return f"<EnergyFlowLink {self.source_node_id}->{self.target_node_id}>"


class EnergyBudget(Base):
    __tablename__ = "energy_budgets"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=True)  # 不填=年度
    energy_type_id = Column(Integer, ForeignKey("energy_types.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("energy_units.id"), nullable=True)
    budget_value = Column(ENERGY, default=0)
    actual_value = Column(ENERGY, default=0)
    unit_consumption = Column(ENERGY, default=0)  # 产品单耗
    planned_output = Column(ENERGY, default=0)  # 计划产量
    source_type = Column(String(32), default="手工填写")  # 能效指标/能效测评/手工填写
    remark = Column(String(255), default="")

    energy_type = relationship("EnergyType")
    unit = relationship("EnergyUnit")

    def __repr__(self):
        return f"<EnergyBudget {self.year}>"


class CarbonBudget(Base):
    __tablename__ = "carbon_budgets"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=True)
    unit_id = Column(Integer, ForeignKey("energy_units.id"), nullable=True)
    budget_carbon = Column(CARBON, default=0)
    actual_carbon = Column(CARBON, default=0)
    carbon_intensity = Column(CARBON, default=0)  # 碳排放强度
    intensity_type = Column(String(32), default="产值强度")  # 产值强度/产品强度
    planned_output = Column(ENERGY, default=0)  # 计划产量或产值
    remark = Column(String(255), default="")

    unit = relationship("EnergyUnit")

    def __repr__(self):
        return f"<CarbonBudget {self.year}>"


# ====================== 碳业务表（10 张） ======================

class CarbonFactor(Base):
    __tablename__ = "carbon_factors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    factor_value = Column(COEF, default=0)
    unit = Column(String(32), default="kgCO2e/单位")
    source = Column(String(128), default="")  # 来源标准
    effective_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def __repr__(self):
        return f"<CarbonFactor {self.name}>"


class EmissionSource(Base):
    __tablename__ = "emission_sources"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(64), nullable=False)
    # scope: 范围1/范围2/范围3
    scope = Column(String(16), default="范围1")
    category = Column(String(64), default="")
    carbon_factor_id = Column(Integer, ForeignKey("carbon_factors.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    remark = Column(String(255), default="")

    carbon_factor = relationship("CarbonFactor")

    def __repr__(self):
        return f"<EmissionSource {self.name}>"


class CarbonAccounting(Base):
    __tablename__ = "carbon_accounting"
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("emission_sources.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    activity_data = Column(ENERGY, default=0)
    unit = Column(String(16), default="")
    emission_factor = Column(COEF, default=0)
    emission = Column(CARBON, default=0)
    data_source = Column(String(64), default="")
    # 存证状态：未存证/已存证（避免对同一条核算重复存证）
    evidence_status = Column(String(16), default="未存证")
    remark = Column(String(255), default="")

    source = relationship("EmissionSource")

    def __repr__(self):
        return f"<CarbonAccounting {self.year}-{self.month}>"


class CarbonReport(Base):
    __tablename__ = "carbon_reports"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, unique=True)
    total_emission = Column(CARBON, default=0)
    scope1 = Column(CARBON, default=0)
    scope2 = Column(CARBON, default=0)
    scope3 = Column(CARBON, default=0)
    intensity_value = Column(CARBON, default=0)  # 产值强度
    product_intensity = Column(CARBON, default=0)  # 产品强度
    per_capita = Column(CARBON, default=0)  # 人均
    measures = Column(Text, default="")
    next_plan = Column(Text, default="")
    report_date = Column(Date, nullable=True)
    status = Column(String(16), default="草稿")

    def __repr__(self):
        return f"<CarbonReport {self.year}>"


class ProductFootprint(Base):
    __tablename__ = "product_footprints"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    functional_unit = Column(String(64), default="")
    # 系统边界：从摇篮到大门/从摇篮到坟墓
    boundary = Column(String(32), default="从摇篮到大门")
    raw_material = Column(CARBON, default=0)
    production = Column(CARBON, default=0)
    transport = Column(CARBON, default=0)
    use_phase = Column(CARBON, default=0)
    disposal = Column(CARBON, default=0)
    total = Column(CARBON, default=0)
    assessment_date = Column(Date, nullable=True)
    data_source = Column(String(255), default="")

    product = relationship("Product")

    def __repr__(self):
        return f"<ProductFootprint {self.product_id}>"


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    credit_code = Column(String(64), default="")
    contact_person = Column(String(64), default="")
    phone = Column(String(32), default="")
    category = Column(String(32), default="原材料")  # 原材料/零部件/服务/物流/其他
    risk_level = Column(String(16), default="中")  # 高/中/低
    address = Column(String(255), default="")
    total_emission = Column(CARBON, default=0)

    def __repr__(self):
        return f"<Supplier {self.name}>"


class SupplierCarbonData(Base):
    __tablename__ = "supplier_carbon_data"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    year = Column(Integer, nullable=False)
    material_name = Column(String(128), default="")
    quantity = Column(ENERGY, default=0)
    unit = Column(String(16), default="")
    emission_factor = Column(COEF, default=0)
    emission = Column(CARBON, default=0)
    data_source = Column(String(32), default="供应商申报")  # 供应商申报/实测/默认因子

    supplier = relationship("Supplier")

    def __repr__(self):
        return f"<SupplierCarbonData {self.supplier_id}>"


class CarbonVerification(Base):
    __tablename__ = "carbon_verifications"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    verification_agency = Column(String(128), default="")
    verifier = Column(String(64), default="")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    reported_emission = Column(CARBON, default=0)
    verified_emission = Column(CARBON, default=0)
    # 状态：待核查/核查中/已完成/有异议
    status = Column(String(16), default="待核查")
    conclusion = Column(Text, default="")
    evidence_hash = Column(String(255), default="")

    def __repr__(self):
        return f"<CarbonVerification {self.year}>"


class CarbonEvidence(Base):
    __tablename__ = "carbon_evidences"
    id = Column(Integer, primary_key=True, index=True)
    accounting_id = Column(Integer, ForeignKey("carbon_accounting.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    scope = Column(String(16), default="")  # 范围1/2/3
    source_name = Column(String(64), default="")  # 排放源名称（冗余，便于检索）
    emission = Column(CARBON, default=0)  # 该核算记录排放量（冗余）
    evidence_no = Column(String(64), unique=True, index=True, nullable=False)  # 存证编号
    evidence_hash = Column(String(255), default="")  # 链上存证哈希
    chain_platform = Column(String(128), default="")  # 存证链/平台名称
    tx_time = Column(DateTime, nullable=True)  # 上链时间
    # 状态：待上链/已上链/校验通过/校验失败
    status = Column(String(16), default="已上链")
    operator = Column(String(64), default="")  # 存证人
    remark = Column(String(255), default="")

    accounting = relationship("CarbonAccounting")

    def __repr__(self):
        return f"<CarbonEvidence {self.evidence_no}>"


class CarbonAsset(Base):
    __tablename__ = "carbon_assets"
    id = Column(Integer, primary_key=True, index=True)
    asset_type = Column(String(32), default="配额")  # 配额/CCER
    year = Column(Integer, nullable=False)
    project_name = Column(String(128), default="")
    quantity = Column(CARBON, default=0)
    used_quantity = Column(CARBON, default=0)
    acquisition_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    status = Column(String(16), default="有效")  # 有效/已用完/已过期

    def __repr__(self):
        return f"<CarbonAsset {self.project_name}>"


class QuotaRecord(Base):
    __tablename__ = "quota_records"
    id = Column(Integer, primary_key=True, index=True)
    trade_date = Column(Date, nullable=True)
    trade_type = Column(String(16), default="买入")  # 买入/卖出
    quantity = Column(CARBON, default=0)
    price = Column(MONEY, default=0)
    total_amount = Column(MONEY, default=0)
    market = Column(String(32), default="全国碳市场")
    remark = Column(String(255), default="")

    def __repr__(self):
        return f"<QuotaRecord {self.trade_type}>"


# ====================== 日志表（1 张） ======================

class OperationLog(Base):
    __tablename__ = "operation_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(64), default="")
    module = Column(String(64), default="")
    action = Column(String(64), default="")
    ip = Column(String(64), default="")
    user_agent = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<OperationLog {self.module}.{self.action}>"
