set -euo pipefail

# Linux 单文件二进制构建（PyInstaller 路线，CI 与本地通用）。
# 与 build_binary.sh（Nuitka onefile）二选一：本脚本构建速度快数倍。
# 产物：dist_linux/capm（供 build_deb.sh / build_rpm.sh 以 REUSE_BINARY=1 复用）

project_root="$(cd "$(dirname "$0")/../.." && pwd)"

cd "$project_root"
mkdir -p dist_linux

python3 -m PyInstaller \
  --name=capm_linux \
  --onefile \
  --add-data="assets:assets" \
  --hidden-import=zhdate \
  --collect-all=capm \
  --collect-all=pandas \
  --collect-all=scipy \
  --collect-all=statsmodels \
  --collect-all=numpy \
  --collect-all=akshare \
  --noconfirm --clean \
  CAPM.py

bin_path="$project_root/dist/capm_linux"
if [ ! -f "$bin_path" ]; then
  echo "Expected binary not found: $bin_path" >&2
  exit 1
fi
chmod +x "$bin_path"
cp "$bin_path" "$project_root/dist_linux/capm"

printf "%s\n" "$project_root/dist_linux/capm"
