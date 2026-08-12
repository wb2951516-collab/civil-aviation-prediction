import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SpringFestivalResult:
    date: datetime
    source: str


def _parse_ymd(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except Exception:
        return None


def get_spring_festival_date(year: int, spring_festival_dates: Dict[str, str]) -> SpringFestivalResult:
    key = str(int(year))
    if key in spring_festival_dates:
        parsed = _parse_ymd(spring_festival_dates[key])
        if parsed is not None:
            return SpringFestivalResult(parsed, "config")

    try:
        from zhdate import ZhDate  # type: ignore

        d = ZhDate(year, 1, 1).to_datetime()
        return SpringFestivalResult(datetime(d.year, d.month, d.day), "zhdate")
    except Exception:
        pass

    base_year = 2025
    base = _parse_ymd(spring_festival_dates.get(str(base_year), "2025-01-29")) or datetime(2025, 1, 29)
    year_diff = year - base_year
    estimated_date = base + timedelta(days=year_diff * 11)
    return SpringFestivalResult(estimated_date, "estimated")


def compute_spring_travel_span(
    year: int,
    spring_festival_dates: Dict[str, str],
    before_days: int,
    after_days: int,
) -> Tuple[datetime, datetime, SpringFestivalResult]:
    sf = get_spring_festival_date(year, spring_festival_dates)
    start = sf.date - timedelta(days=int(before_days))
    end = sf.date + timedelta(days=int(after_days))
    return start, end, sf


def compute_month_spring_travel_days(
    year: int,
    month: int,
    spring_festival_dates: Dict[str, str],
    before_days: int,
    after_days: int,
) -> int:
    start, end, _ = compute_spring_travel_span(year, spring_festival_dates, before_days, after_days)
    days_in_month = calendar.monthrange(year, month)[1]
    spring_days = 0
    for day in range(1, days_in_month + 1):
        current_date = datetime(year, month, day)
        if start <= current_date <= end:
            spring_days += 1
    return spring_days


def compute_month_spring_effect(
    year: int,
    month: int,
    spring_festival_dates: Dict[str, str],
    before_days: int,
    after_days: int,
    spring_effect: float,
    months_in_scope: List[int],
) -> float:
    if month not in months_in_scope:
        return 1.0
    spring_days = compute_month_spring_travel_days(year, month, spring_festival_dates, before_days, after_days)
    if spring_days == 0:
        return 1.0
    days_in_month = calendar.monthrange(year, month)[1]
    return 1.0 + (spring_days / days_in_month) * (float(spring_effect) - 1.0)


def compute_holiday_effect(year: int, month: int, holiday_cfg: Dict[str, Any], spring_festival_dates: Dict[str, str]) -> float:
    if not holiday_cfg.get("enabled", True):
        return 1.0

    effect = 1.0

    months_in_scope = holiday_cfg.get("spring_travel_months", [1, 2, 3])
    if not isinstance(months_in_scope, list):
        months_in_scope = [1, 2, 3]
    months_in_scope = [int(m) for m in months_in_scope]

    before_days = int(holiday_cfg.get("spring_travel_before_days", 15))
    after_days = int(holiday_cfg.get("spring_travel_after_days", 24))
    spring_festival_effect = float(holiday_cfg.get("spring_festival_effect", 1.15))

    if month in months_in_scope:
        effect *= compute_month_spring_effect(
            year=year,
            month=month,
            spring_festival_dates=spring_festival_dates,
            before_days=before_days,
            after_days=after_days,
            spring_effect=spring_festival_effect,
            months_in_scope=months_in_scope,
        )

    if month in [7, 8]:
        effect *= float(holiday_cfg.get("summer_vacation_effect", 1.10))
    elif month == 5:
        effect *= float(holiday_cfg.get("may_day_effect", 1.05))
    elif month == 10:
        effect *= float(holiday_cfg.get("national_day_effect", 1.08))

    if month in [11, 12]:
        effect *= float(holiday_cfg.get("winter_peak_effect", 1.03))

    return float(effect)


def apply_holiday_effects(
    forecast,
    holiday_cfg: Dict[str, Any],
    spring_festival_dates: Dict[str, str],
) -> Tuple[Any, Dict[str, Any]]:
    if not holiday_cfg.get("enabled", True):
        return forecast, {}

    adjusted = forecast.copy()
    spring_info: Dict[str, Any] = {}

    months_in_scope = holiday_cfg.get("spring_travel_months", [1, 2, 3])
    if not isinstance(months_in_scope, list):
        months_in_scope = [1, 2, 3]
    months_in_scope = [int(m) for m in months_in_scope]

    before_days = int(holiday_cfg.get("spring_travel_before_days", 15))
    after_days = int(holiday_cfg.get("spring_travel_after_days", 24))

    for i, date in enumerate(forecast.index):
        year = int(date.year)
        month = int(date.month)
        effect = compute_holiday_effect(year, month, holiday_cfg, spring_festival_dates)
        adjusted.iloc[i] = adjusted.iloc[i] * effect

        if month in months_in_scope:
            spring_days = compute_month_spring_travel_days(year, month, spring_festival_dates, before_days, after_days)
            if spring_days > 0:
                sf = get_spring_festival_date(year, spring_festival_dates)
                start, end, _ = compute_spring_travel_span(year, spring_festival_dates, before_days, after_days)
                spring_info[f"{year}-{month:02d}"] = {
                    "春运天数": spring_days,
                    "效应系数": effect,
                    "春节日期": sf.date.strftime("%Y-%m-%d"),
                    "春节来源": sf.source,
                    "春运开始": start.strftime("%Y-%m-%d"),
                    "春运结束": end.strftime("%Y-%m-%d"),
                }

    return adjusted, spring_info


# ============================================================
# 干预模型外生变量构造 (V2 干预引擎, 替代后处理乘法效应)
# 融入来源: V1.1.1 分支 (capm/holiday.py build_intervention_exog)
# ============================================================
def build_intervention_exog(
    index,
    spring_festival_dates: Dict[str, str],
    holiday_cfg: Optional[Dict[str, Any]] = None,
    include_covid: bool = True,
    exog_data: Any = None,
) -> Any:
    """构造 SARIMAX 外生变量, 用于干预建模替代后处理假日乘法效应。

    外生变量:
      - sf: 春节窗口(春节±7天覆盖的月份=1, 否则0) —— 解决移动节假日双重叠加
      - nd: 国庆窗口(10月=1, 9月=0.3, 其他0)
      - summer: 暑期(7/8月=1)
      - covid_step: 2020.03起=1 (永久水平下移, Box-Tiao阶跃干预)
      - covid_recovery: 2023.01起线性增长至1 (恢复斜坡干预)
      - ask/gdp: 若 exog_data 提供则追加

    依据: Monsell(2007) 移动节假日须独立建模; Box&Tiao(1975) 干预分析;
    Hyndman&Rostami-Tabar(2025) COVID 显式建模优于剔除/插值。
    """
    import pandas as pd

    holiday_cfg = holiday_cfg or {}
    holiday_enabled = bool(holiday_cfg.get("enabled", True))

    sf_col, nd_col, summer_col = [], [], []
    covid_step_col, covid_recovery_col = [], []

    for d in pd.to_datetime(index):
        y, m = int(d.year), int(d.month)
        # 春节窗口: 春节±7天覆盖该月则为1
        sf_hit = 0.0
        if holiday_enabled:
            try:
                sf = get_spring_festival_date(y, spring_festival_dates).date
                win_start = sf - timedelta(days=7)
                win_end = sf + timedelta(days=7)
                month_start = datetime(y, m, 1)
                days_in_m = calendar.monthrange(y, m)[1]
                month_end = month_start + timedelta(days=days_in_m - 1)
                if win_end >= month_start and win_start <= month_end:
                    sf_hit = 1.0
            except Exception:
                sf_hit = 0.0
        # 国庆窗口
        nd_hit = 1.0 if m == 10 else (0.3 if m == 9 else 0.0)
        if not holiday_enabled:
            nd_hit = 0.0
        # 暑期
        summer_hit = 1.0 if m in (7, 8) else 0.0
        if not holiday_enabled:
            summer_hit = 0.0
        # COVID干预
        cs = 1.0 if d >= pd.Timestamp("2020-03-01") else 0.0
        if d >= pd.Timestamp("2023-01-01"):
            months_since = (y - 2023) * 12 + m - 1
            cr = min(1.0, months_since / 24.0)
        else:
            cr = 0.0
        if not include_covid:
            cs = 0.0
            cr = 0.0

        sf_col.append(sf_hit)
        nd_col.append(nd_hit)
        summer_col.append(summer_hit)
        covid_step_col.append(cs)
        covid_recovery_col.append(cr)

    df = pd.DataFrame(
        {"sf": sf_col, "nd": nd_col, "summer": summer_col,
         "covid_step": covid_step_col, "covid_recovery": covid_recovery_col},
        index=pd.to_datetime(index),
    )

    # 追加 ASK/GDP 外生变量
    if exog_data is not None:
        try:
            exog_aligned = exog_data.reindex(df.index) if hasattr(exog_data, "reindex") else None
            if exog_aligned is not None:
                for col in ("ask", "gdp"):
                    if col in exog_aligned.columns:
                        df[col] = exog_aligned[col].astype(float)
        except Exception:
            pass

    return df

