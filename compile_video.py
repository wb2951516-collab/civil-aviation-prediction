from pathlib import Path
import numpy as np
from PIL import Image

try:
    from moviepy.editor import ImageSequenceClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False
    print("提示: moviepy 未安装，正在尝试安装...")
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "moviepy"])
    from moviepy.editor import ImageSequenceClip
    HAS_MOVIEPY = True

def main():
    print('=' * 60)
    print('合成第二版视频')
    print('=' * 60)
    
    frames_dir = Path('media/videos/alternative/frames')
    output_path = Path('media/videos/alternative/1080p30/CAPM_Alternative.mp4')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not frames_dir.exists():
        print(f"✗ 帧目录不存在: {frames_dir}")
        print("请先运行: python alternative_video_simple.py")
        return
    
    frame_files = sorted(frames_dir.glob('frame_*.png'))
    
    if len(frame_files) == 0:
        print(f"✗ 未找到帧图片")
        return
    
    print(f"✓ 找到 {len(frame_files)} 帧")
    print(f"✓ 输出路径: {output_path.resolve()}")
    
    try:
        clip = ImageSequenceClip([str(f) for f in frame_files], fps=30)
        clip.write_videofile(str(output_path), codec='libx264', fps=30)
        
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print('=' * 60)
        print('✓ 视频合成成功！')
        print(f'✓ 文件: {output_path.resolve()}')
        print(f'✓ 大小: {size_mb:.2f} MB')
        print('=' * 60)
        
    except Exception as e:
        print(f"✗ 合成失败: {e}")
        print("\n替代方案：您可以直接查看帧图片")
        print(f"帧图片目录: {frames_dir.resolve()}")

if __name__ == '__main__':
    main()
