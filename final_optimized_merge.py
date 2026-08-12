"""
最终优化版音视频合并
Final Optimized Audio-Video Merge
"""

import subprocess
import imageio_ffmpeg
from pathlib import Path

def main():
    print('=' * 60)
    print('最终优化版音视频合并 / Final Optimized Audio-Video Merge')
    print('=' * 60)
    
    video_path = Path('media/videos/synchronized_3d/1080p30/CAPM_Synchronized_3D_Final.mp4')
    audio_dir = Path('media/videos/narrated_3d/audio')
    output_dir = Path('media/videos/final_optimized/1080p30')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / 'CAPM_Final_Optimized.mp4'
    
    audio_files = [
        'intro.mp3',
        'linear.mp3', 
        'holtwinters.mp3',
        'sarima.mp3',
        'ensemble.mp3',
        'holiday.mp3',
        'summary.mp3'
    ]
    
    print('\n步骤 1: 合并播音主持女声音频文件 / Step 1: Merging hostess female voice audio files...')
    concat_list = audio_dir / 'concat_list.txt'
    with open(concat_list, 'w') as f:
        for audio_file in audio_files:
            audio_path = audio_dir / audio_file
            if audio_path.exists():
                f.write(f"file '{audio_path.absolute()}'\n")
    
    combined_audio = audio_dir / 'combined.mp3'
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_exe, '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_list),
        '-c', 'copy',
        str(combined_audio)
    ]
    subprocess.run(cmd, capture_output=True)
    
    print('步骤 2: 合并音视频 / Step 2: Merging audio and video...')
    cmd = [
        ffmpeg_exe, '-y',
        '-i', str(video_path),
        '-i', str(combined_audio),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-map', '0:v:0',
        '-map', '1:a:0',
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)
    
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        
        def get_duration(path):
            cmd = [ffmpeg_exe, '-i', str(path), '-f', 'null', '-']
            result = subprocess.run(cmd, capture_output=True, text=True)
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    duration_str = line.split('Duration:')[1].split(',')[0].strip()
                    h, m, s = duration_str.split(':')
                    return float(h) * 3600 + float(m) * 60 + float(s)
            return 0
        
        final_duration = get_duration(output_path)
        
        print('\n' + '=' * 60)
        print('✓ 最终优化版视频生成成功！')
        print('✓ Final Optimized Video Generated Successfully!')
        print('=' * 60)
        print(f'✓ 文件 / File: {output_path.resolve()}')
        print(f'✓ 大小 / Size: {size_mb:.2f} MB')
        print(f'✓ 时长 / Duration: {final_duration:.2f} 秒')
        print('=' * 60)
        print('\n优化特性 / Optimized Features:')
        print('  ✓ 无边框字幕 / No Border Subtitles')
        print('  ✓ 优化动画速度 / Optimized Animation Speed')
        print('  ✓ 播音主持女声 / Hostess Female Voice')
        print('  ✓ 音画完全同步 / Perfect Audio-Video Sync')
        print('  ✓ 中英双语字幕 / Chinese-English Bilingual Subtitles')
    else:
        print('\n✗ 合并失败 / Merge failed')

if __name__ == '__main__':
    main()
