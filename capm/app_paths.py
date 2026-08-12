import os
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class AppPaths:
    app_name: str = "CAPM"
    legacy_app_name: str = "民航旅客运输量预测系统"

    def _base_dir(self) -> str:
        return os.environ.get("APPDATA") or os.path.expanduser("~")

    def data_dir(self) -> str:
        return os.path.join(self._base_dir(), self.app_name)

    def legacy_data_dir(self) -> str:
        return os.path.join(self._base_dir(), self.legacy_app_name)

    def ensure_data_dir(self) -> str:
        path = self.data_dir()
        legacy = self.legacy_data_dir()

        if not os.path.exists(path) and os.path.exists(legacy):
            try:
                os.replace(legacy, path)
                os.makedirs(path, exist_ok=True)
                return path
            except Exception:
                os.makedirs(path, exist_ok=True)
        else:
            os.makedirs(path, exist_ok=True)

        legacy_cfg = os.path.join(legacy, "config.json")
        new_cfg = os.path.join(path, "config.json")
        if os.path.exists(legacy_cfg) and not os.path.exists(new_cfg):
            try:
                shutil.copy2(legacy_cfg, new_cfg)
            except Exception:
                pass

        legacy_logs = os.path.join(legacy, "logs")
        new_logs = os.path.join(path, "logs")
        if os.path.isdir(legacy_logs) and not os.path.isdir(new_logs):
            try:
                shutil.copytree(legacy_logs, new_logs, dirs_exist_ok=True)
            except TypeError:
                try:
                    shutil.copytree(legacy_logs, new_logs)
                except Exception:
                    pass
            except Exception:
                pass

        return path

    def config_path(self) -> str:
        return os.path.join(self.ensure_data_dir(), "config.json")

    def logs_dir(self) -> str:
        return os.path.join(self.ensure_data_dir(), "logs")

    def ensure_logs_dir(self) -> str:
        path = self.logs_dir()
        os.makedirs(path, exist_ok=True)
        return path

    def log_path(self) -> str:
        return os.path.join(self.ensure_logs_dir(), "app.log")

