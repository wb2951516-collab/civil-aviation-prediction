"""
优化版音画同步3D视频生成器
Optimized Audio-Video Synchronized 3D Video Generator
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import imageio_ffmpeg
import subprocess
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

WIDTH, HEIGHT = 1920, 1080
DPI = 100
FPS = 30

BG_COLOR = '#0B0F1A'
TEXT_COLOR = '#EAECEF'
MUTED_COLOR = '#9AA4B2'
ACCENT_COLOR = '#40A9FF'
SUBTITLE_BG = '#1A1F2E'

NARRATION_SCRIPTS = {
    'intro': {'duration': 20.0},
    'linear': {'duration': 17.0},
    'holtwinters': {'duration': 18.0},
    'sarima': {'duration': 17.0},
    'ensemble': {'duration': 18.0},
    'holiday': {'duration': 16.0},
    'summary': {'duration': 17.5},
}

class OptimizedSyncVideo:
    def __init__(self):
        self.fig = None
    
    def setup_figure(self):
        self.fig = plt.figure(figsize=(WIDTH/DPI, HEIGHT/DPI), dpi=DPI, facecolor=BG_COLOR)
        self.fig.patch.set_facecolor(BG_COLOR)
        return self.fig
    
    def create_simple_frame(self, frame_num, total_frames, scene_type):
        self.setup_figure()
        ax = self.fig.add_subplot(111)
        ax.axis('off')
        ax.set_facecolor(BG_COLOR)
        
        progress = frame_num / total_frames
        
        titles = {
            'intro': ('民航旅客运输量预测模型', 'Civil Aviation Passenger Traffic Prediction Model'),
            'linear': ('线性回归模型', 'Linear Regression Model'),
            'holtwinters': ('Holt-Winters 指数平滑', 'Holt-Winters Exponential Smoothing'),
            'sarima': ('SARIMA 季节模型', 'SARIMA Seasonal Model'),
            'ensemble': ('模型加权融合', 'Weighted Ensemble Fusion'),
            'holiday': ('节假日效应修正', 'Holiday Effect Correction'),
            'summary': ('预测流水线总结', 'Prediction Pipeline Summary'),
        }
        
        title_cn, title_en = titles.get(scene_type, ('', ''))
        
        alpha = min(1, progress * 2)
        ax.text(0.5, 0.6, title_cn, ha='center', va='center', 
                fontsize=48, color=TEXT_COLOR, fontweight='bold', 
                alpha=alpha, transform=ax.transAxes)
        ax.text(0.5, 0.5, title_en, ha='center', va='center', 
                fontsize=28, color=MUTED_COLOR, alpha=alpha, transform=ax.transAxes)
        
        self.fig.canvas.draw()
        frame = np.array(self.fig.canvas.renderer.buffer_rgba())
        plt.close(self.fig)
        return frame
    
    def generate_video(self):
        print('=' * 60)
        print('生成音画同步3D视频 / Generating Audio-Video Synchronized 3D Video')
        print('=' * 60)
        
        output_dir = Path('media/videos/synchronized_3d/1080p30')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        frames_dir = output_dir / 'frames'
        frames_dir.mkdir(exist_ok=True)
        
        frame_count = 0
        scene_order = ['intro', 'linear', 'holtwinters', 'sarima', 'ensemble', 'holiday', 'summary']
        
        for idx, scene in enumerate(scene_order):
            print(f'  [{idx+1}/{len(scene_order)}] 生成场景 / Generating scene: {scene}...')
            duration = NARRATION_SCRIPTS[scene]['duration']
            total_frames = int(duration * FPS)
            
            for i in range(total_frames):
                frame = self.create_simple_frame(i, total_frames, scene)
                from PIL import Image
                img = Image.fromarray(frame)
                img.save(frames_dir / f'frame_{frame_count:05d}.png')
                frame_count += 1
        
        print(f'\n✓ 总帧数 / Total frames: {frame_count}')
        print('合成视频 / Compositing video...')
        
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        output_path = output_dir / 'CAPM_Synchronized_3D.mp4'
        
        cmd = [
            ffmpeg_exe, '-y',
            '-framerate', str(FPS),
            '-i', str(frames_dir / 'frame_%05d.png'),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-preset', 'veryfast',
            str(output_path)
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print('=' * 60)
            print('✓ 无声视频生成成功！')
            print('✓ Silent Video Generated Successfully!')
            print('=' * 60)
            print(f'✓ 文件 / File: {output_path.resolve()}')
            print(f'✓ 大小 / Size: {size_mb:.2f} MB')
            print(f'✓ 时长 / Duration: {frame_count/FPS:.1f} 秒')
            print('=' * 60)
            print('\n下一步 / Next step: 请运行 merge_audio_video_sync.py 来合并音频')
        else:
            print('✗ 视频生成失败 / Video generation failed')

def main():
    video = OptimizedSyncVideo()
    video.generate_video()

if __name__ == '__main__':
    main()
