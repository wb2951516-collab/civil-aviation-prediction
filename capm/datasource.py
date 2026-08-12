"""外部宏观与行业数据源接入模块（GDP / ASK 可用座公里）

职责：
1. 通过 akshare 从官方公开渠道自动抓取 GDP（国家统计局）与民航行业指标数据；
2. 网络不可用或接口变动时，自动降级为内置参考数据（基于官方公开统计整理）；
3. 本地缓存 + 统一对外接口（月度对齐），供预测算法作为外生变量参与计算。

使用示例：
    from capm.datasource import ExternalDataManager
    mgr = ExternalDataManager()
    factors = mgr.get_monthly_factors(ts_index, periods=12)   # DataFrame[gdp, ask]
    status = mgr.refresh()                                     # 触发在线更新
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from capm.app_paths import AppPaths

logger = logging.getLogger(__name__)

# 内置参考数据（基于国家统计局 / 民航局公开统计整理的近似值，仅供离线兜底）
_ANNUAL_GDP_YI = {
    1992: 27195, 1993: 35673, 1994: 48637, 1995: 61340, 1996: 71814,
    1997: 79715, 1998: 85196, 1999: 90564, 2000: 100280, 2001: 110863,
    2002: 121717, 2003: 137422, 2004: 161840, 2005: 187319, 2006: 219439,
    2007: 270092, 2008: 319245, 2009: 349081, 2010: 413030, 2011: 489301,
    2012: 540367, 2013: 595244, 2014: 643974, 2015: 688858, 2016: 746395,
    2017: 832036, 2018: 919281, 2019: 986515, 2020: 1013567, 2021: 1149237,
    2022: 1210207, 2023: 1260582, 2024: 1349084, 2025: 1405000,
}
# 季度现价占比近似（中国季度 GDP 分布大致为 Q1~Q4 = 22%/25%/26%/27%）
_QUARTER_SHARE = {1: 0.22, 2: 0.25, 3: 0.26, 4: 0.27}

# 内置 ASK（可用座公里，亿座公里，2015-2025 月度近似，含季节性形态）
_ASK_ANNUAL_BASE = {
    2015: 8500, 2016: 9600, 2017: 10850, 2018: 12100, 2019: 13070,
    2020: 7200, 2021: 11050, 2022: 8400, 2023: 13050, 2024: 14100, 2025: 14950,
}
# 月度季节性系数（2 月春运、7-8 月暑期为高峰，1 月为低谷）
_ASK_MONTHLY_SHAPE = [0.90, 0.96, 0.94, 0.95, 0.97, 1.00, 1.12, 1.15, 1.02, 1.04, 0.98, 0.97]
_ASK_YOY_GROWTH = 0.045  # 未来外推年增速（保守假设）


def _builtin_gdp_frame() -> pd.DataFrame:
    """内置 GDP 参考数据（季度 → 月均，单位：亿元）"""
    rows: List[Dict[str, Any]] = []
    for year, total in sorted(_ANNUAL_GDP_YI.items()):
        for q, share in sorted(_QUARTER_SHARE.items()):
            q_value = total * share
            month_of_quarter = {1: 1, 2: 4, 3: 7, 4: 10}
            m = month_of_quarter[q]
            date = pd.Timestamp(year=year, month=m, day=1)
            rows.append({"date": date, "gdp": round(q_value / 3.0, 1)})
    df = pd.DataFrame(rows).set_index("date")
    return df["gdp"].to_frame()


def _builtin_ask_frame() -> pd.DataFrame:
    """内置 ASK 参考数据（月度，单位：亿座公里）"""
    rows: List[Dict[str, Any]] = []
    for year, total in sorted(_ASK_ANNUAL_BASE.items()):
        shape = _ASK_MONTHLY_SHAPE
        s = sum(shape)
        for m in range(1, 13):
            date = pd.Timestamp(year=year, month=m, day=1)
            rows.append({"date": date, "ask": round(total * shape[m - 1] / s, 1)})
    df = pd.DataFrame(rows).set_index("date")
    return df["ask"].to_frame()


def _parse_ak_gdp_date(value: str):
    """解析 akshare 季度行日期：'2026年第1季度' → 2026-01-01；累计行（如 '2026年1-2月'）返回 None 剔除。"""
    import re

    s = str(value).strip()
    m = re.match(r"(\d{4})年.*?([1-4])季度", s)
    if m:
        year, q = int(m.group(1)), int(m.group(2))
        month = {1: 1, 2: 4, 3: 7, 4: 10}[q]
        return pd.Timestamp(year=year, month=month, day=1)
    if re.match(r"\d{4}年\d{1,2}-\d{1,2}月", s):
        return None  # 累计口径行，剔除避免混入
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return None


def _fetch_gdp_akshare() -> Optional[pd.DataFrame]:
    """通过 akshare 抓取国家统计局季度 GDP（当季绝对值，亿元）"""
    try:
        import akshare as ak

        raw = ak.macro_china_gdp()
        if raw is None or raw.empty:
            return None
        df = raw.copy()
        # 兼容不同版本列名
        date_col = next((c for c in df.columns if "季度" in str(c)), None)
        val_col = next(
            (c for c in df.columns if "国内生产总值-绝对值" in str(c) or "国内生产总值" in str(c)),
            None,
        )
        if date_col is None or val_col is None:
            return None
        dates = [_parse_ak_gdp_date(v) for v in df[date_col]]
        out = pd.DataFrame({"date": dates, "gdp": pd.to_numeric(df[val_col], errors="coerce")})
        out = out.dropna().sort_values("date")
        if out.empty:
            return None
        # 季度值 → 月均（与内置口径一致）
        out["month_start"] = out["date"].dt.year * 100 + out["date"].dt.month
        out = out.drop_duplicates(subset=["month_start"], keep="last").set_index("date")
        out["gdp"] = (out["gdp"] / 3.0).round(1)
        return out[["gdp"]]
    except Exception as e:
        logger.warning("akshare 抓取 GDP 失败: %s", e)
        return None


def _fetch_ask_akshare() -> Optional[pd.DataFrame]:
    """尝试通过 akshare 抓取民航行业指标（ASK 无直接公开接口时返回 None）"""
    try:
        import akshare as ak

        # 动态探测 akshare 中可能存在的民航/航空运力相关接口
        candidates = [n for n in dir(ak) if any(k in n.lower() for k in ("caac", "airline", "aviation", "air_trans"))]
        for name in candidates[:6]:
            try:
                fn = getattr(ak, name)
                raw = fn()
                if raw is None or not hasattr(raw, "empty") or raw.empty:
                    continue
                cols = [str(c) for c in raw.columns]
                date_col = next((c for c in cols if any(k in c for k in ("日期", "时间", "月份", "统计期"))), None)
                ask_col = next((c for c in cols if any(k in c for k in ("可用座公里", "座公里", "ASK", "ask"))), None)
                if date_col is None or ask_col is None:
                    continue
                df = pd.DataFrame()
                df["date"] = pd.to_datetime(raw[date_col], errors="coerce")
                df["ask"] = pd.to_numeric(raw[ask_col], errors="coerce")
                df = df.dropna().sort_values("date")
                if len(df) >= 12:
                    return df.set_index("date")[["ask"]]
            except Exception:
                continue
        return None
    except Exception as e:
        logger.warning("akshare 抓取 ASK 失败: %s", e)
        return None


class ExternalDataManager:
    """外部数据源管理器：抓取 → 缓存 → 月度对齐输出"""

    def __init__(self, cache_dir: Optional[str] = None):
        try:
            self.cache_dir = cache_dir or os.path.join(AppPaths().ensure_data_dir(), "external")
        except Exception:
            self.cache_dir = cache_dir
        self._cache: Optional[Dict[str, pd.DataFrame]] = None
        self._last_refresh: Optional[datetime] = None
        self._source_flags: Dict[str, str] = {}

    # ---------- 缓存 ----------
    def _cache_file(self, name: str) -> str:
        if not self.cache_dir:
            return ""
        return os.path.join(self.cache_dir, name)

    def _save_cache(self):
        if not self.cache_dir:
            return
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            meta = {"refreshed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "sources": self._source_flags}
            with open(self._cache_file("meta.json"), "w", encoding="utf-8") as f:
                import json

                json.dump(meta, f, ensure_ascii=False, indent=2)
            for name in ("gdp", "ask"):
                df = self._cache.get(name) if self._cache else None
                if df is not None and len(df):
                    df.to_csv(self._cache_file(f"{name}.csv"), encoding="utf-8-sig")
        except Exception as e:
            logger.warning("外部数据缓存保存失败: %s", e)

    def _load_cache(self) -> bool:
        if not self.cache_dir or not os.path.isdir(self.cache_dir):
            return False
        try:
            meta_path = self._cache_file("meta.json")
            if not os.path.exists(meta_path):
                return False
            with open(meta_path, "r", encoding="utf-8") as f:
                import json

                meta = json.load(f)
            self._source_flags = dict(meta.get("sources", {}))
            self._last_refresh = datetime.strptime(meta.get("refreshed_at", ""), "%Y-%m-%d %H:%M:%S") if meta.get("refreshed_at") else None
            gdp_path, ask_path = self._cache_file("gdp.csv"), self._cache_file("ask.csv")
            if not (os.path.exists(gdp_path) and os.path.exists(ask_path)):
                return False
            gdp = pd.read_csv(gdp_path, index_col=0, parse_dates=True)
            ask = pd.read_csv(ask_path, index_col=0, parse_dates=True)
            self._cache = {"gdp": gdp, "ask": ask}
            return True
        except Exception as e:
            logger.warning("外部数据缓存读取失败: %s", e)
            return False

    def clear_cache(self) -> None:
        """清空本地外部数据缓存"""
        self._cache = None
        self._last_refresh = None
        self._source_flags = {}
        if self.cache_dir and os.path.isdir(self.cache_dir):
            for f in os.listdir(self.cache_dir):
                try:
                    os.remove(os.path.join(self.cache_dir, f))
                except Exception:
                    pass

    # ---------- 数据加载 ----------
    def load(self) -> Dict[str, pd.DataFrame]:
        """返回 {"gdp": DataFrame, "ask": DataFrame}，优先缓存，其次内置"""
        if self._cache is not None:
            return self._cache
        if not self._load_cache():
            self._cache = {"gdp": _builtin_gdp_frame(), "ask": _builtin_ask_frame()}
            self._source_flags = {"gdp": "内置参考数据", "ask": "内置参考数据"}
        return self._cache

    def refresh(self, use_akshare: bool = True) -> Dict[str, Any]:
        """在线更新数据。返回更新状态摘要。"""
        builtin = {"gdp": _builtin_gdp_frame(), "ask": _builtin_ask_frame()}
        if use_akshare:
            gdp = _fetch_gdp_akshare()
            ask = _fetch_ask_akshare()
        else:
            gdp = ask = None

        self._cache = {
            "gdp": gdp if gdp is not None else builtin["gdp"],
            "ask": ask if ask is not None else builtin["ask"],
        }
        self._source_flags = {
            "gdp": "国家统计局(akshare)" if gdp is not None else "内置参考数据",
            "ask": "akshare民航接口" if ask is not None else "内置参考数据",
        }
        self._last_refresh = datetime.now()
        self._save_cache()
        return {
            "gdp_ok": gdp is not None,
            "ask_ok": ask is not None,
            "gdp_source": self._source_flags["gdp"],
            "ask_source": self._source_flags["ask"],
            "refreshed_at": self._last_refresh.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ---------- 对外接口 ----------
    def get_monthly_factors(self, ts_index: pd.DatetimeIndex, periods: int = 12) -> pd.DataFrame:
        """返回与 ts_index 对齐 + 未来 periods 个月的月度因子 DataFrame[gdp, ask]。

        训练期部分优先使用实际/缓存数据，缺失月份用插值补齐；
        未来部分按最近增速保守外推。
        """
        data = self.load()
        gdp = data["gdp"]["gdp"].copy()
        ask = data["ask"]["ask"].copy()

        # 训练期：按月索引 reindex + 前向填充兜底
        hist_idx = pd.DatetimeIndex(ts_index)
        gdp_hist = gdp.reindex(hist_idx).interpolate(method="time").ffill().bfill()
        ask_hist = ask.reindex(hist_idx).interpolate(method="time").ffill().bfill()

        # 未来月份索引
        if len(hist_idx) > 0:
            future_start = (hist_idx[-1].to_period("M") + 1).to_timestamp()
        else:
            future_start = pd.Timestamp.today().to_period("M").to_timestamp()
        future_idx = pd.date_range(start=future_start, periods=int(periods), freq="MS")

        # 未来外推：GDP 按最近 12 个月 YoY 增速；ASK 按最近 12 个月 YoY 增速
        gdp_extrap = self._extrapolate(gdp_hist, future_idx)
        ask_extrap = self._extrapolate(ask_hist, future_idx)

        out = pd.concat([gdp_hist, gdp_extrap], axis=0)
        ask_out = pd.concat([ask_hist, ask_extrap], axis=0)
        factors = pd.DataFrame({"gdp": out, "ask": ask_out})
        factors = factors[~factors.index.duplicated(keep="first")].sort_index()
        return factors

    @staticmethod
    def _extrapolate(hist: pd.Series, future_idx: pd.DatetimeIndex) -> pd.Series:
        """按最近 12 个月同比增速外推（含季节性），数据不足时退化为水平外推"""
        if len(hist) < 12:
            last = float(hist.iloc[-1]) if len(hist) else 0.0
            return pd.Series([last] * len(future_idx), index=future_idx)
        # 逐月同比增速
        yoy = hist / hist.shift(12) - 1.0
        g = float(yoy.iloc[-12:].mean())
        if g != g or g < -0.5 or g > 0.5:
            g = 0.0
        last12 = hist.iloc[-12:].copy()
        last12.index = last12.index.to_period("M")
        future_periods = future_idx.to_period("M")
        base_periods = last12.index
        values = []
        for p in future_periods:
            m = p.month
            # 用历史同月的值 × (1+g)^年数 外推
            same_month = base_periods[base_periods.month == m]
            if len(same_month):
                base_val = float(last12.loc[same_month[-1]])
            else:
                base_val = float(last12.iloc[-1])
            years = max(1, int((p - same_month[-1]).n) // 12 + 1) if len(same_month) else 1
            values.append(base_val * (1.0 + g) ** years)
        return pd.Series(values, index=future_idx)

    # ---------- 状态 ----------
    def status(self) -> List[Dict[str, Any]]:
        """数据源状态（供管理控制台展示）"""
        data = self.load()
        rows = []
        for key, label in (("gdp", "GDP（亿元）"), ("ask", "ASK（亿座公里）")):
            df = data[key]
            ok = df is not None and len(df) > 0
            rows.append({
                "指标": label,
                "来源": self._source_flags.get(key, "内置参考数据"),
                "数据量": len(df) if ok else 0,
                "最新日期": str(df.index.max().strftime("%Y-%m")) if ok else "-",
                "最新值": float(df[key].iloc[-1]) if ok and len(df) else None,
                "更新时间": self._last_refresh.strftime("%Y-%m-%d %H:%M:%S") if self._last_refresh else "-",
                "状态": "正常" if ok else "异常",
            })
        return rows
