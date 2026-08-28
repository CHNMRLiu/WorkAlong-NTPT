"""数据库初始化与种子数据。

执行时机：FastAPI 启动时（main.py lifespan）会自动调用 init_db() 与 seed()。
也可单独运行：python init_db.py

种子数据说明（重要）：折标煤系数、碳排放因子均为**国家标准示例值**，来源已在注释标注，
上线前务必替换为最新官方发布值：
- 折标煤系数：GB/T 2589-2020《综合能耗计算通则》
- 电网排放因子：生态环境部公开数据（示例 0.5703 kgCO2/kWh，对应 0.5703 tCO2/MWh）
- 燃料碳排放因子：参考 IPCC / 省级温室气体清单指南
"""
from sqlalchemy import func

from app.database import Base, SessionLocal, engine
from app.models import (
    CarbonFactor,
    EmissionSource,
    EnergyType,
    Organization,
    User,
)
from app.utils.security import hash_password


def init_db(retries: int = 30, wait_seconds: float = 2.0):
    """创建全部表。容器启动时数据库可能尚未就绪，带连接重试。"""
    import time

    import app.models  # noqa: F401  导入模型包，确保表注册到 Base.metadata
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as exc:  # 数据库未就绪（连接拒绝等），等待后重试
            if attempt == retries:
                raise
            print(f"等待数据库就绪（{attempt}/{retries}）：{exc}")
            time.sleep(wait_seconds)


# 默认能源类型（示例值，单位与系数配套）
DEFAULT_ENERGY_TYPES = [
    # name, code, unit, 折标系数(kgce/单位), 碳因子(kgCO2/单位), 单价(元/单位), 是否外购电
    ("电力", "electricity", "kWh", 0.1229, 0.5703, 0.70, True),
    ("原煤", "raw_coal", "t", 714.3, 1900.0, 800.0, False),
    ("天然气", "natural_gas", "m3", 1.2143, 1.96, 3.20, False),
    ("汽油", "gasoline", "kg", 1.4714, 2.925, 8.00, False),
    ("柴油", "diesel", "kg", 1.4571, 3.095, 7.50, False),
    ("蒸汽", "steam", "t", 92.3, 100.0, 200.0, False),
    ("新水", "water", "t", 0.0857, 0.0, 4.50, False),
]

# 默认碳排放因子（用于碳核算/排放源，单位与活动数据配套）
DEFAULT_CARBON_FACTORS = [
    # name, factor_value, unit, source
    ("电网电力", 0.5703, "kgCO2/kWh", "生态环境部"),
    ("天然气燃烧", 1.96, "kgCO2/m3", "IPCC"),
    ("汽油燃烧", 2.925, "kgCO2/kg", "IPCC"),
    ("柴油燃烧", 3.095, "kgCO2/kg", "IPCC"),
    ("原煤燃烧", 1900.0, "kgCO2/t", "省级清单指南"),
    ("外购热力", 0.11, "tCO2/GJ", "生态环境部"),
]

# 默认排放源（scope: 范围1/范围2/范围3）
DEFAULT_EMISSION_SOURCES = [
    # code, name, scope, category, factor_index(对应 DEFAULT_CARBON_FACTORS)
    ("NG", "天然气燃烧", "范围1", "燃料燃烧", 1),
    ("GAS", "汽油燃烧", "范围1", "燃料燃烧", 2),
    ("DIE", "柴油燃烧", "范围1", "燃料燃烧", 3),
    ("COAL", "原煤燃烧", "范围1", "燃料燃烧", 4),
    ("EL", "外购电力", "范围2", "外购电力", 0),
    ("HEAT", "外购热力", "范围2", "外购热力", 5),
    ("UP", "上游运输", "范围3", "上游", None),
    ("DOWN", "下游产品使用", "范围3", "下游", None),
]


def seed():
    """写入默认基础数据（仅当表为空时）。"""
    db = SessionLocal()
    try:
        # 默认企业信息
        if db.query(Organization).count() == 0:
            db.add(Organization(
                name="示例企业（请修改）",
                credit_code="",
                industry="",
                address="",
                contact="",
                phone="",
                scale="",
            ))
            db.commit()

        # 管理员账号 admin/admin123
        if db.query(User).filter(User.username == "admin").count() == 0:
            db.add(User(
                username="admin",
                password_hash=hash_password("admin123"),
                name="系统管理员",
                role="admin",
                is_active=True,
            ))
            db.commit()

        # 默认能源类型
        if db.query(EnergyType).count() == 0:
            for name, code, unit, coef, cf, price, is_el in DEFAULT_ENERGY_TYPES:
                db.add(EnergyType(
                    name=name, code=code, unit=unit,
                    standard_coal_coefficient=coef,
                    carbon_factor=cf, default_price=price,
                    is_purchased_electricity=is_el,
                    is_active=True, sort_order=0,
                ))
            db.commit()

        # 默认碳排放因子
        if db.query(CarbonFactor).count() == 0:
            for name, fv, unit, source in DEFAULT_CARBON_FACTORS:
                db.add(CarbonFactor(
                    name=name, factor_value=fv, unit=unit,
                    source=source, is_active=True, sort_order=0,
                ))
            db.commit()

        # 默认排放源（关联碳因子）
        if db.query(EmissionSource).count() == 0:
            factors = db.query(CarbonFactor).order_by(CarbonFactor.id).all()
            for code, name, scope, category, fidx in DEFAULT_EMISSION_SOURCES:
                fid = factors[fidx].id if (fidx is not None and fidx < len(factors)) else None
                db.add(EmissionSource(
                    code=code, name=name, scope=scope, category=category,
                    carbon_factor_id=fid, is_active=True, sort_order=0,
                ))
            db.commit()

        print("数据库初始化与种子数据完成。")
    except Exception as e:
        db.rollback()
        print(f"种子数据写入异常：{e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed()
