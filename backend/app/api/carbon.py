"""碳管理接口：碳核算、碳统计、碳报告、产品碳足迹、供应链、碳核查、碳资产、配额交易。"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    CarbonAccounting,
    CarbonAsset,
    CarbonEvidence,
    CarbonFactor,
    CarbonReport,
    CarbonVerification,
    EmissionSource,
    Product,
    ProductFootprint,
    ProductionData,
    QuotaRecord,
    Supplier,
    SupplierCarbonData,
)
from ..schemas import (
    CarbonAccountingCreate, CarbonAccountingResponse, CarbonAccountingUpdate,
    CarbonAssetCreate, CarbonAssetResponse, CarbonAssetUpdate,
    CarbonEvidenceCreate, CarbonEvidenceResponse, CarbonEvidenceUpdate,
    CarbonReportCreate, CarbonReportResponse, CarbonReportUpdate,
    CarbonVerificationCreate, CarbonVerificationResponse, CarbonVerificationUpdate,
    ProductFootprintCreate, ProductFootprintResponse, ProductFootprintUpdate,
    QuotaRecordCreate, QuotaRecordResponse, QuotaRecordUpdate,
    SupplierCreate, SupplierResponse, SupplierUpdate,
    SupplierCarbonDataCreate, SupplierCarbonDataResponse, SupplierCarbonDataUpdate,
)
from ..utils import calculator as calc
from ..utils.response import fail, ok, page as page_resp
from .deps import get_current_user

router = APIRouter(prefix="/api/carbon", tags=["碳排放"])


# ---------------- 碳核算 ----------------
@router.get("/accounting", summary="碳核算列表")
def list_accounting(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    year: int = Query(None), scope: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(CarbonAccounting)
    if year:
        q = q.filter(CarbonAccounting.year == year)
    if scope:
        q = q.join(EmissionSource, CarbonAccounting.source_id == EmissionSource.id).filter(EmissionSource.scope == scope)
    total = q.count()
    items = q.order_by(CarbonAccounting.year.desc(), CarbonAccounting.month).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([CarbonAccountingResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/accounting", summary="新增碳核算（自动算排放量）")
def create_accounting(req: CarbonAccountingCreate, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    emission = float(calc.calc_emission_from_factor(req.activity_data, req.emission_factor))
    obj = CarbonAccounting(**req.model_dump(), emission=emission)
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(CarbonAccountingResponse.model_validate(obj).model_dump())


@router.put("/accounting/{oid}", summary="修改碳核算")
def update_accounting(oid: int, req: CarbonAccountingUpdate, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    obj = db.query(CarbonAccounting).filter(CarbonAccounting.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    obj.emission = float(calc.calc_emission_from_factor(obj.activity_data, obj.emission_factor))
    db.commit(); db.refresh(obj)
    return ok(CarbonAccountingResponse.model_validate(obj).model_dump())


@router.delete("/accounting/{oid}", summary="删除碳核算")
def delete_accounting(oid: int, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    obj = db.query(CarbonAccounting).filter(CarbonAccounting.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 碳统计 ----------------
@router.get("/statistics", summary="碳排统计（范围/排放源/月度）")
def carbon_statistics(
    year: int = Query(None), scope: str = Query(""),  # 范围1/2/3/全部
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(CarbonAccounting).join(EmissionSource, CarbonAccounting.source_id == EmissionSource.id)
    if year:
        q = q.filter(CarbonAccounting.year == year)
    rows = q.all()

    scope_sum = {"范围1": 0.0, "范围2": 0.0, "范围3": 0.0}
    source_map = {}
    monthly = {}
    total = 0.0
    for r in rows:
        src = db.query(EmissionSource).filter(EmissionSource.id == r.source_id).first()
        sc = src.scope if src else "范围1"
        if scope and scope != "全部" and sc != scope:
            continue
        em = float(r.emission or 0)
        if sc in scope_sum:
            scope_sum[sc] += em
        total += em
        name = src.name if src else f"源{r.source_id}"
        s = source_map.setdefault(name, {"name": name, "scope": sc, "emission": 0.0})
        s["emission"] += em
        key = f"{r.year}-{r.month:02d}"
        m = monthly.setdefault(key, {"month": key, "emission": 0.0})
        m["emission"] += em

    # 供应链范围3（供应商碳数据）并入碳核算统计，形成完整范围1/2/3 闭环
    show_supplier = (not scope) or scope == "全部" or scope == "范围3"
    if show_supplier:
        sup_q = db.query(SupplierCarbonData)
        if year:
            sup_q = sup_q.filter(SupplierCarbonData.year == year)
        for sr in sup_q.all():
            em = float(sr.emission or 0)
            scope_sum["范围3"] += em
            total += em
            sup = db.query(Supplier).filter(Supplier.id == sr.supplier_id).first()
            sname = f"供应链·{sup.name if sup else sr.supplier_id}"
            s = source_map.setdefault(sname, {"name": sname, "scope": "范围3", "emission": 0.0})
            s["emission"] += em

    sources = sorted(source_map.values(), key=lambda x: x["emission"], reverse=True)
    for s in sources:
        s["ratio"] = round(s["emission"] / total * 100, 2) if total else 0
    monthly_list = sorted(monthly.values(), key=lambda x: x["month"])
    return ok({
        "scope1": round(scope_sum["范围1"], 6),
        "scope2": round(scope_sum["范围2"], 6),
        "scope3": round(scope_sum["范围3"], 6),
        "total": round(total, 6),
        "sources": sources,
        "monthly": monthly_list,
    })


# ---------------- 碳报告 ----------------
@router.get("/reports", summary="碳报告列表")
def list_reports(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(CarbonReport).order_by(CarbonReport.year.desc()).all()
    return ok([CarbonReportResponse.model_validate(i).model_dump() for i in items])


@router.post("/reports/generate", summary="生成碳报告（汇总碳核算+供应链）")
def generate_report(req: CarbonReportCreate, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    year = req.year
    rows = db.query(CarbonAccounting).filter(CarbonAccounting.year == year).all()
    scope_sum = {"范围1": 0.0, "范围2": 0.0, "范围3": 0.0}
    source_items = []
    total = 0.0
    for r in rows:
        src = db.query(EmissionSource).filter(EmissionSource.id == r.source_id).first()
        sc = src.scope if src else "范围1"
        if sc in scope_sum:
            scope_sum[sc] += float(r.emission or 0)
        total += float(r.emission or 0)
        source_items.append({
            "source_name": src.name if src else "",
            "scope": sc, "activity_data": r.activity_data,
            "unit": r.unit, "emission_factor": r.emission_factor,
            "emission": round(r.emission or 0, 6),
        })
    # 供应链范围3（供应商碳数据）并入报告，形成完整范围1/2/3
    sup_rows = db.query(SupplierCarbonData).filter(SupplierCarbonData.year == year).all()
    for sr in sup_rows:
        scope_sum["范围3"] += float(sr.emission or 0)
        total += float(sr.emission or 0)
        sup = db.query(Supplier).filter(Supplier.id == sr.supplier_id).first()
        source_items.append({
            "source_name": f"供应链·{sup.name if sup else sr.supplier_id}",
            "scope": "范围3", "activity_data": sr.quantity,
            "unit": sr.unit, "emission_factor": sr.emission_factor,
            "emission": round(sr.emission or 0, 6),
        })
    # 强度：产值强度(tCO2/万元) = 总排放(tCO2) / 总产值(万元)
    prod = db.query(ProductionData).filter(
        ProductionData.stat_date >= datetime(year, 1, 1),
        ProductionData.stat_date <= datetime(year, 12, 31, 23, 59, 59)).all()
    total_value = float(sum(p.output_value or 0 for p in prod))
    total_output = float(sum(p.output or 0 for p in prod))
    intensity_value = round((total / 1000) / (total_value / 10000), 6) if total_value else 0
    product_intensity = round((total / 1000) / total_output, 6) if total_output else 0

    obj = db.query(CarbonReport).filter(CarbonReport.year == year).first()
    if not obj:
        obj = CarbonReport(year=year)
        db.add(obj)
    obj.total_emission = round(total, 6)
    obj.scope1 = round(scope_sum["范围1"], 6)
    obj.scope2 = round(scope_sum["范围2"], 6)
    obj.scope3 = round(scope_sum["范围3"], 6)
    obj.intensity_value = intensity_value
    obj.product_intensity = product_intensity
    obj.per_capita = 0
    obj.report_date = req.report_date
    obj.status = "已生成"
    db.commit(); db.refresh(obj)
    # 碳资产盈亏：配额/CCER 总量 vs 实际排放
    assets = db.query(CarbonAsset).filter(CarbonAsset.year == year).all()
    total_quota = float(sum(a.quantity or 0 for a in assets if a.asset_type == "配额"))
    total_ccer = float(sum(a.quantity or 0 for a in assets if a.asset_type == "CCER"))
    asset_summary = {
        "year": year,
        "actual_emission": round(total, 6),
        "total_quota": round(total_quota, 6),
        "total_ccer": round(total_ccer, 6),
        "surplus": round(total_quota + total_ccer - total, 6),  # 正=盈余 负=缺口
    }
    return ok({
        "report": CarbonReportResponse.model_validate(obj).model_dump(),
        "sources": source_items,
        "asset_summary": asset_summary,
    })


@router.put("/reports/{oid}", summary="更新碳报告文本")
def update_report(oid: int, req: CarbonReportUpdate, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    obj = db.query(CarbonReport).filter(CarbonReport.id == oid).first()
    if not obj:
        return fail("报告不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(CarbonReportResponse.model_validate(obj).model_dump())


# ---------------- 产品碳足迹 ----------------
@router.get("/footprints", summary="产品碳足迹列表")
def list_footprints(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    product_id: int = Query(None), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(ProductFootprint)
    if product_id:
        q = q.filter(ProductFootprint.product_id == product_id)
    total = q.count()
    items = q.order_by(ProductFootprint.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([ProductFootprintResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/footprints", summary="新增产品碳足迹（自动合计）")
def create_footprint(req: ProductFootprintCreate, db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    total = float(calc.calc_total_footprint(
        req.raw_material, req.production, req.transport, req.use_phase, req.disposal))
    obj = ProductFootprint(**req.model_dump(), total=total)
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(ProductFootprintResponse.model_validate(obj).model_dump())


@router.put("/footprints/{oid}", summary="修改产品碳足迹")
def update_footprint(oid: int, req: ProductFootprintUpdate, db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    obj = db.query(ProductFootprint).filter(ProductFootprint.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    obj.total = float(calc.calc_total_footprint(
        obj.raw_material, obj.production, obj.transport, obj.use_phase, obj.disposal))
    db.commit(); db.refresh(obj)
    return ok(ProductFootprintResponse.model_validate(obj).model_dump())


@router.delete("/footprints/{oid}", summary="删除产品碳足迹")
def delete_footprint(oid: int, db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    obj = db.query(ProductFootprint).filter(ProductFootprint.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


@router.post("/footprints/auto-allocate", summary="按产量分摊公司排放生成产品碳足迹")
def auto_allocate_footprint(
    year: int = Query(default=None, description="年度，默认当前年"),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    """打通 碳核算(总排放) × 生产数据(各产品产量) → 产品碳足迹(生产碳排)。
    按各产品当年产量占比，将公司总排放分摊为该产品的 production 碳排字段。"""
    yr = year or datetime.now().year
    # 公司当年总排放（范围1+2，生产相关）
    rows = db.query(CarbonAccounting).filter(CarbonAccounting.year == yr).all()
    company_total = float(sum(r.emission or 0 for r in rows))
    # 各产品当年产量
    prod = db.query(ProductionData).filter(
        ProductionData.stat_date >= datetime(yr, 1, 1),
        ProductionData.stat_date <= datetime(yr, 12, 31, 23, 59, 59)).all()
    by_product = {}
    for p in prod:
        by_product[p.product_id] = float(by_product.get(p.product_id, 0)) + float(p.output or 0)
    total_output = float(sum(by_product.values()))
    if not total_output:
        return fail(f"请先在「生产数据」录入 {yr} 年各产品产量后再分摊")
    created = 0
    updated = 0
    for pid, out in by_product.items():
        share = out / total_output
        prod_emission = round(company_total * share, 6)
        fp = db.query(ProductFootprint).filter(ProductFootprint.product_id == pid).order_by(ProductFootprint.id.desc()).first()
        if fp:
            fp.production = prod_emission
            fp.total = float(calc.calc_total_footprint(
                fp.raw_material, fp.production, fp.transport, fp.use_phase, fp.disposal))
            updated += 1
        else:
            prod_obj = db.query(Product).filter(Product.id == pid).first()
            fp = ProductFootprint(
                product_id=pid,
                functional_unit=(prod_obj.output_unit if prod_obj else "吨"),
                boundary="从摇篮到大门",
                production=prod_emission,
                total=prod_emission,
            )
            db.add(fp)
            created += 1
    db.commit()
    return ok({
        "year": yr,
        "company_total": round(company_total, 6),
        "total_output": round(total_output, 4),
        "created": created,
        "updated": updated,
    }, message=f"已按产量分摊：新建 {created} 条、更新 {updated} 条产品碳足迹")


# ---------------- 供应商 ----------------
@router.get("/suppliers", summary="供应商列表")
def list_suppliers(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    keyword: str = Query(""), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Supplier)
    if keyword:
        q = q.filter(Supplier.name.ilike(f"%{keyword}%"))
    total = q.count()
    items = q.order_by(Supplier.id).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([SupplierResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/suppliers", summary="新增供应商")
def create_supplier(req: SupplierCreate, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    obj = Supplier(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(SupplierResponse.model_validate(obj).model_dump())


@router.put("/suppliers/{oid}", summary="修改供应商")
def update_supplier(oid: int, req: SupplierUpdate, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    obj = db.query(Supplier).filter(Supplier.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(SupplierResponse.model_validate(obj).model_dump())


@router.delete("/suppliers/{oid}", summary="删除供应商")
def delete_supplier(oid: int, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    obj = db.query(Supplier).filter(Supplier.id == oid).first()
    if not obj:
        return fail("记录不存在")
    if db.query(SupplierCarbonData).filter(SupplierCarbonData.supplier_id == oid).first():
        return fail("该供应商已有碳数据，无法删除")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 供应商碳数据 ----------------
@router.get("/supplier-carbon-data", summary="供应商碳数据列表")
def list_supplier_carbon(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    supplier_id: int = Query(None), year: int = Query(None),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(SupplierCarbonData)
    if supplier_id:
        q = q.filter(SupplierCarbonData.supplier_id == supplier_id)
    if year:
        q = q.filter(SupplierCarbonData.year == year)
    total = q.count()
    items = q.order_by(SupplierCarbonData.year.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([SupplierCarbonDataResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/supplier-carbon-data", summary="录入供应商碳数据（自动算排放量）")
def create_supplier_carbon(req: SupplierCarbonDataCreate, db: Session = Depends(get_db),
                           current_user=Depends(get_current_user)):
    emission = float(calc.calc_emission_from_factor(req.quantity, req.emission_factor))
    obj = SupplierCarbonData(**req.model_dump(), emission=emission)
    db.add(obj)
    sup = db.query(Supplier).filter(Supplier.id == req.supplier_id).first()
    if sup:
        sup.total_emission = float((sup.total_emission or 0) + emission)
    db.commit(); db.refresh(obj)
    return ok(SupplierCarbonDataResponse.model_validate(obj).model_dump())


@router.delete("/supplier-carbon-data/{oid}", summary="删除供应商碳数据")
def delete_supplier_carbon(oid: int, db: Session = Depends(get_db),
                           current_user=Depends(get_current_user)):
    obj = db.query(SupplierCarbonData).filter(SupplierCarbonData.id == oid).first()
    if not obj:
        return fail("记录不存在")
    sup = db.query(Supplier).filter(Supplier.id == obj.supplier_id).first()
    if sup:
        sup.total_emission = float(max(0, (sup.total_emission or 0) - (obj.emission or 0)))
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 供应链汇总 / 预算实际值 / 碳资产盈亏 ----------------

@router.get("/supply-chain/summary", summary="供应链碳汇总（范围3）")
def supply_chain_summary(year: int = Query(None), db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    yr = year or datetime.now().year
    rows = db.query(SupplierCarbonData).filter(SupplierCarbonData.year == yr).all()
    total = 0.0
    sup_map = {}
    for sr in rows:
        em = float(sr.emission or 0)
        total += em
        sup = db.query(Supplier).filter(Supplier.id == sr.supplier_id).first()
        name = sup.name if sup else f"供应商{sr.supplier_id}"
        g = sup_map.setdefault(name, {"supplier": name, "emission": 0.0,
                                     "risk": sup.risk_level if sup else ""})
        g["emission"] += em
    top = sorted(sup_map.values(), key=lambda x: -x["emission"])[:10]
    return ok({
        "year": yr,
        "scope3_total": round(total, 6),
        "supplier_count": len(sup_map),
        "top": top,
    })


@router.get("/budgets/actual", summary="碳排放预算实际值（取碳核算+供应链）")
def carbon_budget_actual(
    year: int = Query(...), month: int = Query(None), unit_id: int = Query(None),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    """打通 碳核算 / 供应链 → 碳排放预算：返回某口径下实际碳排放，供预算一键同步。"""
    q = db.query(CarbonAccounting).filter(CarbonAccounting.year == year)
    if month:
        q = q.filter(CarbonAccounting.month == month)
    s12 = float(sum(r.emission or 0 for r in q.all()))
    # 供应链范围3 按年并入（供应商数据无月份维度）
    sup = db.query(SupplierCarbonData).filter(SupplierCarbonData.year == year)
    s3 = float(sum(sr.emission or 0 for sr in sup.all()))
    return ok({
        "year": year, "month": month,
        "scope1_2": round(s12, 6),
        "scope3": round(s3, 6),
        "actual_carbon": round(s12 + s3, 6),
    })


@router.get("/assets/balance", summary="碳资产盈亏（配额/CCER vs 实际排放）")
def carbon_asset_balance(year: int = Query(...), db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
    """打通 碳核算 / 供应链(实际排放) → 碳资产：返回配额+CCER 总量与实际排放的盈余/缺口。"""
    actual = float(sum(r.emission or 0 for r in db.query(CarbonAccounting).filter(CarbonAccounting.year == year).all()))
    actual += float(sum(sr.emission or 0 for sr in db.query(SupplierCarbonData).filter(SupplierCarbonData.year == year).all()))
    assets = db.query(CarbonAsset).filter(CarbonAsset.year == year).all()
    total_quota = float(sum(a.quantity or 0 for a in assets if a.asset_type == "配额"))
    total_ccer = float(sum(a.quantity or 0 for a in assets if a.asset_type == "CCER"))
    return ok({
        "year": year,
        "actual_emission": round(actual, 6),
        "total_quota": round(total_quota, 6),
        "total_ccer": round(total_ccer, 6),
        "surplus": round(total_quota + total_ccer - actual, 6),  # 正=盈余 负=缺口
    })


# ---------------- 碳核查 ----------------
@router.get("/verifications", summary="碳核查列表")
def list_verifications(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    year: int = Query(None), status: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(CarbonVerification)
    if year:
        q = q.filter(CarbonVerification.year == year)
    if status:
        q = q.filter(CarbonVerification.status == status)
    total = q.count()
    items = q.order_by(CarbonVerification.year.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([CarbonVerificationResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/verifications", summary="新增碳核查")
def create_verification(req: CarbonVerificationCreate, db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
    obj = CarbonVerification(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(CarbonVerificationResponse.model_validate(obj).model_dump())


@router.put("/verifications/{oid}", summary="修改碳核查")
def update_verification(oid: int, req: CarbonVerificationUpdate, db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
    obj = db.query(CarbonVerification).filter(CarbonVerification.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(CarbonVerificationResponse.model_validate(obj).model_dump())


@router.delete("/verifications/{oid}", summary="删除碳核查")
def delete_verification(oid: int, db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
    obj = db.query(CarbonVerification).filter(CarbonVerification.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 碳核算存证 ----------------
def _gen_evidence_no():
    import random
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"EVD{ts}{random.randint(1000, 9999)}"


@router.get("/evidences", summary="碳核算存证列表")
def list_evidences(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    year: int = Query(None), status: str = Query(""),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(CarbonEvidence)
    if year:
        q = q.filter(CarbonEvidence.year == year)
    if status:
        q = q.filter(CarbonEvidence.status == status)
    total = q.count()
    items = q.order_by(CarbonEvidence.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([CarbonEvidenceResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/evidences", summary="新增碳核算存证（关联核算记录）")
def create_evidence(req: CarbonEvidenceCreate, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    acc = db.query(CarbonAccounting).filter(CarbonAccounting.id == req.accounting_id).first()
    if not acc:
        return fail("关联的碳核算记录不存在")
    src = db.query(EmissionSource).filter(EmissionSource.id == acc.source_id).first()
    obj = CarbonEvidence(
        accounting_id=req.accounting_id,
        year=acc.year, month=acc.month,
        scope=src.scope if src else "",
        source_name=src.name if src else f"源{acc.source_id}",
        emission=float(acc.emission or 0),
        evidence_no=_gen_evidence_no(),
        evidence_hash=req.evidence_hash or "",
        chain_platform=req.chain_platform or "",
        tx_time=req.tx_time,
        status=req.status or "已上链",
        operator=req.operator or "",
        remark=req.remark or "",
    )
    db.add(obj); db.commit()
    # 标记关联核算记录为已存证
    acc.evidence_status = "已存证"
    db.commit(); db.refresh(obj)
    return ok(CarbonEvidenceResponse.model_validate(obj).model_dump())


@router.put("/evidences/{oid}", summary="修改碳核算存证")
def update_evidence(oid: int, req: CarbonEvidenceUpdate, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    obj = db.query(CarbonEvidence).filter(CarbonEvidence.id == oid).first()
    if not obj:
        return fail("存证记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(CarbonEvidenceResponse.model_validate(obj).model_dump())


@router.delete("/evidences/{oid}", summary="删除碳核算存证")
def delete_evidence(oid: int, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    obj = db.query(CarbonEvidence).filter(CarbonEvidence.id == oid).first()
    if not obj:
        return fail("存证记录不存在")
    acc_id = obj.accounting_id
    db.delete(obj); db.commit()
    # 若该核算记录已无其他存证，则回退为未存证
    remaining = db.query(CarbonEvidence).filter(CarbonEvidence.accounting_id == acc_id).count()
    if remaining == 0:
        acc = db.query(CarbonAccounting).filter(CarbonAccounting.id == acc_id).first()
        if acc:
            acc.evidence_status = "未存证"
            db.commit()
    return ok(message="已删除")


# ---------------- 碳资产 ----------------
@router.get("/assets", summary="碳资产列表")
def list_assets(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    year: int = Query(None), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(CarbonAsset)
    if year:
        q = q.filter(CarbonAsset.year == year)
    total = q.count()
    items = q.order_by(CarbonAsset.year.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([CarbonAssetResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/assets", summary="登记碳资产")
def create_asset(req: CarbonAssetCreate, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    obj = CarbonAsset(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(CarbonAssetResponse.model_validate(obj).model_dump())


@router.put("/assets/{oid}", summary="修改碳资产")
def update_asset(oid: int, req: CarbonAssetUpdate, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    obj = db.query(CarbonAsset).filter(CarbonAsset.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(CarbonAssetResponse.model_validate(obj).model_dump())


@router.delete("/assets/{oid}", summary="删除碳资产")
def delete_asset(oid: int, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    obj = db.query(CarbonAsset).filter(CarbonAsset.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 配额交易 ----------------
@router.get("/quota-records", summary="配额交易列表")
def list_quota(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    total = db.query(QuotaRecord).count()
    items = db.query(QuotaRecord).order_by(QuotaRecord.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_resp([QuotaRecordResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/quota-records", summary="新增配额交易（自动算金额）")
def create_quota(req: QuotaRecordCreate, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    total_amount = float(calc.calc_emission_from_factor(req.quantity, req.price))
    obj = QuotaRecord(**req.model_dump(), total_amount=total_amount)
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(QuotaRecordResponse.model_validate(obj).model_dump())


@router.delete("/quota-records/{oid}", summary="删除配额交易")
def delete_quota(oid: int, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    obj = db.query(QuotaRecord).filter(QuotaRecord.id == oid).first()
    if not obj:
        return fail("记录不存在")
    db.delete(obj); db.commit()
    return ok(message="已删除")
