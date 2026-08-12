import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

print('正在检查 imageio_ffmpeg...')
try:
    import imageio_ffmpeg
    print(f'✓ imageio_ffmpeg 已安装')
except ImportError:
    print('正在安装 imageio_ffmpeg...')
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "imageio_ffmpeg"], check=True)
    import imageio_ffmpeg

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
        return
    
    frame_files = sorted(frames_dir.glob('frame_*.png'))
    
    if len(frame_files) == 0:
        print(f"✗ 未找到帧图片")
        return
    
    print(f"✓ 找到 {len(frame_files)} 帧")
    print(f"✓ 输出路径: {output_path.resolve()}")
    
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"✓ 使用 FFmpeg: {ffmpeg_exe}")
        
        cmd = [
            ffmpeg_exe,
            '-y',
            '-framerate', '30',
            '-i', str(frames_dir / 'frame_%04d.png'),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            str(output_path)
        ]
        
        print(f"✓ 正在合成视频...")
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print('=' * 60)
            print('✓ 第二版完整视频生成成功！')
            print(f'✓ 文件: {output_path.resolve()}')
            print(f'✓ 大小: {size_mb:.2f} MB')
            print('=' * 60)
            print('\n两个版本的视频现在都已完成：')
            print('  版本一（Manim）: media/videos/tutorial/1080p60/CAPMTutorial.mp4')
            print(f'  版本二（PIL）: {output_path.resolve()}')
        else:
            print(f"✗ FFmpeg 返回错误: {result.returncode}")
            print(result.stderr)
            
    except Exception as e:
        print(f"✗ 合成失败: {e}")
        import traceback
        traceback.print_exc()
        print('\n不过不用担心！第一个版本的视频已经可以观看：')
        print('  media/videos/tutorial/1080p60/CAPMTutorial.mp4')

if __name__ == '__main__':
    main()
