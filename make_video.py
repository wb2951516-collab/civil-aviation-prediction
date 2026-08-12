import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

try:
    import moviepy
    from moviepy.editor import ImageSequenceClip
    print(f"✓ MoviePy 版本: {moviepy.__version__}")
except ImportError:
    print("正在安装 MoviePy...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "moviepy"], check=True)
    import moviepy
    from moviepy.editor import ImageSequenceClip

def main():
    print('=' * 60)
    print('合成第二版完整视频')
    print('=' * 60)
    
    frames_dir = repo_root / 'media' / 'videos' / 'alternative' / 'frames'
    output_dir = repo_root / 'media' / 'videos' / 'alternative' / '1080p30'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'CAPM_Alternative.mp4'
    
    if not frames_dir.exists():
        print(f"✗ 帧目录不存在: {frames_dir}")
        print("请先运行: python alternative_video_simple.py")
        return
    
    frame_files = sorted(frames_dir.glob('frame_*.png'))
    
    if len(frame_files) == 0:
        print(f"✗ 未找到帧图片")
        return
    
    print(f"✓ 找到 {len(frame_files)} 帧")
    print(f"✓ 正在合成视频...")
    
    try:
        clip = ImageSequenceClip([str(f) for f in frame_files], fps=30)
        clip.write_videofile(
            str(output_path),
            codec='libx264',
            fps=30,
            bitrate='5000k',
            preset='medium'
        )
        
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print('=' * 60)
        print('✓ 第二版完整视频生成成功！')
        print(f'✓ 文件路径: {output_path.resolve()}')
        print(f'✓ 文件大小: {size_mb:.2f} MB')
        print(f'✓ 分辨率: 1920x1080')
        print(f'✓ 帧率: 30fps')
        print(f'✓ 时长: {len(frame_files)/30:.1f} 秒')
        print('=' * 60)
        
    except Exception as e:
        print(f"✗ 视频合成失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n提示：您仍然可以直接查看第一个版本的视频：")
        print(f"  media/videos/tutorial/1080p60/CAPMTutorial.mp4")

if __name__ == '__main__':
    main()
