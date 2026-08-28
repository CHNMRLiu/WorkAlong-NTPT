"""看板 / 数据大屏统计接口。"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    CarbonAccounting,
    CarbonBudget,
    EmissionSource,
    EnergyBudget,
    EnergyType,
    EnergyUnit,
    Meter,
    MeterReading,
    Organization,
    ProductionData,
    SupplierCarbonData,
)
from ..utils.response import ok
from .deps import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["看板"])


@router.get("/summary", summary="看板汇总（核心指标）")
def dashboard_summary(year: int = Query(None), db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    y = year or datetime.now().year
    org = db.query(Organization).order_by(Organization.id).first()

    # 当年读数汇总
    readings = db.query(MeterReading).filter(
        MeterReading.reading_time >= datetime(y, 1, 1),
        MeterReading.reading_time <= datetime(y, 12, 31, 23, 59, 59)).all()
    # Numeric 字段返回 Decimal，统一转 float，避免 Decimal 与 float 混算报错
    total_consumption = float(sum(r.consumption or 0 for r in readings))
    total_cost = float(sum(r.cost or 0 for r in readings))
    total_coal = float(sum(r.standard_coal or 0 for r in readings))
    total_carbon = float(sum(r.carbon_emission or 0 for r in readings))

    # 当年生产
    prod = db.query(ProductionData).filter(
        ProductionData.stat_date >= datetime(y, 1, 1),
        ProductionData.stat_date <= datetime(y, 12, 31, 23, 59, 59)).all()
    total_output = float(sum(p.output or 0 for p in prod))
    total_value = float(sum(p.output_value or 0 for p in prod))

    # 强度：单位产值能耗(kgce/万元) = 总标煤(kgce) / 总产值(万元)
    energy_per_value = round(total_coal / (total_value / 10000), 4) if total_value else 0
    carbon_intensity_value = round((total_carbon / 1000) / (total_value / 10000), 6) if total_value else 0
    carbon_intensity_product = round((total_carbon / 1000) / total_output, 6) if total_output else 0

    # 供应链范围3（供应商碳数据）
    supply_chain_carbon = float(sum(
        sr.emission or 0 for sr in db.query(SupplierCarbonData).filter(SupplierCarbonData.year == y).all()))

    return ok({
        "year": y,
        "org_name": org.name if org else "",
        "total_consumption": round(total_consumption, 4),
        "total_cost": round(total_cost, 2),
        "total_standard_coal": round(total_coal, 4),
        "total_carbon": round(total_carbon, 6),
        "supply_chain_carbon": round(supply_chain_carbon, 6),
        "total_output": round(total_output, 4),
        "total_output_value": round(total_value, 2),
        "energy_per_value": energy_per_value,
        "carbon_intensity_value": carbon_intensity_value,
        "carbon_intensity_product": carbon_intensity_product,
    })


@router.get("/carbon-trend", summary="碳排放月度趋势")
def carbon_trend(year: int = Query(None), db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    y = year or datetime.now().year
    rows = db.query(CarbonAccounting).filter(CarbonAccounting.year == y).all()
    monthly = {f"{y}-{m:02d}": 0.0 for m in range(1, 13)}
    for r in rows:
        key = f"{r.year}-{r.month:02d}"
        if key in monthly:
            monthly[key] += float(r.emission or 0)
    return ok([{"month": k, "emission": round(v, 6)} for k, v in monthly.items()])


@router.get("/energy-structure", summary="能源消费结构（按能源类型）")
def energy_structure(year: int = Query(None), db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    y = year or datetime.now().year
    readings = db.query(MeterReading).filter(
        MeterReading.reading_time >= datetime(y, 1, 1),
        MeterReading.reading_time <= datetime(y, 12, 31, 23, 59, 59)).all()
    result = {}
    for r in readings:
        meter = db.query(Meter).filter(Meter.id == r.meter_id).first()
        et = db.query(EnergyType).filter(EnergyType.id == meter.energy_type_id).first() if meter else None
        name = et.name if et else "未知"
        result[name] = result.get(name, 0.0) + float(r.consumption or 0)
    total = sum(result.values()) or 1
    items = [{"name": k, "value": round(v, 4), "ratio": round(v / total * 100, 2)}
             for k, v in sorted(result.items(), key=lambda x: -x[1])]
    return ok(items)


@router.get("/unit-ranking", summary="用能单元能耗排行")
def unit_ranking(year: int = Query(None), dimension: str = Query("carbon"),
                 db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    y = year or datetime.now().year
    field_map = {"energy": "consumption", "cost": "cost", "coal": "standard_coal", "carbon": "carbon_emission"}
    readings = db.query(MeterReading).filter(
        MeterReading.reading_time >= datetime(y, 1, 1),
        MeterReading.reading_time <= datetime(y, 12, 31, 23, 59, 59)).all()
    result = {}
    for r in readings:
        meter = db.query(Meter).filter(Meter.id == r.meter_id).first()
        if not meter:
            continue
        unit = db.query(EnergyUnit).filter(EnergyUnit.id == meter.unit_id).first()
        name = unit.name if unit else f"单元{meter.unit_id}"
        result[name] = result.get(name, 0.0) + float(getattr(r, field_map[dimension]) or 0)
    items = [{"name": k, "value": round(v, 6)} for k, v in
             sorted(result.items(), key=lambda x: -x[1])[:10]]
    return ok(items)


@router.get("/scope-breakdown", summary="碳排放范围占比")
def scope_breakdown(year: int = Query(None), db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    y = year or datetime.now().year
    rows = db.query(CarbonAccounting).filter(CarbonAccounting.year == y).all()
    scope_sum = {"范围1": 0.0, "范围2": 0.0, "范围3": 0.0}
    for r in rows:
        src = db.query(EmissionSource).filter(EmissionSource.id == r.source_id).first()
        sc = src.scope if src else "范围1"
        if sc in scope_sum:
            scope_sum[sc] += float(r.emission or 0)
    # 供应链范围3（供应商碳数据）并入范围占比
    for sr in db.query(SupplierCarbonData).filter(SupplierCarbonData.year == y).all():
        scope_sum["范围3"] += float(sr.emission or 0)
    total = sum(scope_sum.values()) or 1
    items = [{"name": k, "value": round(v, 6), "ratio": round(v / total * 100, 2)}
             for k, v in scope_sum.items()]
    return ok(items)


@router.get("/recent", summary="最新录入数据（大屏滚动）")
def recent_entries(limit: int = Query(10), db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    rows = db.query(MeterReading).order_by(MeterReading.created_at.desc()).limit(limit).all()
    items = []
    for r in rows:
        meter = db.query(Meter).filter(Meter.id == r.meter_id).first()
        items.append({
            "time": r.reading_time.strftime("%Y-%m-%d %H:%M"),
            "meter": meter.name if meter else "",
            "consumption": round(r.consumption or 0, 4),
            "carbon": round(r.carbon_emission or 0, 6),
        })
    return ok(items)
