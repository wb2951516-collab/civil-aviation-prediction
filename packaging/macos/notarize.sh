set -euo pipefail

project_root="$(cd "$(dirname "$0")/../.." && pwd)"
meta_path="$project_root/packaging/app.json"
version="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['version'])")"
product_name="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['product_name'])")"

apple_id="${APPLE_ID:?APPLE_ID is required}"
team_id="${APPLE_TEAM_ID:?APPLE_TEAM_ID is required}"
app_password="${APPLE_APP_PASSWORD:?APPLE_APP_PASSWORD is required}"

out_dir="$project_root/dist_installers/macos"
zip_path="$out_dir/${product_name}-${version}.zip"
app_path="$project_root/dist_macos/${product_name}.app"

rm -f "$zip_path"
ditto -c -k --sequesterRsrc --keepParent "$app_path" "$zip_path"

xcrun notarytool submit "$zip_path" --apple-id "$apple_id" --team-id "$team_id" --password "$app_password" --wait
xcrun stapler staple "$app_path"
printf "%s\n" "$app_path"
