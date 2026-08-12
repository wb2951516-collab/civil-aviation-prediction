set -euo pipefail

project_root="$(cd "$(dirname "$0")/../.." && pwd)"
meta_path="$project_root/packaging/app.json"
version="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['version'])")"
product_name="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['product_name'])")"
bundle_id="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['bundle_id'])")"

cd "$project_root"

python3 -m nuitka \
  --mode=standalone \
  --macos-create-app-bundle \
  --macos-app-name="$product_name" \
  --macos-app-version="$version" \
  --macos-app-protected-resource=packaging/app.json \
  --macos-app-company-name="$product_name" \
  --enable-plugin=tk-inter \
  --enable-plugin=matplotlib \
  --include-package=capm \
  --output-dir=dist_macos \
  CAPM.py

app_path="dist_macos/${product_name}.app"
if [ ! -d "$app_path" ]; then
  echo "Expected app bundle not found: $app_path" >&2
  exit 1
fi

printf "%s\n" "$app_path"
