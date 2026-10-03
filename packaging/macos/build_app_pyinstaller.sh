set -euo pipefail

# macOS .app + DMG 构建（PyInstaller 路线，CI 与本地通用）。
# 与 build_app.sh（Nuitka）二选一：本脚本构建速度快数倍，产物为未签名 DMG。
# 产物：dist_installers/macos/CAPM-<version>-macos-<arch>.dmg

project_root="$(cd "$(dirname "$0")/../.." && pwd)"
meta_path="$project_root/packaging/app.json"
version="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['version'])")"
product_name="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['product_name'])")"
arch="$(uname -m)"

cd "$project_root"

python3 -m PyInstaller \
  --name="$product_name" \
  --windowed \
  --icon="assets/airCAPM.icns" \
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

app_path="dist/${product_name}.app"
if [ ! -d "$app_path" ]; then
  echo "Expected app bundle not found: $app_path" >&2
  exit 1
fi

out_dir="$project_root/dist_installers/macos"
mkdir -p "$out_dir"
dmg_path="$out_dir/${product_name}-${version}-macos-${arch}.dmg"
rm -f "$dmg_path"

hdiutil create \
  -volname "$product_name" \
  -srcfolder "$app_path" \
  -ov \
  -format UDZO \
  "$dmg_path"

printf "%s\n" "$dmg_path"
