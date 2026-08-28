"""能源核心接口：表计读数、手工录入、生产数据、能效指标/测评、能流、预算，及统计接口。"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    CarbonBudget,
    EfficiencyAssessment,
    EfficiencyIndicator,
    EnergyBudget,
    EnergyFlowLink,
    EnergyFlowNode,
    EnergyType,
    EnergyUnit,
    ManualEntry,
    Meter,
    MeterReading,
    Product,
    ProductionData,
)
from ..schemas import (
    CarbonBudgetCreate, CarbonBudgetResponse, CarbonBudgetUpdate,
    EfficiencyAssessmentCreate, EfficiencyAssessmentResponse, EfficiencyAssessmentUpdate,
    EfficiencyIndicatorCreate, EfficiencyIndicatorResponse, EfficiencyIndicatorUpdate,
    EnergyBudgetCreate, EnergyBudgetResponse, EnergyBudgetUpdate,
    EnergyFlowLinkCreate, EnergyFlowLinkResponse, EnergyFlowLinkUpdate,
    EnergyFlowNodeCreate, EnergyFlowNodeResponse, EnergyFlowNodeUpdate,
    ManualEntryCreate, ManualEntryResponse, ManualEntryUpdate,
    MeterReadingCreate, MeterReadingResponse, MeterReadingUpdate,
    ProductionDataCreate, ProductionDataResponse, ProductionDataUpdate,
)
from ..utils import calculator as calc
from ..utils.response import fail, ok, page as page_resp
from .deps import get_current_user

router = APIRouter(prefix="/api/energy", tags=["能源消费"])


def _parse_dt(value: str, end: bool = False) -> datetime:
    if not value:
        return None
    if len(value) <= 10:
        return datetime.fromisoformat(value + ("T23:59:59" if end else "T00:00:00"))
    return datetime.fromisoformat(value)


# ---------------- 表计读数 ----------------
@router.get("/meter-readings", summary="表计读数列表")
def list_readings(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    meter_id: int = Query(None), start: str = Query(""), end: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(MeterReading)
    if meter_id:
        q = q.filter(MeterReading.meter_id == meter_id)
    if start:
        q = q.filter(MeterReading.reading_time >= _parse_dt(start))
    if end:
        q = q.filter(MeterReading.reading_time <= _parse_dt(end, True))
    total = q.count()
    items = q.order_by(MeterReading.reading_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([MeterReadingResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/meter-readings", summary="新增表计读数（自动折算费用/标煤/碳排）")
def create_reading(req: MeterReadingCreate, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    meter = db.query(Meter).filter(Meter.id == req.meter_id).first()
    if not meter:
        return fail("表计不存在")
    et = db.query(EnergyType).filter(EnergyType.id == meter.energy_type_id).first()
    consumption = calc.calc_consumption(req.last_reading, req.current_reading)
    unit_price = req.unit_price if req.unit_price else (et.default_price if et else 0)
    obj = MeterReading(
        meter_id=req.meter_id,
        reading_time=req.reading_time,
        last_reading=req.last_reading,
        current_reading=req.current_reading,
        consumption=float(consumption),
        unit_price=unit_price,
        cost=float(calc.calc_cost(consumption, unit_price)),
        standard_coal=float(calc.calc_standard_coal(consumption, et.standard_coal_coefficient if et else 0)),
        carbon_emission=float(calc.calc_carbon(consumption, et.carbon_factor if et else 0)),
        recorder=req.recorder,
        remark=req.remark,
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(MeterReadingResponse.model_validate(obj).model_dump())


@router.put("/meter-readings/{oid}", summary="修改表计读数")
def update_reading(oid: int, req: MeterReadingUpdate, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    obj = db.query(MeterReading).filter(MeterReading.id == oid).first()
    if not obj:
        return fail("记录不存在")
    data = req.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    # 重新计算派生值
    meter = db.query(Meter).filter(Meter.id == obj.meter_id).first()
    et = db.query(EnergyType).filter(EnergyType.id == meter.energy_type_id).first() if meter else None
    consumption = calc.calc_consumption(obj.last_reading, obj.current_reading)
    obj.consumption = float(consumption)
    obj.cost = float(calc.calc_cost(consumption, obj.unit_price))
    obj.standard_coal = float(calc.calc_standard_coal(consumption, et.standard_coal_coefficient if et else 0))
    obj.carbon_emission = float(calc.calc_carbon(consumption, et.carbon_factor if et else 0))
    db.commit(); db.refresh(obj)
    return ok(MeterReadingResponse.model_validate(obj).model_dump())


@router.delete("/meter-readings/{oid}", summary="删除表计读数")
def delete_reading(oid: int, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    obj = db.query(MeterReading).filter(MeterReading.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 手工录入 ----------------
@router.get("/manual-entries", summary="手工录入列表")
def list_manual(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    unit_id: int = Query(None), start: str = Query(""), end: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(ManualEntry)
    if unit_id:
        q = q.filter(ManualEntry.unit_id == unit_id)
    if start:
        q = q.filter(ManualEntry.entry_date >= _parse_dt(start))
    if end:
        q = q.filter(ManualEntry.entry_date <= _parse_dt(end, True))
    total = q.count()
    items = q.order_by(ManualEntry.entry_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([ManualEntryResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/manual-entries", summary="新增手工录入（自动折算）")
def create_manual(req: ManualEntryCreate, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    et = db.query(EnergyType).filter(EnergyType.id == req.energy_type_id).first()
    if not et:
        return fail("能源类型不存在")
    unit_price = req.unit_price if req.unit_price else et.default_price
    consumption = req.consumption
    obj = ManualEntry(
        energy_type_id=req.energy_type_id, unit_id=req.unit_id, meter_id=req.meter_id,
        entry_date=req.entry_date, consumption=consumption, unit_price=unit_price,
        cost=float(calc.calc_cost(consumption, unit_price)),
        standard_coal=float(calc.calc_standard_coal(consumption, et.standard_coal_coefficient)),
        carbon_emission=float(calc.calc_carbon(consumption, et.carbon_factor)),
        data_source=req.data_source, recorder=req.recorder, remark=req.remark,
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(ManualEntryResponse.model_validate(obj).model_dump())


@router.put("/manual-entries/{oid}", summary="修改手工录入")
def update_manual(oid: int, req: ManualEntryUpdate, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    obj = db.query(ManualEntry).filter(ManualEntry.id == oid).first()
    if not obj:
        return fail("记录不存在")
    data = req.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    et = db.query(EnergyType).filter(EnergyType.id == obj.energy_type_id).first()
    obj.cost = float(calc.calc_cost(obj.consumption, obj.unit_price))
    obj.standard_coal = float(calc.calc_standard_coal(obj.consumption, et.standard_coal_coefficient if et else 0))
    obj.carbon_emission = float(calc.calc_carbon(obj.consumption, et.carbon_factor if et else 0))
    db.commit(); db.refresh(obj)
    return ok(ManualEntryResponse.model_validate(obj).model_dump())


@router.delete("/manual-entries/{oid}", summary="删除手工录入")
def delete_manual(oid: int, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    obj = db.query(ManualEntry).filter(ManualEntry.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 生产数据 ----------------
@router.get("/production", summary="生产数据列表")
def list_production(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    product_id: int = Query(None), start: str = Query(""), end: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(ProductionData)
    if product_id:
        q = q.filter(ProductionData.product_id == product_id)
    if start:
        q = q.filter(ProductionData.stat_date >= _parse_dt(start))
    if end:
        q = q.filter(ProductionData.stat_date <= _parse_dt(end, True))
    total = q.count()
    items = q.order_by(ProductionData.stat_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([ProductionDataResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/production", summary="新增生产数据")
def create_production(req: ProductionDataCreate, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    obj = ProductionData(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(ProductionDataResponse.model_validate(obj).model_dump())


@router.put("/production/{oid}", summary="修改生产数据")
def update_production(oid: int, req: ProductionDataUpdate, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    obj = db.query(ProductionData).filter(ProductionData.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(ProductionDataResponse.model_validate(obj).model_dump())


@router.delete("/production/{oid}", summary="删除生产数据")
def delete_production(oid: int, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    obj = db.query(ProductionData).filter(ProductionData.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 能效指标 ----------------
@router.get("/efficiency-indicators", summary="能效指标列表")
def list_indicators(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(EfficiencyIndicator).order_by(EfficiencyIndicator.sort_order, EfficiencyIndicator.id).all()
    return ok([EfficiencyIndicatorResponse.model_validate(i).model_dump() for i in items])


@router.post("/efficiency-indicators", summary="新增能效指标")
def create_indicator(req: EfficiencyIndicatorCreate, db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    obj = EfficiencyIndicator(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(EfficiencyIndicatorResponse.model_validate(obj).model_dump())


@router.delete("/efficiency-indicators/{oid}", summary="删除能效指标")
def delete_indicator(oid: int, db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    obj = db.query(EfficiencyIndicator).filter(EfficiencyIndicator.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 能效测评 ----------------
@router.get("/efficiency-assessments", summary="能效测评列表")
def list_assessments(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    indicator_id: int = Query(None), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(EfficiencyAssessment)
    if indicator_id:
        q = q.filter(EfficiencyAssessment.indicator_id == indicator_id)
    total = q.count()
    items = q.order_by(EfficiencyAssessment.stat_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([EfficiencyAssessmentResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/efficiency-assessments", summary="新增能效测评（自动算单位能耗/偏差/等级）")
def create_assessment(req: EfficiencyAssessmentCreate, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    indicator = db.query(EfficiencyIndicator).filter(EfficiencyIndicator.id == req.indicator_id).first()
    if not indicator:
        return fail("能效指标不存在")
    benchmark = req.benchmark_value if req.benchmark_value else indicator.benchmark_value
    actual = calc.calc_unit_energy(req.energy_consumption, req.output)
    deviation = calc.calc_deviation(actual, benchmark)
    obj = EfficiencyAssessment(
        indicator_id=req.indicator_id, stat_date=req.stat_date,
        energy_consumption=req.energy_consumption, output=req.output,
        actual_value=float(actual), benchmark_value=benchmark,
        deviation=float(deviation), level=calc.judge_level(deviation), remark=req.remark,
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(EfficiencyAssessmentResponse.model_validate(obj).model_dump())


@router.delete("/efficiency-assessments/{oid}", summary="删除能效测评")
def delete_assessment(oid: int, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    obj = db.query(EfficiencyAssessment).filter(EfficiencyAssessment.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 能流节点 ----------------
@router.get("/flow-nodes", summary="能流节点列表")
def list_nodes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(EnergyFlowNode).order_by(EnergyFlowNode.sort_order, EnergyFlowNode.id).all()
    return ok([EnergyFlowNodeResponse.model_validate(i).model_dump() for i in items])


@router.post("/flow-nodes", summary="新增能流节点")
def create_node(req: EnergyFlowNodeCreate, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    obj = EnergyFlowNode(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(EnergyFlowNodeResponse.model_validate(obj).model_dump())


@router.delete("/flow-nodes/{oid}", summary="删除能流节点")
def delete_node(oid: int, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    obj = db.query(EnergyFlowNode).filter(EnergyFlowNode.id == oid).first()
    if not obj:
        return fail("记录不存在")
    if db.query(EnergyFlowLink).filter(
        (EnergyFlowLink.source_node_id == oid) | (EnergyFlowLink.target_node_id == oid)).first():
        return fail("该节点已存在连接，无法删除")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 能流连接 ----------------
@router.get("/flow-links", summary="能流连接列表")
def list_links(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(EnergyFlowLink).order_by(EnergyFlowLink.id).all()
    return ok([EnergyFlowLinkResponse.model_validate(i).model_dump() for i in items])


@router.post("/flow-links", summary="新增能流连接")
def create_link(req: EnergyFlowLinkCreate, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    obj = EnergyFlowLink(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(EnergyFlowLinkResponse.model_validate(obj).model_dump())


@router.delete("/flow-links/{oid}", summary="删除能流连接")
def delete_link(oid: int, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    obj = db.query(EnergyFlowLink).filter(EnergyFlowLink.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


@router.post("/flow-auto-build", summary="从能耗数据自动生成能流桑基图(能源类型→用能单元)")
def auto_build_flow(year: int = Query(default=None, description="年度，默认当前年"),
                    db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """基于 meter_readings 按 (能源类型 × 用能单元) 聚合标准煤，自动构建桑基图节点与连接。"""
    from sqlalchemy import func
    yr = year or datetime.now().year
    start = datetime(yr, 1, 1)
    end = datetime(yr, 12, 31, 23, 59, 59)
    rows = (
        db.query(EnergyType.name.label("et"), EnergyUnit.name.label("un"),
                 func.sum(MeterReading.standard_coal).label("sc"))
        .join(Meter, MeterReading.meter_id == Meter.id)
        .join(EnergyType, Meter.energy_type_id == EnergyType.id)
        .join(EnergyUnit, Meter.unit_id == EnergyUnit.id)
        .filter(MeterReading.reading_time >= start, MeterReading.reading_time <= end)
        .group_by(EnergyType.name, EnergyUnit.name)
        .all()
    )
    if not rows:
        return fail(f"{yr}年暂无读数数据，无法生成能流图")
    # 清空旧的能流数据
    db.query(EnergyFlowLink).delete()
    db.query(EnergyFlowNode).delete()
    # 能源类型节点(输入) + 用能单元节点(利用)
    node_map = {}
    for name in sorted({r.et for r in rows}):
        n = EnergyFlowNode(name=name, node_type="输入", sort_order=0)
        db.add(n); db.flush(); node_map[("et", name)] = n.id
    for name in sorted({r.un for r in rows}):
        n = EnergyFlowNode(name=name, node_type="利用", sort_order=1)
        db.add(n); db.flush(); node_map[("un", name)] = n.id
    link_cnt = 0
    for r in rows:
        db.add(EnergyFlowLink(
            source_node_id=node_map[("et", r.et)],
            target_node_id=node_map[("un", r.un)],
            flow_value=float(r.sc or 0), unit="kgce", loss_rate=0))
        link_cnt += 1
    db.commit()
    return ok({"nodes": len(node_map), "links": link_cnt, "year": yr, "unit": "kgce"},
              message=f"已基于{yr}年数据生成能流图：{len(rows)}条能源流向")


# ---------------- 用能预算 ----------------
@router.get("/energy-budgets", summary="用能预算列表")
def list_energy_budgets(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    year: int = Query(None), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(EnergyBudget)
    if year:
        q = q.filter(EnergyBudget.year == year)
    total = q.count()
    items = q.order_by(EnergyBudget.year.desc(), EnergyBudget.month).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([EnergyBudgetResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/energy-budgets", summary="新增用能预算（自动算预算量）")
def create_energy_budget(req: EnergyBudgetCreate, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    budget_value = req.budget_value if req.budget_value else float(
        calc.calc_budget_value(req.unit_consumption, req.planned_output))
    obj = EnergyBudget(**req.model_dump(exclude={"budget_value"}), budget_value=budget_value)
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(EnergyBudgetResponse.model_validate(obj).model_dump())


@router.put("/energy-budgets/{oid}", summary="修改用能预算")
def update_energy_budget(oid: int, req: EnergyBudgetUpdate, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    obj = db.query(EnergyBudget).filter(EnergyBudget.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(EnergyBudgetResponse.model_validate(obj).model_dump())


@router.delete("/energy-budgets/{oid}", summary="删除用能预算")
def delete_energy_budget(oid: int, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    obj = db.query(EnergyBudget).filter(EnergyBudget.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 碳排放预算 ----------------
@router.get("/carbon-budgets", summary="碳排放预算列表")
def list_carbon_budgets(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    year: int = Query(None), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(CarbonBudget)
    if year:
        q = q.filter(CarbonBudget.year == year)
    total = q.count()
    items = q.order_by(CarbonBudget.year.desc(), CarbonBudget.month).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([CarbonBudgetResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/carbon-budgets", summary="新增碳排放预算（自动算预算碳排）")
def create_carbon_budget(req: CarbonBudgetCreate, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    budget_carbon = req.budget_carbon if req.budget_carbon else float(
        calc.calc_budget_carbon(req.carbon_intensity, req.planned_output))
    obj = CarbonBudget(**req.model_dump(exclude={"budget_carbon"}), budget_carbon=budget_carbon)
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(CarbonBudgetResponse.model_validate(obj).model_dump())


@router.put("/carbon-budgets/{oid}", summary="修改碳排放预算")
def update_carbon_budget(oid: int, req: CarbonBudgetUpdate, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    obj = db.query(CarbonBudget).filter(CarbonBudget.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(CarbonBudgetResponse.model_validate(obj).model_dump())


@router.delete("/carbon-budgets/{oid}", summary="删除碳排放预算")
def delete_carbon_budget(oid: int, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    obj = db.query(CarbonBudget).filter(CarbonBudget.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 统计接口 ----------------

def _group_by_energy_type(db, unit_id, start, end):
    """从表计读数聚合：按能源类型汇总消耗量/费用/标煤/碳排。"""
    q = db.query(MeterReading).join(Meter, MeterReading.meter_id == Meter.id)
    if unit_id:
        q = q.filter(Meter.unit_id == unit_id)
    if start:
        q = q.filter(MeterReading.reading_time >= _parse_dt(start))
    if end:
        q = q.filter(MeterReading.reading_time <= _parse_dt(end, True))
    rows = q.all()
    result = {}
    for r in rows:
        meter = db.query(Meter).filter(Meter.id == r.meter_id).first()
        et = db.query(EnergyType).filter(EnergyType.id == meter.energy_type_id).first() if meter else None
        name = et.name if et else f"能源{meter.energy_type_id}"
        unit = et.unit if et else ""
        g = result.setdefault(name, {"energy_type": name, "unit": unit,
                                     "consumption": 0.0, "cost": 0.0,
                                     "standard_coal": 0.0, "carbon_emission": 0.0})
        # Numeric 字段返回 Decimal，统一转 float 参与累加，避免 float+Decimal 类型错误
        g["consumption"] += float(r.consumption or 0)
        g["cost"] += float(r.cost or 0)
        g["standard_coal"] += float(r.standard_coal or 0)
        g["carbon_emission"] += float(r.carbon_emission or 0)
    return list(result.values())


@router.get("/comprehensive", summary="综合能耗（按能源类型汇总）")
def comprehensive(
    unit_id: int = Query(None), start: str = Query(""), end: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    groups = _group_by_energy_type(db, unit_id, start, end)
    total_cons = sum(g["consumption"] for g in groups)
    total_cost = sum(g["cost"] for g in groups)
    total_coal = sum(g["standard_coal"] for g in groups)
    total_carbon = sum(g["carbon_emission"] for g in groups)
    for g in groups:
        g["ratio"] = round(g["carbon_emission"] / total_carbon * 100, 2) if total_carbon else 0
    groups.sort(key=lambda x: x["carbon_emission"], reverse=True)
    return ok({
        "total_consumption": round(total_cons, 4),
        "total_cost": round(total_cost, 2),
        "total_standard_coal": round(total_coal, 4),
        "total_carbon": round(total_carbon, 6),
        "energy_type_count": len(groups),
        "items": groups,
    })


@router.get("/unit-stat", summary="单元统计（按周期汇总）")
def unit_stat(
    unit_id: int = Query(None), period: str = Query("month"),  # day/month/year
    start: str = Query(""), end: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(MeterReading).join(Meter, MeterReading.meter_id == Meter.id)
    if unit_id:
        q = q.filter(Meter.unit_id == unit_id)
    if start:
        q = q.filter(MeterReading.reading_time >= _parse_dt(start))
    if end:
        q = q.filter(MeterReading.reading_time <= _parse_dt(end, True))
    rows = q.all()
    result = {}
    for r in rows:
        d = r.reading_time
        if period == "day":
            key = d.strftime("%Y-%m-%d")
        elif period == "year":
            key = d.strftime("%Y")
        else:
            key = d.strftime("%Y-%m")
        g = result.setdefault(key, {"period": key, "consumption": 0.0, "cost": 0.0,
                                    "standard_coal": 0.0, "carbon_emission": 0.0})
        g["consumption"] += float(r.consumption or 0)
        g["cost"] += float(r.cost or 0)
        g["standard_coal"] += float(r.standard_coal or 0)
        g["carbon_emission"] += float(r.carbon_emission or 0)
    items = sorted(result.values(), key=lambda x: x["period"])
    total = {"consumption": 0.0, "cost": 0.0, "standard_coal": 0.0, "carbon_emission": 0.0}
    for it in items:
        for k in total:
            total[k] += it[k]
    return ok({"items": items, "total": {k: round(v, 6) for k, v in total.items()}})


@router.get("/meter-query", summary="计量查询（单表计按周期）")
def meter_query(
    meter_id: int = Query(None), period: str = Query("month"),
    start: str = Query(""), end: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(MeterReading)
    if meter_id:
        q = q.filter(MeterReading.meter_id == meter_id)
    if start:
        q = q.filter(MeterReading.reading_time >= _parse_dt(start))
    if end:
        q = q.filter(MeterReading.reading_time <= _parse_dt(end, True))
    rows = q.order_by(MeterReading.reading_time).all()
    result = {}
    for r in rows:
        d = r.reading_time
        key = d.strftime("%Y-%m-%d") if period == "day" else (d.strftime("%Y") if period == "year" else d.strftime("%Y-%m"))
        g = result.setdefault(key, {"period": key, "last_reading": 0, "current_reading": 0,
                                    "consumption": 0.0, "cost": 0.0,
                                    "standard_coal": 0.0, "carbon_emission": 0.0})
        g["last_reading"] = r.last_reading
        g["current_reading"] = r.current_reading
        g["consumption"] += float(r.consumption or 0)
        g["cost"] += float(r.cost or 0)
        g["standard_coal"] += float(r.standard_coal or 0)
        g["carbon_emission"] += float(r.carbon_emission or 0)
    items = sorted(result.values(), key=lambda x: x["period"])
    return ok({"items": items})


# ---------------- 能源分析（对标/环比） ----------------

@router.get("/compare", summary="计量/单元对标（双对象按周期）")
def compare(
    type_a: int = Query(..., description="表计或单元ID"), type_b: int = Query(..., description="表计或单元ID"),
    dimension: str = Query("carbon", description="energy/cost/coal/carbon"),
    mode: str = Query("meter", description="meter/unit"),
    start: str = Query(""), end: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    field_map = {"energy": "consumption", "cost": "cost", "coal": "standard_coal", "carbon": "carbon_emission"}

    def fetch(target_id):
        q = db.query(MeterReading)
        if mode == "meter":
            q = q.filter(MeterReading.meter_id == target_id)
        else:
            q = q.join(Meter, MeterReading.meter_id == Meter.id).filter(Meter.unit_id == target_id)
        if start:
            q = q.filter(MeterReading.reading_time >= _parse_dt(start))
        if end:
            q = q.filter(MeterReading.reading_time <= _parse_dt(end, True))
        return float(sum(getattr(r, field_map[dimension]) or 0 for r in q.all()))

    a_val = fetch(type_a)
    b_val = fetch(type_b)
    diff = a_val - b_val
    diff_rate = round(diff / b_val * 100, 2) if b_val else 0
    return ok({"a_value": round(a_val, 6), "b_value": round(b_val, 6),
               "diff": round(diff, 6), "diff_rate": diff_rate})


@router.get("/ratio", summary="计量/单元环比（本期 vs 上期）")
def ratio(
    target_id: int = Query(..., description="表计或单元ID"),
    dimension: str = Query("carbon"), mode: str = Query("meter"),
    current_start: str = Query(""), current_end: str = Query(""),
    last_start: str = Query(""), last_end: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    field_map = {"energy": "consumption", "cost": "cost", "coal": "standard_coal", "carbon": "carbon_emission"}

    def fetch(s, e, tid):
        q = db.query(MeterReading)
        if mode == "meter":
            q = q.filter(MeterReading.meter_id == tid)
        else:
            q = q.join(Meter, MeterReading.meter_id == Meter.id).filter(Meter.unit_id == tid)
        if s:
            q = q.filter(MeterReading.reading_time >= _parse_dt(s))
        if e:
            q = q.filter(MeterReading.reading_time <= _parse_dt(e, True))
        return float(sum(getattr(r, field_map[dimension]) or 0 for r in q.all()))

    cur = fetch(current_start, current_end, target_id)
    last = fetch(last_start, last_end, target_id)
    diff = cur - last
    ratio_pct = round(diff / last * 100, 2) if last else 0
    return ok({"current": round(cur, 6), "last": round(last, 6),
               "diff": round(diff, 6), "ratio": ratio_pct})
