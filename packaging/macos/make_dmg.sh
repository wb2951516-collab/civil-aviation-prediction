set -euo pipefail

project_root="$(cd "$(dirname "$0")/../.." && pwd)"
meta_path="$project_root/packaging/app.json"
version="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['version'])")"
product_name="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['product_name'])")"

app_path="$project_root/dist_macos/${product_name}.app"
out_dir="$project_root/dist_installers/macos"
mkdir -p "$out_dir"

dmg_path="$out_dir/${product_name}-${version}.dmg"
rm -f "$dmg_path"

hdiutil create \
  -volname "$product_name" \
  -srcfolder "$app_path" \
  -ov \
  -format UDZO \
  "$dmg_path"

printf "%s\n" "$dmg_path"
