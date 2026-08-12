"""
调整视频速度并合并音频
Adjust video speed and merge with audio
"""

import subprocess
import imageio_ffmpeg
from pathlib import Path

def adjust_and_merge():
    print('=' * 60)
    print('调整视频速度并合并音频 / Adjust Video Speed and Merge Audio')
    print('=' * 60)
    
    input_video = Path('media/videos/narrated_3d/1080p30/CAPM_Narrated_3D.mp4')
    audio_dir = Path('media/videos/narrated_3d/audio')
    output_dir = Path('media/videos/synchronized_3d/1080p30')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / 'CAPM_Synchronized_3D_Final.mp4'
    temp_video = output_dir / 'temp_adjusted.mp4'
    
    audio_files = [
        'intro.mp3',
        'linear.mp3', 
        'holtwinters.mp3',
        'sarima.mp3',
        'ensemble.mp3',
        'holiday.mp3',
        'summary.mp3'
    ]
    
    print('\n1. 合并音频文件 / Merging audio files...')
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
    subprocess.run(cmd, capture_output=True, text=True)
    
    print('2. 获取时长 / Getting durations...')
    
    def get_duration(path):
        cmd = [ffmpeg_exe, '-i', str(path), '-f', 'null', '-']
        result = subprocess.run(cmd, capture_output=True, text=True)
        for line in result.stderr.split('\n'):
            if 'Duration:' in line:
                duration_str = line.split('Duration:')[1].split(',')[0].strip()
                h, m, s = duration_str.split(':')
                return float(h) * 3600 + float(m) * 60 + float(s)
        return 0
    
    video_duration = get_duration(input_video)
    audio_duration = get_duration(combined_audio)
    print(f'   原视频时长 / Original video duration: {video_duration:.2f} 秒')
    print(f'   音频时长 / Audio duration: {audio_duration:.2f} 秒')
    
    speed_factor = video_duration / audio_duration
    print(f'   速度调整因子 / Speed factor: {speed_factor:.4f}')
    
    print('\n3. 调整视频速度 / Adjusting video speed...')
    cmd = [
        ffmpeg_exe, '-y',
        '-i', str(input_video),
        '-filter:v', f'setpts={speed_factor}*PTS',
        '-filter:a', f'atempo={1/speed_factor}',
        '-c:v', 'libx264',
        '-crf', '18',
        '-preset', 'fast',
        '-an',
        str(temp_video)
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    
    print('4. 合并视频和音频 / Merging video and audio...')
    cmd = [
        ffmpeg_exe, '-y',
        '-i', str(temp_video),
        '-i', str(combined_audio),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-map', '0:v:0',
        '-map', '1:a:0',
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    
    if temp_video.exists():
        temp_video.unlink()
    
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        final_duration = get_duration(output_path)
        print('\n' + '=' * 60)
        print('✓ 音视频同步完成！')
        print('✓ Audio-Video Synchronization Complete!')
        print('=' * 60)
        print(f'✓ 文件 / File: {output_path.resolve()}')
        print(f'✓ 大小 / Size: {size_mb:.2f} MB')
        print(f'✓ 最终时长 / Final duration: {final_duration:.2f} 秒')
        print('=' * 60)
    else:
        print('\n✗ 同步失败 / Synchronization failed')

if __name__ == '__main__':
    adjust_and_merge()
