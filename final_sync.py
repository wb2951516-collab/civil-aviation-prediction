"""
最终音画同步脚本
Final Audio-Video Synchronization Script
"""

import subprocess
import imageio_ffmpeg
from pathlib import Path

def main():
    print('=' * 60)
    print('最终音画同步处理 / Final Audio-Video Synchronization')
    print('=' * 60)
    
    video_path = Path('media/videos/narrated_3d/1080p30/CAPM_Narrated_3D.mp4')
    audio_dir = Path('media/videos/narrated_3d/audio')
    output_dir = Path('media/videos/synchronized_3d/1080p30')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / 'CAPM_Synchronized_3D_Final.mp4'
    combined_audio = audio_dir / 'combined.mp3'
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    audio_files = ['intro.mp3', 'linear.mp3', 'holtwinters.mp3', 'sarima.mp3', 
                  'ensemble.mp3', 'holiday.mp3', 'summary.mp3']
    
    print('\n步骤 1: 合并音频文件 / Step 1: Merging audio files...')
    concat_list = audio_dir / 'concat_list.txt'
    with open(concat_list, 'w') as f:
        for af in audio_files:
            ap = audio_dir / af
            if ap.exists():
                f.write(f"file '{ap.absolute()}'\n")
    
    cmd = [ffmpeg_exe, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_list), '-c', 'copy', str(combined_audio)]
    subprocess.run(cmd, capture_output=True)
    
    print('步骤 2: 获取时长 / Step 2: Getting durations...')
    def get_dur(p):
        cmd = [ffmpeg_exe, '-i', str(p), '-f', 'null', '-']
        r = subprocess.run(cmd, capture_output=True, text=True)
        for line in r.stderr.split('\n'):
            if 'Duration:' in line:
                d = line.split('Duration:')[1].split(',')[0].strip()
                h, m, s = d.split(':')
                return float(h)*3600 + float(m)*60 + float(s)
        return 0
    
    vd = get_dur(video_path)
    ad = get_dur(combined_audio)
    print(f'  视频时长 / Video: {vd:.2f}s, 音频时长 / Audio: {ad:.2f}s')
    
    factor = vd / ad
    print(f'  速度因子 / Speed factor: {factor:.4f}')
    
    print('步骤 3: 调整视频速度 / Step 3: Adjusting video speed...')
    temp_vid = output_dir / 'temp.mp4'
    cmd = [ffmpeg_exe, '-y', '-i', str(video_path), 
           '-filter:v', f'setpts={factor}*PTS', 
           '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-an', str(temp_vid)]
    subprocess.run(cmd, capture_output=True)
    
    print('步骤 4: 合并音视频 / Step 4: Merging audio and video...')
    cmd = [ffmpeg_exe, '-y', '-i', str(temp_vid), '-i', str(combined_audio),
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', 
           '-map', '0:v:0', '-map', '1:a:0', str(output_path)]
    subprocess.run(cmd, capture_output=True)
    
    if temp_vid.exists():
        temp_vid.unlink()
    
    if output_path.exists():
        size = output_path.stat().st_size / (1024*1024)
        fd = get_dur(output_path)
        print('\n' + '='*60)
        print('✓ 完成！/ Done!')
        print('='*60)
        print(f'文件 / File: {output_path}')
        print(f'大小 / Size: {size:.2f} MB')
        print(f'时长 / Duration: {fd:.2f} 秒')
        print('='*60)
    else:
        print('✗ 失败 / Failed')

if __name__ == '__main__':
    main()
