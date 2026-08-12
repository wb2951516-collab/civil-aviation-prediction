"""
合并视频和音频 / Merge Video and Audio
"""

import subprocess
import imageio_ffmpeg
from pathlib import Path

def merge_video_audio():
    video_path = Path('media/videos/narrated_3d/1080p30/CAPM_Narrated_3D.mp4')
    audio_dir = Path('media/videos/narrated_3d/audio')
    output_path = Path('media/videos/narrated_3d/1080p30/CAPM_Narrated_3D_Final.mp4')
    
    audio_files = [
        'intro.mp3',
        'linear.mp3', 
        'holtwinters.mp3',
        'sarima.mp3',
        'ensemble.mp3',
        'holiday.mp3',
        'summary.mp3'
    ]
    
    concat_list = audio_dir / 'concat_list.txt'
    with open(concat_list, 'w') as f:
        for audio_file in audio_files:
            audio_path = audio_dir / audio_file
            if audio_path.exists():
                f.write(f"file '{audio_path.absolute()}'\n")
    
    combined_audio = audio_dir / 'combined.mp3'
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    print('合并音频文件 / Merging audio files...')
    cmd = [
        ffmpeg_exe, '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_list),
        '-c', 'copy',
        str(combined_audio)
    ]
    subprocess.run(cmd, capture_output=True)
    
    print('合并视频和音频 / Merging video and audio...')
    cmd = [
        ffmpeg_exe, '-y',
        '-i', str(video_path),
        '-i', str(combined_audio),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-shortest',
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)
    
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print('=' * 60)
        print('✓ 专业解说版视频生成成功！')
        print('✓ Professional Narrated Video Generated Successfully!')
        print('=' * 60)
        print(f'✓ 文件 / File: {output_path.resolve()}')
        print(f'✓ 大小 / Size: {size_mb:.2f} MB')
        print('=' * 60)
    else:
        print('✗ 合并失败 / Merge failed')

if __name__ == '__main__':
    merge_video_audio()
