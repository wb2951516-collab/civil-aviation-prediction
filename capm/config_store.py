import os
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from capm.app_paths import AppPaths


def _default_spring_festival_dates() -> Dict[str, str]:
    return {
        "2000": "2000-02-05",
        "2001": "2001-01-24",
        "2002": "2002-02-12",
        "2003": "2003-02-01",
        "2004": "2004-01-22",
        "2005": "2005-02-09",
        "2006": "2006-01-29",
        "2007": "2007-02-18",
        "2008": "2008-02-07",
        "2009": "2009-01-26",
        "2010": "2010-02-14",
        "2011": "2011-02-03",
        "2012": "2012-01-23",
        "2013": "2013-02-10",
        "2014": "2014-01-31",
        "2015": "2015-02-19",
        "2016": "2016-02-08",
        "2017": "2017-01-28",
        "2018": "2018-02-16",
        "2019": "2019-02-05",
        "2020": "2020-01-25",
        "2021": "2021-02-12",
        "2022": "2022-02-01",
        "2023": "2023-01-22",
        "2024": "2024-02-10",
        "2025": "2025-01-29",
        "2026": "2026-02-17",
        "2027": "2027-02-06",
        "2028": "2028-01-26",
        "2029": "2029-02-13",
        "2030": "2030-02-03",
    }


def default_config() -> Dict[str, Any]:
    return {
        "version": 1,
        "active_profile": "default",
        "profiles": {
            "default": {
                "holiday": {
                    "enabled": True,
                    "spring_festival_effect": 1.15,
                    "spring_travel_before_days": 15,
                    "spring_travel_after_days": 24,
                    "spring_travel_months": [1, 2, 3],
                    "summer_vacation_effect": 1.10,
                    "may_day_effect": 1.05,
                    "national_day_effect": 1.08,
                    "winter_peak_effect": 1.03,
                },
                "growth": {"annual_growth_rate": 0.027},
                "model": {
                    "weight_mode": "manual",
                    "weights": {"hw": 0.4, "sarima": 0.3, "linear": 0.3},
                    "sarima": {
                        "auto_tune": False,
                        "order": [1, 1, 1],
                        "seasonal_order": [1, 1, 1, 12],
                    },
                    "holt_winters": {
                        "trend": "add",
                        "seasonal": "add",
                        "seasonal_periods": 12,
                        "auto_tune": False,
                    },
                },
                "spring_festival_dates": _default_spring_festival_dates(),
            }
        },
    }


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = _deep_merge(dict(base[k]), v)
        else:
            base[k] = v
    return base


@dataclass
class ConfigStore:
    paths: AppPaths = AppPaths()
    cache: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        if self.cache is not None:
            return self.cache

        cfg = default_config()
        path = self.paths.config_path()
        if not path or not isinstance(path, str):
            self.cache = cfg
            return cfg

        if not os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            self.cache = cfg
            return cfg

        try:
            with open(path, "r", encoding="utf-8") as f:
                disk = json.load(f)
            if isinstance(disk, dict):
                cfg = _deep_merge(cfg, disk)
        except Exception:
            pass

        self.cache = cfg
        return cfg

    def save(self, cfg: Dict[str, Any]) -> Tuple[bool, str]:
        path = self.paths.config_path()
        try:
            cfg = dict(cfg)
            cfg["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.cache = cfg
            return True, path
        except Exception as e:
            return False, str(e)

    def get_active_profile(self) -> Dict[str, Any]:
        cfg = self.load()
        active_name = cfg.get("active_profile", "default")
        profiles = cfg.get("profiles", {})
        profile = profiles.get(active_name) if isinstance(profiles, dict) else None
        if not isinstance(profile, dict):
            profile = default_config()["profiles"]["default"]
        return profile

    def set_active_profile(self, name: str) -> None:
        cfg = self.load()
        if "profiles" not in cfg or not isinstance(cfg["profiles"], dict):
            cfg["profiles"] = {}
        if name not in cfg["profiles"]:
            return
        cfg["active_profile"] = name
        self.cache = cfg

    def upsert_profile(self, name: str, profile: Dict[str, Any]) -> None:
        cfg = self.load()
        if "profiles" not in cfg or not isinstance(cfg["profiles"], dict):
            cfg["profiles"] = {}
        cfg["profiles"][name] = profile
        self.cache = cfg

    def delete_profile(self, name: str) -> bool:
        cfg = self.load()
        profiles = cfg.get("profiles", {})
        if not isinstance(profiles, dict) or name not in profiles:
            return False
        if len(profiles) <= 1:
            return False
        del profiles[name]
        if cfg.get("active_profile") == name:
            cfg["active_profile"] = next(iter(profiles.keys()))
        self.cache = cfg
        return True

