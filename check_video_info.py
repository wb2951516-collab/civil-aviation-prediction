from pathlib import Path

video_path = Path("media/videos/tutorial/1080p60/CAPMTutorial.mp4")

if video_path.exists():
    size_mb = video_path.stat().st_size / (1024 * 1024)
    print("=" * 60)
    print("✓ 第一个版本（Manim）视频生成成功！")
    print("=" * 60)
    print(f"文件路径: {video_path.resolve()}")
    print(f"文件大小: {size_mb:.2f} MB")
    print("分辨率: 1920x1080 (1080p)")
    print("帧率: 60fps")
    print("=" * 60)
    
    print("\n📁 相关文件:")
    print(f"  配置文件: capm_manim/manim.cfg")
    print(f"  动画脚本: capm_manim/scenes/tutorial.py")
    print(f"  组件库: capm_manim/components/")
else:
    print("✗ 视频文件未找到")
