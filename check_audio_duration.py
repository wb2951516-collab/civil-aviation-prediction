"""
使用ffmpeg检查音频文件时长 / Check Audio File Durations with ffmpeg
"""

import subprocess
import imageio_ffmpeg
from pathlib import Path

def get_audio_duration(audio_path):
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        '-i', str(audio_path),
        '-f', 'null',
        '-'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr
    
    duration_str = None
    for line in output.split('\n'):
        if 'Duration:' in line:
            duration_str = line.split('Duration:')[1].split(',')[0].strip()
            break
    
    if duration_str:
        h, m, s = duration_str.split(':')
        total_seconds = float(h) * 3600 + float(m) * 60 + float(s)
        return total_seconds
    return 0

def check_audio_durations():
    audio_dir = Path('media/videos/narrated_3d/audio')
    if not audio_dir.exists():
        print("音频目录不存在 / Audio directory not found")
        return {}
    
    audio_files = [
        'intro.mp3',
        'linear.mp3',
        'holtwinters.mp3',
        'sarima.mp3',
        'ensemble.mp3',
        'holiday.mp3',
        'summary.mp3'
    ]
    
    durations = {}
    print('=' * 60)
    print('音频文件时长 / Audio File Durations')
    print('=' * 60)
    
    for audio_file in audio_files:
        audio_path = audio_dir / audio_file
        if audio_path.exists():
            try:
                duration = get_audio_duration(audio_path)
                durations[audio_file.replace('.mp3', '')] = duration
                print(f'  {audio_file:15s} → {duration:.2f} 秒 / seconds')
            except Exception as e:
                print(f'  {audio_file:15s} → 读取失败 / Error: {e}')
        else:
            print(f'  {audio_file:15s} → 文件不存在 / File not found')
    
    total_duration = sum(durations.values())
    print('=' * 60)
    print(f'  总时长 / Total Duration: {total_duration:.2f} 秒 / seconds')
    print('=' * 60)
    
    return durations

if __name__ == '__main__':
    check_audio_durations()
