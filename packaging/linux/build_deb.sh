set -euo pipefail

project_root="$(cd "$(dirname "$0")/../.." && pwd)"
meta_path="$project_root/packaging/app.json"
version="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['version'])")"

cd "$project_root"

if [ "${REUSE_BINARY:-0}" = "1" ] && [ -x "$project_root/dist_linux/capm" ]; then
  echo "Reusing existing dist_linux/capm (REUSE_BINARY=1)"
else
  bash packaging/linux/build_binary.sh
fi

out_dir="$project_root/dist_installers/linux"
mkdir -p "$out_dir"

stage="$project_root/dist_installers/linux/deb_root"
rm -rf "$stage"
mkdir -p "$stage/DEBIAN" "$stage/opt/capm" "$stage/usr/bin" "$stage/usr/share/applications" "$stage/usr/share/icons/hicolor/256x256/apps"

cp "$project_root/packaging/linux/deb/control" "$stage/DEBIAN/control"
sed -i "s/^Version:.*/Version: ${version}/" "$stage/DEBIAN/control"

install -m 0755 "$project_root/dist_linux/capm" "$stage/opt/capm/capm"
install -m 0755 "$project_root/dist_linux/capm" "$stage/usr/bin/capm"
install -m 0644 "$project_root/packaging/linux/capm.desktop" "$stage/usr/share/applications/capm.desktop"
install -m 0644 "$project_root/assets/airCAPM_256.png" "$stage/usr/share/icons/hicolor/256x256/apps/capm.png"

install -m 0755 "$project_root/packaging/linux/deb/postinst" "$stage/DEBIAN/postinst"
install -m 0755 "$project_root/packaging/linux/deb/postrm" "$stage/DEBIAN/postrm"

deb_path="$out_dir/capm_${version}_amd64.deb"
rm -f "$deb_path"
dpkg-deb --build "$stage" "$deb_path"
printf "%s\n" "$deb_path"
