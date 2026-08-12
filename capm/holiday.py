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

