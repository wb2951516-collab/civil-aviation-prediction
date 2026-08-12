import sys
import subprocess
from pathlib import Path

def check_import(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
        print(f"✓ {package_name} 已安装")
        return True
    except ImportError:
        print(f"✗ {package_name} 未安装")
        return False

print("检查项目依赖...")
print("=" * 50)

deps = [
    ("manim", "manim"),
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("matplotlib", "matplotlib"),
    ("scipy", "scipy"),
    ("statsmodels", "statsmodels"),
]

all_ok = True
for package, import_name in deps:
    if not check_import(package, import_name):
        all_ok = False

print("=" * 50)
if all_ok:
    print("所有依赖已就绪！")
else:
    print("部分依赖缺失，正在安装...")
    subprocess.run([sys.executable, "-m", "pip", "install", "manim", "numpy", "pandas", "matplotlib", "scipy", "statsmodels"])
