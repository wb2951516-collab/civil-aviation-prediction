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

class Enhanced3DVideo:
    def __init__(self):
        self.fig = None
        self.ax = None
        
    def setup_figure(self):
        self.fig = plt.figure(figsize=(WIDTH/DPI, HEIGHT/DPI), dpi=DPI, facecolor=BG_COLOR)
        self.fig.patch.set_facecolor(BG_COLOR)
        return self.fig
    
    def create_3d_surface_frame(self, frame_num, total_frames, surface_type='linear'):
        self.fig = self.setup_figure()
        self.ax = self.fig.add_subplot(111, projection='3d', computed_zorder=False)
        self.ax.set_facecolor(BG_COLOR)
        
        progress = frame_num / total_frames
        
        X = np.linspace(-5, 5, 80)
        Y = np.linspace(-5, 5, 80)
        X, Y = np.meshgrid(X, Y)
        
        if surface_type == 'linear':
            Z = 7000 + 100*X + 80*Y
            title = 'Linear Regression Model'
            subtitle = 'y = β₀ + β₁x + β₂y'
            cmap = 'viridis'
        elif surface_type == 'holtwinters':
            Z = 7000 + 500*np.sin(X*0.5) + 80*Y + 300*np.cos(Y*0.3)
            title = 'Holt-Winters Exponential Smoothing'
            subtitle = 'Level + Trend + Seasonality'
            cmap = 'plasma'
        elif surface_type == 'sarima':
            Z = 7000 + 400*np.sin(X*0.8) + 300*np.cos(Y*0.6) + 200*np.sin((X+Y)*0.4)
            title = 'SARIMA Model'
            subtitle = 'Seasonal ARIMA'
            cmap = 'magma'
        else:
            Z = 7000 + 100*X + 80*Y
            title = '3D Visualization'
            subtitle = 'Mathematical Surface'
            cmap = 'viridis'
        
        elev = 25 + 15 * np.sin(progress * 2 * np.pi)
        azim = 45 + progress * 360
        
        surf = self.ax.plot_surface(X, Y, Z, cmap=cmap, alpha=0.85,
                                     linewidth=0, antialiased=True,
                                     rcount=50, ccount=50)
        
        self.ax.view_init(elev=elev, azim=azim)
        
        self.ax.set_xlabel('Dimension X', color=MUTED_COLOR, fontsize=12, labelpad=10)
        self.ax.set_ylabel('Dimension Y', color=MUTED_COLOR, fontsize=12, labelpad=10)
        self.ax.set_zlabel('Prediction Z', color=MUTED_COLOR, fontsize=12, labelpad=10)
        
        self.ax.tick_params(axis='x', colors=MUTED_COLOR, labelsize=8)
        self.ax.tick_params(axis='y', colors=MUTED_COLOR, labelsize=8)
        self.ax.tick_params(axis='z', colors=MUTED_COLOR, labelsize=8)
        
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.ax.xaxis.pane.set_edgecolor(BG_COLOR)
        self.ax.yaxis.pane.set_edgecolor(BG_COLOR)
        self.ax.zaxis.pane.set_edgecolor(BG_COLOR)
        
        self.ax.set_title(title, color=TEXT_COLOR, fontsize=28, fontweight='bold', pad=20)
        
        self.fig.text(0.5, 0.88, subtitle, ha='center', va='center', 
                      fontsize=20, color=MUTED_COLOR)
        
        self.fig.canvas.draw()
        frame = np.array(self.fig.canvas.renderer.buffer_rgba())
        plt.close(self.fig)
        
        return frame
    
    def create_3d_scatter_frame(self, frame_num, total_frames):
        self.fig = self.setup_figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor(BG_COLOR)
        
        progress = frame_num / total_frames
        
        np.random.seed(42)
        n_points = 100
        
        t = np.linspace(0, 4*np.pi, n_points)
        x = t + np.random.randn(n_points) * 0.3
        y = np.sin(t) * 2 + np.random.randn(n_points) * 0.2
        z = 7000 + 500*t/(4*np.pi) + 200*np.cos(t*2) + np.random.randn(n_points) * 50
        
        colors = plt.cm.viridis(np.linspace(0, 1, n_points))
        
        visible = int(n_points * min(1, progress * 1.5))
        
        scatter = self.ax.scatter(x[:visible], y[:visible], z[:visible], 
                                   c=colors[:visible], s=50, alpha=0.8,
                                   edgecolors='white', linewidths=0.5)
        
        if visible > 1:
            self.ax.plot(x[:visible], y[:visible], z[:visible], 
                        color=ACCENT_COLOR, alpha=0.4, linewidth=2)
        
        elev = 20 + 10 * np.sin(progress * 3 * np.pi)
        azim = 30 + progress * 270
        self.ax.view_init(elev=elev, azim=azim)
        
        self.ax.set_xlabel('Time', color=MUTED_COLOR, fontsize=12)
        self.ax.set_ylabel('Seasonal', color=MUTED_COLOR, fontsize=12)
        self.ax.set_zlabel('Passengers', color=MUTED_COLOR, fontsize=12)
        
        self.ax.tick_params(axis='x', colors=MUTED_COLOR, labelsize=8)
        self.ax.tick_params(axis='y', colors=MUTED_COLOR, labelsize=8)
        self.ax.tick_params(axis='z', colors=MUTED_COLOR, labelsize=8)
        
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        
        self.ax.set_title('Time Series Data Visualization', 
                          color=TEXT_COLOR, fontsize=28, fontweight='bold', pad=20)
        
        self.fig.text(0.5, 0.88, 'Historical Passenger Traffic Data', 
                      ha='center', fontsize=20, color=MUTED_COLOR)
        
        self.fig.canvas.draw()
        frame = np.array(self.fig.canvas.renderer.buffer_rgba())
        plt.close(self.fig)
        
        return frame
    
    def create_ensemble_3d_frame(self, frame_num, total_frames):
        self.fig = self.setup_figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor(BG_COLOR)
        
        progress = frame_num / total_frames
        
        X = np.linspace(-3, 3, 40)
        Y = np.linspace(-3, 3, 40)
        X, Y = np.meshgrid(X, Y)
        
        Z1 = 7000 + 100*X + 80*Y
        Z2 = 7000 + 300*np.sin(X*0.5) + 100*Y
        Z3 = 7000 + 200*np.sin(X*0.8) + 150*np.cos(Y*0.6)
        
        alpha = min(1, progress * 2)
        
        self.ax.plot_surface(X, Y, Z1, alpha=0.5*alpha, cmap='cool', linewidth=0)
        self.ax.plot_surface(X, Y, Z2, alpha=0.4*alpha, cmap='autumn', linewidth=0)
        self.ax.plot_surface(X, Y, Z3, alpha=0.3*alpha, cmap='winter', linewidth=0)
        
        Z_ensemble = 0.4*Z2 + 0.3*Z3 + 0.3*Z1
        self.ax.plot_surface(X, Y, Z_ensemble, alpha=0.7, cmap='viridis', linewidth=0)
        
        elev = 30 + 15 * np.sin(progress * 2 * np.pi)
        azim = 45 + progress * 360
        self.ax.view_init(elev=elev, azim=azim)
        
        self.ax.set_xlabel('X', color=MUTED_COLOR, fontsize=12)
        self.ax.set_ylabel('Y', color=MUTED_COLOR, fontsize=12)
        self.ax.set_zlabel('Prediction', color=MUTED_COLOR, fontsize=12)
        
        self.ax.tick_params(axis='x', colors=MUTED_COLOR, labelsize=8)
        self.ax.tick_params(axis='y', colors=MUTED_COLOR, labelsize=8)
        self.ax.tick_params(axis='z', colors=MUTED_COLOR, labelsize=8)
        
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        
        self.ax.set_title('Ensemble Model Fusion', 
                          color=TEXT_COLOR, fontsize=28, fontweight='bold', pad=20)
        
        self.fig.text(0.5, 0.88, 'ŷ = 0.4×HW + 0.3×SARIMA + 0.3×Linear', 
                      ha='center', fontsize=20, color=MUTED_COLOR)
        
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
        
        alpha = min(1, progress * 3)
        
        ax.text(0.5, 0.55, 'Civil Aviation Passenger\nTraffic Prediction Model', 
                ha='center', va='center', fontsize=52, color=TEXT_COLOR, 
                fontweight='bold', alpha=alpha, transform=ax.transAxes)
        
        ax.text(0.5, 0.35, 'Enhanced 3D Scientific Demonstration', 
                ha='center', va='center', fontsize=32, color=MUTED_COLOR, 
                alpha=alpha, transform=ax.transAxes)
        
        ax.text(0.5, 0.25, 'Professional Camera Transitions & Dynamic Visualizations', 
                ha='center', va='center', fontsize=24, color=ACCENT_COLOR, 
                alpha=alpha, transform=ax.transAxes)
        
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
        
        ax.text(0.5, 0.75, 'Summary', ha='center', va='center', 
                fontsize=56, color=TEXT_COLOR, fontweight='bold', 
                transform=ax.transAxes)
        
        ax.text(0.5, 0.62, 'Interpretable Prediction Pipeline', 
                ha='center', va='center', fontsize=32, color=MUTED_COLOR, 
                transform=ax.transAxes)
        
        steps = [
            'Data Preprocessing',
            'Time Series Construction', 
            'Three-Model Prediction',
            'Weighted Ensemble Fusion',
            'Holiday Effect Correction',
            'Growth Rate Calibration',
            'Result Output'
        ]
        
        visible_steps = int(len(steps) * min(1, progress * 1.5))
        
        for i, step in enumerate(steps[:visible_steps]):
            y = 0.52 - i * 0.06
            ax.text(0.5, y, f'• {step}', ha='center', va='center', 
                    fontsize=24, color=ACCENT_COLOR, transform=ax.transAxes)
        
        self.fig.canvas.draw()
        frame = np.array(self.fig.canvas.renderer.buffer_rgba())
        plt.close(self.fig)
        
        return frame
    
    def generate_all_frames(self):
        print('=' * 60)
        print('Generating Enhanced 3D Video with Camera Transitions')
        print('=' * 60)
        
        frames = []
        
        print('  [1/6] Creating intro with fade-in...')
        for i in range(60):
            frames.append(self.create_intro_frame(i, 60))
        
        print('  [2/6] Creating Linear Regression 3D surface with rotation...')
        for i in range(120):
            frames.append(self.create_3d_surface_frame(i, 120, 'linear'))
        
        print('  [3/6] Creating Holt-Winters 3D surface with dynamic camera...')
        for i in range(120):
            frames.append(self.create_3d_surface_frame(i, 120, 'holtwinters'))
        
        print('  [4/6] Creating SARIMA 3D surface with smooth transitions...')
        for i in range(120):
            frames.append(self.create_3d_surface_frame(i, 120, 'sarima'))
        
        print('  [5/6] Creating Ensemble fusion with multi-surface rotation...')
        for i in range(120):
            frames.append(self.create_ensemble_3d_frame(i, 120))
        
        print('  [6/6] Creating summary with progressive reveal...')
        for i in range(60):
            frames.append(self.create_summary_frame(i, 60))
        
        print(f'\n✓ Total frames generated: {len(frames)}')
        print(f'✓ Estimated duration: {len(frames)/FPS:.1f} seconds')
        
        return frames
    
    def save_video(self, frames, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        frames_dir = output_path.parent / 'enhanced_3d_frames'
        frames_dir.mkdir(exist_ok=True)
        
        print(f'\n  Saving frame images...')
        for i, frame in enumerate(frames):
            from PIL import Image
            img = Image.fromarray(frame)
            img.save(frames_dir / f'frame_{i:04d}.png')
            if i % 60 == 0:
                print(f'    Progress: {i}/{len(frames)} frames')
        
        print(f'\n  Compositing video with FFmpeg...')
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
                print('✓ Enhanced 3D Video Generated Successfully!')
                print(f'✓ File: {output_path.resolve()}')
                print(f'✓ Size: {size_mb:.2f} MB')
                print(f'✓ Duration: {len(frames)/FPS:.1f} seconds')
                print(f'✓ Resolution: 1920x1080 @ {FPS}fps')
                print('=' * 60)
                print('\nCamera Features Implemented:')
                print('  • Smooth 360° rotational camera movements')
                print('  • Dynamic elevation changes (15°-40°)')
                print('  • Fluid perspective transitions')
                print('  • Synchronized content flow')
                print('  • Multi-surface visualization')
        except Exception as e:
            print(f'✗ Video composition failed: {e}')
            print(f'✓ Frames saved to: {frames_dir}')

def main():
    video = Enhanced3DVideo()
    frames = video.generate_all_frames()
    video.save_video(frames, 'media/videos/enhanced_3d/1080p30/CAPM_Enhanced_3D.mp4')

if __name__ == '__main__':
    main()
