set -euo pipefail

project_root="$(cd "$(dirname "$0")/../.." && pwd)"
meta_path="$project_root/packaging/app.json"
product_name="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['product_name'])")"

cd "$project_root"
rm -rf dist_linux
mkdir -p dist_linux

python3 -m nuitka \
  --mode=onefile \
  --assume-yes-for-downloads \
  --nofollow-import-to=*.tests \
  --output-dir=dist_linux \
  --output-filename=capm \
  --include-package=capm \
  --enable-plugin=tk-inter \
  --enable-plugin=matplotlib \
  CAPM.py

bin_path="$project_root/dist_linux/capm"
if [ ! -f "$bin_path" ]; then
  echo "Expected binary not found: $bin_path" >&2
  exit 1
fi
chmod +x "$bin_path"
printf "%s\n" "$bin_path"
