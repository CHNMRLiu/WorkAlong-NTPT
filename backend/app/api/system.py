"""系统管理接口：企业信息、能源类型、用能单元、表计、产品、排放源、碳因子、日志、配置。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    CarbonFactor,
    CarbonAccounting,
    EmissionSource,
    EnergyType,
    EnergyUnit,
    ManualEntry,
    Meter,
    MeterReading,
    OperationLog,
    Organization,
    Product,
    ProductionData,
    EfficiencyIndicator,
    EnergyBudget,
    CarbonBudget,
    ProductFootprint,
    SystemConfig,
)
from ..schemas import (
    CarbonFactorCreate, CarbonFactorResponse, CarbonFactorUpdate,
    EmissionSourceCreate, EmissionSourceResponse, EmissionSourceUpdate,
    EnergyTypeCreate, EnergyTypeResponse, EnergyTypeUpdate,
    EnergyUnitCreate, EnergyUnitResponse, EnergyUnitUpdate,
    MeterCreate, MeterResponse, MeterUpdate,
    OperationLogResponse,
    OrganizationResponse, OrganizationUpdate,
    ProductCreate, ProductResponse, ProductUpdate,
    SystemConfigCreate, SystemConfigResponse, SystemConfigUpdate,
)
from ..utils.response import fail, ok, page as page_resp
from .deps import get_current_user, record_log

router = APIRouter(prefix="/api/system", tags=["系统管理"])


def _paginate(query, page, page_size):
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, items


# ---------------- 企业信息 ----------------
@router.get("/organization", summary="获取企业信息")
def get_organization(db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    org = db.query(Organization).order_by(Organization.id).first()
    if not org:
        return fail("企业信息未初始化")
    return ok(OrganizationResponse.model_validate(org).model_dump())


@router.put("/organization", summary="更新企业信息")
def update_organization(req: OrganizationUpdate, db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
    org = db.query(Organization).order_by(Organization.id).first()
    if not org:
        org = Organization()
        db.add(org)
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(org, k, v)
    db.commit()
    db.refresh(org)
    return ok(OrganizationResponse.model_validate(org).model_dump())


# ---------------- 能源类型 ----------------
@router.get("/energy-types", summary="能源类型列表")
def list_energy_types(
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
    keyword: str = Query(""), is_active: bool = Query(None),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    q = db.query(EnergyType)
    if keyword:
        q = q.filter(EnergyType.name.ilike(f"%{keyword}%"))
    if is_active is not None:
        q = q.filter(EnergyType.is_active == is_active)
    total, items = _paginate(q.order_by(EnergyType.sort_order, EnergyType.id), page, page_size)
    return page_resp([EnergyTypeResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/energy-types", summary="新增能源类型")
def create_energy_type(req: EnergyTypeCreate, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    if db.query(EnergyType).filter(EnergyType.code == req.code).first():
        return fail("编码已存在")
    obj = EnergyType(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(EnergyTypeResponse.model_validate(obj).model_dump())


@router.put("/energy-types/{oid}", summary="修改能源类型")
def update_energy_type(oid: int, req: EnergyTypeUpdate, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    obj = db.query(EnergyType).filter(EnergyType.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(EnergyTypeResponse.model_validate(obj).model_dump())


@router.delete("/energy-types/{oid}", summary="删除能源类型")
def delete_energy_type(oid: int, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    obj = db.query(EnergyType).filter(EnergyType.id == oid).first()
    if not obj:
        return fail("记录不存在")
    if db.query(Meter).filter(Meter.energy_type_id == oid).first() \
       or db.query(ManualEntry).filter(ManualEntry.energy_type_id == oid).first() \
       or db.query(EfficiencyIndicator).filter(EfficiencyIndicator.energy_type_id == oid).first() \
       or db.query(EnergyBudget).filter(EnergyBudget.energy_type_id == oid).first():
        return fail("该能源类型已被表计/录入/能效指标/预算引用，无法删除")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 用能单元 ----------------
@router.get("/energy-units", summary="用能单元列表")
def list_energy_units(
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
    keyword: str = Query(""), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(EnergyUnit)
    if keyword:
        q = q.filter(EnergyUnit.name.ilike(f"%{keyword}%"))
    total, items = _paginate(q.order_by(EnergyUnit.sort_order, EnergyUnit.id), page, page_size)
    return page_resp([EnergyUnitResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/energy-units", summary="新增用能单元")
def create_energy_unit(req: EnergyUnitCreate, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    if db.query(EnergyUnit).filter(EnergyUnit.code == req.code).first():
        return fail("编码已存在")
    obj = EnergyUnit(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(EnergyUnitResponse.model_validate(obj).model_dump())


@router.put("/energy-units/{oid}", summary="修改用能单元")
def update_energy_unit(oid: int, req: EnergyUnitUpdate, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    obj = db.query(EnergyUnit).filter(EnergyUnit.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(EnergyUnitResponse.model_validate(obj).model_dump())


@router.delete("/energy-units/{oid}", summary="删除用能单元")
def delete_energy_unit(oid: int, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    obj = db.query(EnergyUnit).filter(EnergyUnit.id == oid).first()
    if not obj:
        return fail("记录不存在")
    if db.query(Meter).filter(Meter.unit_id == oid).first() \
       or db.query(ManualEntry).filter(ManualEntry.unit_id == oid).first() \
       or db.query(ProductionData).filter(ProductionData.unit_id == oid).first() \
       or db.query(EnergyBudget).filter(EnergyBudget.unit_id == oid).first() \
       or db.query(CarbonBudget).filter(CarbonBudget.unit_id == oid).first():
        return fail("该用能单元已被业务数据引用，无法删除")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 表计 ----------------
@router.get("/meters", summary="表计列表")
def list_meters(
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
    keyword: str = Query(""), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Meter)
    if keyword:
        q = q.filter(Meter.name.ilike(f"%{keyword}%"))
    total, items = _paginate(q.order_by(Meter.id), page, page_size)
    return page_resp([MeterResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/meters", summary="新增表计")
def create_meter(req: MeterCreate, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    if db.query(Meter).filter(Meter.code == req.code).first():
        return fail("编码已存在")
    obj = Meter(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(MeterResponse.model_validate(obj).model_dump())


@router.put("/meters/{oid}", summary="修改表计")
def update_meter(oid: int, req: MeterUpdate, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    obj = db.query(Meter).filter(Meter.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(MeterResponse.model_validate(obj).model_dump())


@router.delete("/meters/{oid}", summary="删除表计")
def delete_meter(oid: int, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    obj = db.query(Meter).filter(Meter.id == oid).first()
    if not obj:
        return fail("记录不存在")
    if db.query(MeterReading).filter(MeterReading.meter_id == oid).first() \
       or db.query(ManualEntry).filter(ManualEntry.meter_id == oid).first():
        return fail("该表计已有读数或录入记录，无法删除")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 产品 ----------------
@router.get("/products", summary="产品列表")
def list_products(
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
    keyword: str = Query(""), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Product)
    if keyword:
        q = q.filter(Product.name.ilike(f"%{keyword}%"))
    total, items = _paginate(q.order_by(Product.sort_order, Product.id), page, page_size)
    return page_resp([ProductResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/products", summary="新增产品")
def create_product(req: ProductCreate, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    if db.query(Product).filter(Product.code == req.code).first():
        return fail("编码已存在")
    obj = Product(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(ProductResponse.model_validate(obj).model_dump())


@router.put("/products/{oid}", summary="修改产品")
def update_product(oid: int, req: ProductUpdate, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    obj = db.query(Product).filter(Product.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(ProductResponse.model_validate(obj).model_dump())


@router.delete("/products/{oid}", summary="删除产品")
def delete_product(oid: int, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    obj = db.query(Product).filter(Product.id == oid).first()
    if not obj:
        return fail("记录不存在")
    if db.query(ProductionData).filter(ProductionData.product_id == oid).first() \
       or db.query(ProductFootprint).filter(ProductFootprint.product_id == oid).first():
        return fail("该产品已被生产数据/碳足迹引用，无法删除")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 排放源 ----------------
@router.get("/emission-sources", summary="排放源列表")
def list_emission_sources(
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
    scope: str = Query(""), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(EmissionSource)
    if scope:
        q = q.filter(EmissionSource.scope == scope)
    total, items = _paginate(q.order_by(EmissionSource.sort_order, EmissionSource.id), page, page_size)
    return page_resp([EmissionSourceResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/emission-sources", summary="新增排放源")
def create_emission_source(req: EmissionSourceCreate, db: Session = Depends(get_db),
                           current_user=Depends(get_current_user)):
    if db.query(EmissionSource).filter(EmissionSource.code == req.code).first():
        return fail("编码已存在")
    obj = EmissionSource(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(EmissionSourceResponse.model_validate(obj).model_dump())


@router.put("/emission-sources/{oid}", summary="修改排放源")
def update_emission_source(oid: int, req: EmissionSourceUpdate, db: Session = Depends(get_db),
                           current_user=Depends(get_current_user)):
    obj = db.query(EmissionSource).filter(EmissionSource.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(EmissionSourceResponse.model_validate(obj).model_dump())


@router.delete("/emission-sources/{oid}", summary="删除排放源")
def delete_emission_source(oid: int, db: Session = Depends(get_db),
                           current_user=Depends(get_current_user)):
    obj = db.query(EmissionSource).filter(EmissionSource.id == oid).first()
    if not obj:
        return fail("记录不存在")
    if db.query(CarbonAccounting).filter(CarbonAccounting.source_id == oid).first():
        return fail("该排放源已有关联核算记录，无法删除")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 碳排放因子 ----------------
@router.get("/carbon-factors", summary="碳排放因子列表")
def list_carbon_factors(
    page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
    keyword: str = Query(""), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(CarbonFactor)
    if keyword:
        q = q.filter(CarbonFactor.name.ilike(f"%{keyword}%"))
    total, items = _paginate(q.order_by(CarbonFactor.sort_order, CarbonFactor.id), page, page_size)
    return page_resp([CarbonFactorResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@router.post("/carbon-factors", summary="新增碳排放因子")
def create_carbon_factor(req: CarbonFactorCreate, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    obj = CarbonFactor(**req.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return ok(CarbonFactorResponse.model_validate(obj).model_dump())


@router.put("/carbon-factors/{oid}", summary="修改碳排放因子")
def update_carbon_factor(oid: int, req: CarbonFactorUpdate, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    obj = db.query(CarbonFactor).filter(CarbonFactor.id == oid).first()
    if not obj:
        return fail("记录不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return ok(CarbonFactorResponse.model_validate(obj).model_dump())


@router.delete("/carbon-factors/{oid}", summary="删除碳排放因子")
def delete_carbon_factor(oid: int, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    obj = db.query(CarbonFactor).filter(CarbonFactor.id == oid).first()
    if not obj:
        return fail("记录不存在")
    if db.query(EmissionSource).filter(EmissionSource.carbon_factor_id == oid).first():
        return fail("该因子已被排放源引用，无法删除")
    db.delete(obj); db.commit()
    return ok(message="已删除")


# ---------------- 操作日志 ----------------
@router.get("/logs", summary="操作日志列表")
def list_logs(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    module: str = Query(""), db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(OperationLog)
    if module:
        q = q.filter(OperationLog.module == module)
    total, items = _paginate(q.order_by(OperationLog.id.desc()), page, page_size)
    return page_resp([OperationLogResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


# ---------------- 系统配置 ----------------
@router.get("/configs", summary="系统配置列表")
def list_configs(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(SystemConfig).order_by(SystemConfig.id).all()
    return ok([SystemConfigResponse.model_validate(i).model_dump() for i in items])


@router.post("/configs", summary="新增/更新配置")
def upsert_config(req: SystemConfigCreate, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    obj = db.query(SystemConfig).filter(SystemConfig.config_key == req.config_key).first()
    if obj:
        obj.config_value = req.config_value
        obj.config_group = req.config_group
        obj.description = req.description
    else:
        obj = SystemConfig(**req.model_dump())
        db.add(obj)
    db.commit(); db.refresh(obj)
    return ok(SystemConfigResponse.model_validate(obj).model_dump())
