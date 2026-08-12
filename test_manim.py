import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

print("尝试导入 manim...")
try:
    import manim
    print(f"✓ manim 包导入成功")
    print(f"  包位置: {manim.__file__}")
    
    # 查看 manim 包的内容
    print("\nmanim 包内容:")
    print(dir(manim))
    
    # 尝试查看可用的模块
    print("\n尝试查找 Scene 类...")
    from manim import Scene
    print("✓ Scene 类找到")
    
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
