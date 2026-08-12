set -euo pipefail

project_root="$(cd "$(dirname "$0")/../.." && pwd)"
meta_path="$project_root/packaging/app.json"
version="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['version'])")"
product_name="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['product_name'])")"
bundle_id="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['bundle_id'])")"

app_path="$project_root/dist_macos/${product_name}.app"
stage="$project_root/dist_macos_pkgroot"
rm -rf "$stage"
mkdir -p "$stage/Applications"
cp -R "$app_path" "$stage/Applications/"

out_dir="$project_root/dist_installers/macos"
mkdir -p "$out_dir"

pkg_path="$out_dir/${product_name}-${version}.pkg"
rm -f "$pkg_path"

pkgbuild \
  --root "$stage" \
  --identifier "$bundle_id" \
  --version "$version" \
  --install-location "/" \
  "$pkg_path"

printf "%s\n" "$pkg_path"
