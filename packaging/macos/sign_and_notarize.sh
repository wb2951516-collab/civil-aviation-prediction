set -euo pipefail

project_root="$(cd "$(dirname "$0")/../.." && pwd)"
meta_path="$project_root/packaging/app.json"
product_name="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['product_name'])")"

app_sign_identity="${APP_SIGN_IDENTITY:?APP_SIGN_IDENTITY is required}"
installer_sign_identity="${INSTALLER_SIGN_IDENTITY:-}"

app_path="$project_root/dist_macos/${product_name}.app"

codesign --force --deep --options runtime --sign "$app_sign_identity" "$app_path"
codesign --verify --deep --strict "$app_path"

if [ -n "$installer_sign_identity" ] && [ -f "$project_root/dist_installers/macos/${product_name}.pkg" ]; then
  pkg_in="$project_root/dist_installers/macos/${product_name}.pkg"
  pkg_out="$project_root/dist_installers/macos/${product_name}-signed.pkg"
  productsign --sign "$installer_sign_identity" "$pkg_in" "$pkg_out"
  printf "%s\n" "$pkg_out"
fi
