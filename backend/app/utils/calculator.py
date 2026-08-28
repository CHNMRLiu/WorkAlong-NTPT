"""能碳计算工具函数 —— 所有计算逻辑统一放此处，禁止散落到接口中。

计算公式与参数来源（示例值，上线前须替换为最新官方发布值）：
- 折标煤：标准煤(kgce) = 消耗量 × 折标煤系数，系数来源 GB/T 2589-2020《综合能耗计算通则》
- 碳排放：碳排放(kgCO2e) = 消耗量 × 碳排放因子；外购电默认走范围2（电网因子）
- 电网排放因子示例值：0.5703 tCO2/MWh = 0.0005703 kgCO2/kWh（来源生态环境部公开数据，示例）
- 能效等级：按偏差率判定（见 judge_level）
"""
from decimal import Decimal

# 默认电网排放因子（kgCO2 / kWh），示例值 0.5703，来源生态环境部（对应 0.5703 tCO2/MWh），上线前替换
DEFAULT_GRID_FACTOR = Decimal("0.5703")


def calc_consumption(last_reading, current_reading) -> Decimal:
    """表计消耗量 = 本次读数 - 上次读数。"""
    if last_reading is None or current_reading is None:
        return Decimal("0")
    return Decimal(str(current_reading)) - Decimal(str(last_reading))


def calc_cost(consumption, unit_price) -> Decimal:
    """费用 = 消耗量 × 单价。"""
    c = Decimal(str(consumption)) if consumption is not None else Decimal("0")
    p = Decimal(str(unit_price)) if unit_price is not None else Decimal("0")
    return (c * p).quantize(Decimal("0.01"))


def calc_standard_coal(consumption, coef) -> Decimal:
    """折标煤 = 消耗量 × 折标煤系数。"""
    c = Decimal(str(consumption)) if consumption is not None else Decimal("0")
    k = Decimal(str(coef)) if coef is not None else Decimal("0")
    return (c * k).quantize(Decimal("0.0001"))


def calc_carbon(consumption, factor) -> Decimal:
    """碳排放 = 消耗量 × 碳排放因子。"""
    c = Decimal(str(consumption)) if consumption is not None else Decimal("0")
    f = Decimal(str(factor)) if factor is not None else Decimal("0")
    return (c * f).quantize(Decimal("0.000001"))


def calc_unit_energy(energy_consumption, output) -> Decimal:
    """单位产品能耗 = 总能耗 / 总产量。"""
    e = Decimal(str(energy_consumption)) if energy_consumption is not None else Decimal("0")
    o = Decimal(str(output)) if output else Decimal("0")
    if o == 0:
        return Decimal("0")
    return (e / o).quantize(Decimal("0.0001"))


def calc_deviation(actual, benchmark) -> Decimal:
    """偏差率(%) = (实际 - 基准) / 基准 × 100%。"""
    a = Decimal(str(actual)) if actual is not None else Decimal("0")
    b = Decimal(str(benchmark)) if benchmark else Decimal("0")
    if b == 0:
        return Decimal("0")
    return ((a - b) / b * 100).quantize(Decimal("0.01"))


def judge_level(deviation) -> str:
    """能效等级判定（偏差率 < -10% 领先；-10%~0 先进；0~20% 合格；≥20% 落后）。"""
    d = Decimal(str(deviation)) if deviation is not None else Decimal("0")
    if d < Decimal("-10"):
        return "领先"
    elif d < Decimal("0"):
        return "先进"
    elif d < Decimal("20"):
        return "合格"
    else:
        return "落后"


def calc_budget_value(unit_consumption, planned_output) -> Decimal:
    """用能预算量 = 产品单耗 × 计划产量。"""
    u = Decimal(str(unit_consumption)) if unit_consumption is not None else Decimal("0")
    p = Decimal(str(planned_output)) if planned_output is not None else Decimal("0")
    return (u * p).quantize(Decimal("0.0001"))


def calc_budget_carbon(carbon_intensity, planned_output) -> Decimal:
    """碳排放预算 = 碳排放强度 × 计划产量(或产值)。"""
    i = Decimal(str(carbon_intensity)) if carbon_intensity is not None else Decimal("0")
    p = Decimal(str(planned_output)) if planned_output is not None else Decimal("0")
    return (i * p).quantize(Decimal("0.000001"))


def calc_execution_rate(actual, budget) -> Decimal:
    """执行率(%) = 实际 / 预算 × 100%。"""
    a = Decimal(str(actual)) if actual is not None else Decimal("0")
    b = Decimal(str(budget)) if budget else Decimal("0")
    if b == 0:
        return Decimal("0")
    return (a / b * 100).quantize(Decimal("0.01"))


def calc_emission_from_factor(quantity, factor) -> Decimal:
    """供应商/通用：排放量 = 数量 × 排放因子。"""
    q = Decimal(str(quantity)) if quantity is not None else Decimal("0")
    f = Decimal(str(factor)) if factor is not None else Decimal("0")
    return (q * f).quantize(Decimal("0.000001"))


def calc_total_footprint(raw, prod, trans, use, disposal) -> Decimal:
    """产品碳足迹合计 = 原料+生产+运输+使用+废弃。"""
    parts = [raw, prod, trans, use, disposal]
    total = Decimal("0")
    for p in parts:
        total += Decimal(str(p)) if p is not None else Decimal("0")
    return total.quantize(Decimal("0.000001"))
