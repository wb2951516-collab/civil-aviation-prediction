import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

from manim import config, tempconfig
from manim.utils.file_ops import open_file

from capm_manim.scenes.tutorial import CAPMTutorial

if __name__ == "__main__":
    config_file = repo_root / "capm_manim" / "manim.cfg"
    
    with tempconfig({"config_file": str(config_file)}):
        scene = CAPMTutorial()
        scene.render()
        
        output_dir = Path(config.media_dir) / "videos" / "tutorial" / "1080p60"
        video_files = list(output_dir.glob("CAPMTutorial.mp4"))
        
        if video_files:
            print(f"\n✓ 视频生成成功！")
            print(f"✓ 输出文件: {video_files[0]}")
            print(f"\n文件大小: {video_files[0].stat().st_size / (1024*1024):.2f} MB")
        else:
            print("\n✗ 视频文件未找到，请检查渲染输出")
