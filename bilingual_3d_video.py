import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
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

class Bilingual3DVideo:
    def __init__(self):
        self.fig = None
        self.ax = None
        
        self.scenes = {
            'intro': {
                'title_cn': '民航旅客运输量预测模型',
                'title_en': 'Civil Aviation Passenger Traffic Prediction Model',
                'subtitle_cn': '3D 科学演示视频',
                'subtitle_en': '3D Scientific Demonstration Video',
                'duration': 5
            },
            'linear': {
                'title_cn': '线性回归模型',
                'title_en': 'Linear Regression Model',
                'subtitle_cn': 'y = β₀ + β₁x + β₂y',
                'subtitle_en': 'y = β₀ + β₁x + β₂y',
                'formula_cn': '预测值 = 截距 + 斜率 × 特征',
                'formula_en': 'Prediction = Intercept + Slope × Feature',
                'duration': 8
            },
            'holtwinters': {
                'title_cn': 'Holt-Winters 指数平滑',
                'title_en': 'Holt-Winters Exponential Smoothing',
                'subtitle_cn': '水平 + 趋势 + 季节性',
                'subtitle_en': 'Level + Trend + Seasonality',
                'formula_cn': '适用于具有趋势和季节性的时间序列',
                'formula_en': 'Suitable for time series with trend and seasonality',
                'duration': 8
            },
            'sarima': {
                'title_cn': 'SARIMA 季节模型',
                'title_en': 'SARIMA Seasonal Model',
                'subtitle_cn': '季节性自回归综合移动平均',
                'subtitle_en': 'Seasonal AutoRegressive Integrated Moving Average',
                'formula_cn': '捕捉复杂的时间序列模式',
                'formula_en': 'Captures complex time series patterns',
                'duration': 8
            },
            'ensemble': {
                'title_cn': '模型加权融合',
                'title_en': 'Weighted Ensemble Fusion',
                'subtitle_cn': 'ŷ = 0.4×HW + 0.3×SARIMA + 0.3×Linear',
                'subtitle_en': 'ŷ = 0.4×HW + 0.3×SARIMA + 0.3×Linear',
                'formula_cn': '集成学习提升预测精度',
                'formula_en': 'Ensemble learning improves prediction accuracy',
                'duration': 8
            },
            'holiday': {
                'title_cn': '节假日效应修正',
                'title_en': 'Holiday Effect Correction',
                'subtitle_cn': '系数 = 1 + (春运天数/月天数) × (效应-1)',
                'subtitle_en': 'Factor = 1 + (Spring Festival Days/Month Days) × (Effect-1)',
                'formula_cn': '调整春运等特殊时期的预测值',
                'formula_en': 'Adjusts predictions for special periods like Spring Festival',
                'duration': 6
            },
            'summary': {
                'title_cn': '总结',
                'title_en': 'Summary',
                'subtitle_cn': '可解释的预测流水线',
                'subtitle_en': 'Interpretable Prediction Pipeline',
                'duration': 6
            }
        }
        
    def setup_figure(self):
        self.fig = plt.figure(figsize=(WIDTH/DPI, HEIGHT/DPI), dpi=DPI, facecolor=BG_COLOR)
        self.fig.patch.set_facecolor(BG_COLOR)
        return self.fig
    
    def add_bilingual_title(self, ax, title_cn, title_en, y_top=0.92):
        if hasattr(ax, 'text2D'):
            ax.text2D(0.5, y_top, title_cn, ha='center', va='center', 
                    fontsize=36, color=TEXT_COLOR, fontweight='bold', 
                    transform=ax.transAxes)
            ax.text2D(0.5, y_top - 0.05, title_en, ha='center', va='center', 
                    fontsize=22, color=MUTED_COLOR, transform=ax.transAxes)
        else:
            ax.text(0.5, y_top, title_cn, ha='center', va='center', 
                    fontsize=36, color=TEXT_COLOR, fontweight='bold', 
                    transform=ax.transAxes)
            ax.text(0.5, y_top - 0.05, title_en, ha='center', va='center', 
                    fontsize=22, color=MUTED_COLOR, transform=ax.transAxes)
    
    def add_subtitle_bar(self, text_cn, text_en, y_pos=0.08):
        rect = plt.Rectangle((0.05, y_pos - 0.03), 0.9, 0.08, 
                             transform=self.fig.transFigure,
                             facecolor=SUBTITLE_BG, alpha=0.9,
                             edgecolor=MUTED_COLOR, linewidth=1)
        self.fig.patches.append(rect)
        
        self.fig.text(0.5, y_pos + 0.02, text_cn, ha='center', va='center',
                      fontsize=18, color=TEXT_COLOR, fontweight='bold')
        self.fig.text(0.5, y_pos - 0.015, text_en, ha='center', va='center',
                      fontsize=14, color=MUTED_COLOR)
    
    def create_3d_surface_frame(self, frame_num, total_frames, surface_type='linear'):
        self.fig = self.setup_figure()
        self.ax = self.fig.add_subplot(111, projection='3d', computed_zorder=False)
        self.ax.set_facecolor(BG_COLOR)
        
        progress = frame_num / total_frames
        
        X = np.linspace(-5, 5, 60)
        Y = np.linspace(-5, 5, 60)
        X, Y = np.meshgrid(X, Y)
        
        scene = self.scenes.get(surface_type, self.scenes['linear'])
        
        if surface_type == 'linear':
            Z = 7000 + 100*X + 80*Y
            cmap = 'viridis'
        elif surface_type == 'holtwinters':
            Z = 7000 + 500*np.sin(X*0.5) + 80*Y + 300*np.cos(Y*0.3)
            cmap = 'plasma'
        elif surface_type == 'sarima':
            Z = 7000 + 400*np.sin(X*0.8) + 300*np.cos(Y*0.6) + 200*np.sin((X+Y)*0.4)
            cmap = 'magma'
        else:
            Z = 7000 + 100*X + 80*Y
            cmap = 'viridis'
        
        elev = 25 + 10 * np.sin(progress * np.pi)
        azim = 45 + progress * 180
        
        surf = self.ax.plot_surface(X, Y, Z, cmap=cmap, alpha=0.85,
                                     linewidth=0, antialiased=True,
                                     rcount=40, ccount=40)
        
        self.ax.view_init(elev=elev, azim=azim)
        
        self.ax.set_xlabel('维度 X / Dimension X', color=MUTED_COLOR, fontsize=10, labelpad=8)
        self.ax.set_ylabel('维度 Y / Dimension Y', color=MUTED_COLOR, fontsize=10, labelpad=8)
        self.ax.set_zlabel('预测值 / Prediction', color=MUTED_COLOR, fontsize=10, labelpad=8)
        
        self.ax.tick_params(axis='x', colors=MUTED_COLOR, labelsize=7)
        self.ax.tick_params(axis='y', colors=MUTED_COLOR, labelsize=7)
        self.ax.tick_params(axis='z', colors=MUTED_COLOR, labelsize=7)
        
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.ax.xaxis.pane.set_edgecolor(BG_COLOR)
        self.ax.yaxis.pane.set_edgecolor(BG_COLOR)
        self.ax.zaxis.pane.set_edgecolor(BG_COLOR)
        
        self.add_bilingual_title(self.ax, scene['title_cn'], scene['title_en'])
        
        if 'formula_cn' in scene:
            self.add_subtitle_bar(scene['formula_cn'], scene['formula_en'])
        
        self.fig.canvas.draw()
        frame = np.array(self.fig.canvas.renderer.buffer_rgba())
        plt.close(self.fig)
        
        return frame
    
    def create_ensemble_3d_frame(self, frame_num, total_frames):
        self.fig = self.setup_figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor(BG_COLOR)
        
        progress = frame_num / total_frames
        scene = self.scenes['ensemble']
        
        X = np.linspace(-3, 3, 30)
        Y = np.linspace(-3, 3, 30)
        X, Y = np.meshgrid(X, Y)
        
        Z1 = 7000 + 100*X + 80*Y
        Z2 = 7000 + 300*np.sin(X*0.5) + 100*Y
        Z3 = 7000 + 200*np.sin(X*0.8) + 150*np.cos(Y*0.6)
        
        alpha = min(1, progress * 2)
        
        self.ax.plot_surface(X, Y, Z1, alpha=0.4*alpha, cmap='cool', linewidth=0)
        self.ax.plot_surface(X, Y, Z2, alpha=0.3*alpha, cmap='autumn', linewidth=0)
        self.ax.plot_surface(X, Y, Z3, alpha=0.25*alpha, cmap='winter', linewidth=0)
        
        Z_ensemble = 0.4*Z2 + 0.3*Z3 + 0.3*Z1
        self.ax.plot_surface(X, Y, Z_ensemble, alpha=0.7, cmap='viridis', linewidth=0)
        
        elev = 30 + 10 * np.sin(progress * np.pi)
        azim = 45 + progress * 180
        self.ax.view_init(elev=elev, azim=azim)
        
        self.ax.set_xlabel('X', color=MUTED_COLOR, fontsize=10)
        self.ax.set_ylabel('Y', color=MUTED_COLOR, fontsize=10)
        self.ax.set_zlabel('预测值 / Prediction', color=MUTED_COLOR, fontsize=10)
        
        self.ax.tick_params(axis='x', colors=MUTED_COLOR, labelsize=7)
        self.ax.tick_params(axis='y', colors=MUTED_COLOR, labelsize=7)
        self.ax.tick_params(axis='z', colors=MUTED_COLOR, labelsize=7)
        
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        
        self.add_bilingual_title(self.ax, scene['title_cn'], scene['title_en'])
        self.add_subtitle_bar(scene['formula_cn'], scene['formula_en'])
        
        self.fig.canvas.draw()
        frame = np.array(self.fig.canvas.renderer.buffer_rgba())
        plt.close(self.fig)
        
        return frame
    
    def create_intro_frame(self, frame_num, total_frames):
        self.fig = self.setup_figure()
        ax = self.fig.add_subplot(111)
        ax.axis('off')
        ax.set_facecolor(BG_COLOR)
        
        progress = frame_num / total_frames
        alpha = min(1, progress * 2)
        
        scene = self.scenes['intro']
        
        ax.text(0.5, 0.60, scene['title_cn'], ha='center', va='center', 
                fontsize=48, color=TEXT_COLOR, fontweight='bold', 
                alpha=alpha, transform=ax.transAxes)
        
        ax.text(0.5, 0.50, scene['title_en'], ha='center', va='center', 
                fontsize=28, color=MUTED_COLOR, alpha=alpha, transform=ax.transAxes)
        
        ax.text(0.5, 0.38, scene['subtitle_cn'], ha='center', va='center', 
                fontsize=32, color=ACCENT_COLOR, alpha=alpha, transform=ax.transAxes)
        
        ax.text(0.5, 0.30, scene['subtitle_en'], ha='center', va='center', 
                fontsize=20, color=MUTED_COLOR, alpha=alpha, transform=ax.transAxes)
        
        self.add_subtitle_bar('专业级3D相机过渡效果', 'Professional 3D Camera Transitions')
        
        self.fig.canvas.draw()
        frame = np.array(self.fig.canvas.renderer.buffer_rgba())
        plt.close(self.fig)
        
        return frame
    
    def create_holiday_frame(self, frame_num, total_frames):
        self.fig = self.setup_figure()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(BG_COLOR)
        
        progress = frame_num / total_frames
        scene = self.scenes['holiday']
        
        months_cn = ['1月', '2月', '3月', '4月', '5月', '6月', 
                     '7月', '8月', '9月', '10月', '11月', '12月']
        months_en = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        effects = [1.12, 1.15, 1.08, 1.0, 1.0, 1.0, 
                   1.10, 1.10, 1.0, 1.08, 1.0, 1.0]
        
        visible = int(12 * min(1, progress * 1.5))
        
        bars = ax.bar(range(12), effects, color='#FFA940', alpha=0.8, width=0.7)
        
        for i, bar in enumerate(bars[:visible]):
            bar.set_alpha(0.9)
        
        ax.axhline(y=1.0, color=ACCENT_COLOR, linestyle='--', linewidth=2, alpha=0.5)
        
        ax.set_xticks(range(12))
        ax.set_xticklabels([f'{cn}/{en}' for cn, en in zip(months_cn, months_en)], 
                          color=MUTED_COLOR, fontsize=10, rotation=45, ha='right')
        ax.set_ylabel('效应系数 / Effect Factor', color=MUTED_COLOR, fontsize=12)
        ax.tick_params(axis='y', colors=MUTED_COLOR)
        ax.set_ylim(0.95, 1.20)
        ax.grid(True, alpha=0.2, color='#2B3A55')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(MUTED_COLOR)
        ax.spines['left'].set_color(MUTED_COLOR)
        
        self.add_bilingual_title(ax, scene['title_cn'], scene['title_en'], y_top=0.88)
        self.add_subtitle_bar(scene['formula_cn'], scene['formula_en'])
        
        self.fig.canvas.draw()
        frame = np.array(self.fig.canvas.renderer.buffer_rgba())
        plt.close(self.fig)
        
        return frame
    
    def create_summary_frame(self, frame_num, total_frames):
        self.fig = self.setup_figure()
        ax = self.fig.add_subplot(111)
        ax.axis('off')
        ax.set_facecolor(BG_COLOR)
        
        progress = frame_num / total_frames
        scene = self.scenes['summary']
        
        ax.text(0.5, 0.82, scene['title_cn'], ha='center', va='center', 
                fontsize=48, color=TEXT_COLOR, fontweight='bold', transform=ax.transAxes)
        ax.text(0.5, 0.75, scene['title_en'], ha='center', va='center', 
                fontsize=28, color=MUTED_COLOR, transform=ax.transAxes)
        ax.text(0.5, 0.68, scene['subtitle_cn'], ha='center', va='center', 
                fontsize=24, color=ACCENT_COLOR, transform=ax.transAxes)
        ax.text(0.5, 0.62, scene['subtitle_en'], ha='center', va='center', 
                fontsize=18, color=MUTED_COLOR, transform=ax.transAxes)
        
        steps = [
            ('数据预处理', 'Data Preprocessing'),
            ('时间序列构建', 'Time Series Construction'),
            ('三模型预测', 'Three-Model Prediction'),
            ('加权融合', 'Weighted Fusion'),
            ('节假日修正', 'Holiday Correction'),
            ('增长率校准', 'Growth Calibration'),
            ('结果输出', 'Result Output')
        ]
        
        visible_steps = int(len(steps) * min(1, progress * 1.5))
        
        for i, (step_cn, step_en) in enumerate(steps[:visible_steps]):
            y = 0.52 - i * 0.065
            ax.text(0.5, y, f'• {step_cn} / {step_en}', ha='center', va='center', 
                    fontsize=18, color=ACCENT_COLOR, transform=ax.transAxes)
        
        self.fig.canvas.draw()
        frame = np.array(self.fig.canvas.renderer.buffer_rgba())
        plt.close(self.fig)
        
        return frame
    
    def generate_all_frames(self):
        print('=' * 60)
        print('生成双语慢速版3D视频 / Generating Bilingual Slow-Motion 3D Video')
        print('=' * 60)
        
        frames = []
        
        print('  [1/7] 创建介绍画面 / Creating intro...')
        duration = self.scenes['intro']['duration']
        for i in range(duration * FPS):
            frames.append(self.create_intro_frame(i, duration * FPS))
        
        print('  [2/7] 创建线性回归3D曲面 / Creating Linear Regression 3D...')
        duration = self.scenes['linear']['duration']
        for i in range(duration * FPS):
            frames.append(self.create_3d_surface_frame(i, duration * FPS, 'linear'))
        
        print('  [3/7] 创建Holt-Winters 3D曲面 / Creating Holt-Winters 3D...')
        duration = self.scenes['holtwinters']['duration']
        for i in range(duration * FPS):
            frames.append(self.create_3d_surface_frame(i, duration * FPS, 'holtwinters'))
        
        print('  [4/7] 创建SARIMA 3D曲面 / Creating SARIMA 3D...')
        duration = self.scenes['sarima']['duration']
        for i in range(duration * FPS):
            frames.append(self.create_3d_surface_frame(i, duration * FPS, 'sarima'))
        
        print('  [5/7] 创建集成融合3D / Creating Ensemble 3D...')
        duration = self.scenes['ensemble']['duration']
        for i in range(duration * FPS):
            frames.append(self.create_ensemble_3d_frame(i, duration * FPS))
        
        print('  [6/7] 创建节假日效应图表 / Creating Holiday Effect chart...')
        duration = self.scenes['holiday']['duration']
        for i in range(duration * FPS):
            frames.append(self.create_holiday_frame(i, duration * FPS))
        
        print('  [7/7] 创建总结画面 / Creating summary...')
        duration = self.scenes['summary']['duration']
        for i in range(duration * FPS):
            frames.append(self.create_summary_frame(i, duration * FPS))
        
        total_duration = sum(s['duration'] for s in self.scenes.values())
        
        print(f'\n✓ 总帧数 / Total frames: {len(frames)}')
        print(f'✓ 总时长 / Total duration: {len(frames)/FPS:.1f} 秒 / seconds')
        
        return frames
    
    def save_video(self, frames, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        frames_dir = output_path.parent / 'bilingual_frames'
        frames_dir.mkdir(exist_ok=True)
        
        print(f'\n  保存帧图片 / Saving frame images...')
        from PIL import Image
        for i, frame in enumerate(frames):
            img = Image.fromarray(frame)
            img.save(frames_dir / f'frame_{i:04d}.png')
            if i % 90 == 0:
                print(f'    进度 / Progress: {i}/{len(frames)} 帧 / frames')
        
        print(f'\n  合成视频 / Compositing video...')
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            cmd = [
                ffmpeg_exe,
                '-y',
                '-framerate', str(FPS),
                '-i', str(frames_dir / 'frame_%04d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-crf', '18',
                '-preset', 'slow',
                str(output_path)
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                print('=' * 60)
                print('✓ 双语慢速版3D视频生成成功！')
                print('✓ Bilingual Slow-Motion 3D Video Generated Successfully!')
                print('=' * 60)
                print(f'✓ 文件 / File: {output_path.resolve()}')
                print(f'✓ 大小 / Size: {size_mb:.2f} MB')
                print(f'✓ 时长 / Duration: {len(frames)/FPS:.1f} 秒 / seconds')
                print(f'✓ 分辨率 / Resolution: 1920x1080 @ {FPS}fps')
                print('=' * 60)
                print('\n功能特性 / Features:')
                print('  • 中英双语显示 / Chinese-English Bilingual Display')
                print('  • 慢速旋转动画 / Slow-Motion Rotation Animation')
                print('  • 字幕说明栏 / Subtitle Bar')
                print('  • 专业相机过渡 / Professional Camera Transitions')
        except Exception as e:
            print(f'✗ 视频合成失败 / Video composition failed: {e}')
            print(f'✓ 帧已保存到 / Frames saved to: {frames_dir}')

def main():
    video = Bilingual3DVideo()
    frames = video.generate_all_frames()
    video.save_video(frames, 'media/videos/bilingual_3d/1080p30/CAPM_Bilingual_3D.mp4')

if __name__ == '__main__':
    main()
