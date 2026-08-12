set -euo pipefail

project_root="$(cd "$(dirname "$0")/../.." && pwd)"
meta_path="$project_root/packaging/app.json"
version="$(python3 -c "import json;print(json.load(open(r'$meta_path','r',encoding='utf-8'))['version'])")"

cd "$project_root"

bash packaging/linux/build_binary.sh

out_dir="$project_root/dist_installers/linux"
mkdir -p "$out_dir"

topdir="$project_root/dist_installers/linux/rpmbuild"
rm -rf "$topdir"
mkdir -p "$topdir/BUILD" "$topdir/RPMS" "$topdir/SOURCES" "$topdir/SPECS" "$topdir/SRPMS"

cp "$project_root/dist_linux/capm" "$topdir/SOURCES/capm"
cp "$project_root/packaging/linux/capm.desktop" "$topdir/SOURCES/capm.desktop"
cp "$project_root/packaging/linux/rpm/capm.spec" "$topdir/SPECS/capm.spec"
sed -i "s/^Version:.*/Version: ${version}/" "$topdir/SPECS/capm.spec"

rpmbuild --define "_topdir ${topdir}" -bb "$topdir/SPECS/capm.spec"

rpm_path="$(find "$topdir/RPMS" -type f -name '*.rpm' | head -n 1)"
cp "$rpm_path" "$out_dir/"
printf "%s\n" "$out_dir/$(basename "$rpm_path")"
