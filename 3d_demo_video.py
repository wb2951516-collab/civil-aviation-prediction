import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation, FFMpegWriter
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

WIDTH, HEIGHT = 1920, 1080
DPI = 100
FPS = 30
TOTAL_FRAMES = 600

class ThreeDDemoVideo:
    def __init__(self):
        self.frames = []
        self.current_frame = 0
        
    def create_3d_surface(self, ax, title, subtitle, z_func, angle=0):
        ax.clear()
        ax.set_facecolor('#0B0F1A')
        
        X = np.linspace(-5, 5, 50)
        Y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(X, Y)
        Z = z_func(X, Y)
        
        surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8, 
                              linewidth=0, antialiased=True)
        ax.set_xlabel('维度 X', color='#9AA4B2', fontsize=12)
        ax.set_ylabel('维度 Y', color='#9AA4B2', fontsize=12)
        ax.set_zlabel('预测值 Z', color='#9AA4B2', fontsize=12)
        ax.tick_params(axis='x', colors='#9AA4B2')
        ax.tick_params(axis='y', colors='#9AA4B2')
        ax.tick_params(axis='z', colors='#9AA4B2')
        
        ax.view_init(elev=30 + angle * 0.3, azim=45 + angle)
        
        return surf
    
    def generate_sample_data(self):
        np.random.seed(42)
        months = np.arange(12)
        base = 7000 + np.sin(np.linspace(0, 4*np.pi, 12)) * 800
        data = {
            'Linear': base + np.linspace(0, 600, 12),
            'Holt-Winters': base + np.sin(np.linspace(0, 3*np.pi, 12)) * 400,
            'SARIMA': base + np.cos(np.linspace(0, 5*np.pi, 12)) * 300
        }
        data['Ensemble'] = 0.4 * data['Holt-Winters'] + 0.3 * data['SARIMA'] + 0.3 * data['Linear']
        return months, data
    
    def create_frame_intro(self, frame_num):
        fig = plt.figure(figsize=(WIDTH/100, HEIGHT/100), dpi=100, facecolor='#0B0F1A')
        fig.patch.set_facecolor('#0B0F1A')
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.set_facecolor('#0B0F1A')
        
        ax.text(0.5, 0.6, '民航旅客运输量预测模型', 
                ha='center', va='center', 
                fontsize=48, color='#EAECEF', 
                transform=ax.transAxes, fontweight='bold')
        ax.text(0.5, 0.45, '3D 科学演示视频', 
                ha='center', va='center', 
                fontsize=28, color='#9AA4B2', 
                transform=ax.transAxes)
        ax.text(0.5, 0.3, '核心数学原理可视化', 
                ha='center', va='center', 
                fontsize=24, color='#40A9FF', 
                transform=ax.transAxes)
        
        fig.canvas.draw()
        frame = np.array(fig.canvas.renderer.buffer_rgba())
        plt.close(fig)
        return frame
    
    def create_frame_3d_linear(self, frame_num):
        fig = plt.figure(figsize=(WIDTH/100, HEIGHT/100), dpi=100, facecolor='#0B0F1A')
        fig.patch.set_facecolor('#0B0F1A')
        
        ax = fig.add_subplot(111, projection='3d')
        
        def linear_func(X, Y):
            return 7000 + 100*X + 50*Y
        
        self.create_3d_surface(ax, '线性回归模型', 'y = intercept + slope·x', 
                                 linear_func, frame_num)
        
        ax.text2D(0.5, 0.95, '线性回归模型', transform=ax.transAxes, 
                ha='center', fontsize=24, color='#EAECEF', fontweight='bold')
        ax.text2D(0.5, 0.90, 'y = β₀ + β₁x + β₂y', transform=ax.transAxes, 
                ha='center', fontsize=18, color='#9AA4B2')
        
        fig.canvas.draw()
        frame = np.array(fig.canvas.renderer.buffer_rgba())
        plt.close(fig)
        return frame
    
    def create_frame_3d_holtwinters(self, frame_num):
        fig = plt.figure(figsize=(WIDTH/100, HEIGHT/100), dpi=100, facecolor='#0B0F1A')
        fig.patch.set_facecolor('#0B0F1A')
        
        ax = fig.add_subplot(111, projection='3d')
        
        def hw_func(X, Y):
            seasonal = np.sin(X * 0.5) * 500
            trend = Y * 80
            return 7000 + seasonal + trend
        
        self.create_3d_surface(ax, 'Holt-Winters模型', '三重要素：水平/趋势/季节', 
                                 hw_func, frame_num)
        
        ax.text2D(0.5, 0.95, 'Holt-Winters 指数平滑', transform=ax.transAxes, 
                ha='center', fontsize=24, color='#EAECEF', fontweight='bold')
        ax.text2D(0.5, 0.90, '水平(L) + 趋势(T) + 季节性(S)', transform=ax.transAxes, 
                ha='center', fontsize=18, color='#9AA4B2')
        
        fig.canvas.draw()
        frame = np.array(fig.canvas.renderer.buffer_rgba())
        plt.close(fig)
        return frame
    
    def create_frame_3d_sarima(self, frame_num):
        fig = plt.figure(figsize=(WIDTH/100, HEIGHT/100), dpi=100, facecolor='#0B0F1A')
        fig.patch.set_facecolor('#0B0F1A')
        
        ax = fig.add_subplot(111, projection='3d')
        
        def sarima_func(X, Y):
            ar = np.sin(X*0.8) * 600
            ma = np.cos(Y*0.6) * 400
            seasonal = np.sin((X+Y)*0.3) * 300
            return 7000 + ar + ma + seasonal
        
        self.create_3d_surface(ax, 'SARIMA模型', '季节性ARIMA', 
                                 sarima_func, frame_num)
        
        ax.text2D(0.5, 0.95, 'SARIMA 模型', transform=ax.transAxes, 
                ha='center', fontsize=24, color='#EAECEF', fontweight='bold')
        ax.text2D(0.5, 0.90, '季节性自回归综合移动平均', transform=ax.transAxes, 
                ha='center', fontsize=18, color='#9AA4B2')
        
        fig.canvas.draw()
        frame = np.array(fig.canvas.renderer.buffer_rgba())
        plt.close(fig)
        return frame
    
    def create_frame_ensemble(self, frame_num):
        fig = plt.figure(figsize=(WIDTH/100, HEIGHT/100), dpi=100, facecolor='#0B0F1A')
        fig.patch.set_facecolor('#0B0F1A')
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.set_facecolor('#0B0F1A')
        
        months, data = self.generate_sample_data()
        
        colors = ['#5CDBD3', '#B37FEB', '#FF85C0', '#73D13D']
        labels = ['Linear', 'Holt-Winters', 'SARIMA', 'Ensemble']
        
        for i, (name, values) in enumerate(data.items()):
            ax.plot(months, values, color=colors[i], linewidth=3, label=labels[i], alpha=0.8)
        
        ax.scatter(months, data['Ensemble'], color='#73D13D', s=80, zorder=5)
        
        ax.set_xlabel('月份', color='#9AA4B2', fontsize=16)
        ax.set_ylabel('旅客运输量', color='#9AA4B2', fontsize=16)
        ax.tick_params(axis='x', colors='#9AA4B2')
        ax.tick_params(axis='y', colors='#9AA4B2')
        ax.legend(loc='upper right', facecolor='#121826', edgecolor='#2B3A55', 
                 labelcolor='#EAECEF', fontsize=14)
        ax.grid(True, alpha=0.2, color='#2B3A55')
        
        ax.text(0.5, 0.95, '模型加权融合', ha='center', va='top', 
                fontsize=28, color='#EAECEF', 
                transform=ax.transAxes, fontweight='bold')
        ax.text(0.5, 0.88, 'ŷ = 0.4×HW + 0.3×SARIMA + 0.3×Linear', ha='center', 
                fontsize=20, color='#9AA4B2', transform=ax.transAxes)
        
        fig.canvas.draw()
        frame = np.array(fig.canvas.renderer.buffer_rgba())
        plt.close(fig)
        return frame
    
    def create_frame_holiday(self, frame_num):
        fig = plt.figure(figsize=(WIDTH/100, HEIGHT/100), dpi=100, facecolor='#0B0F1A')
        fig.patch.set_facecolor('#0B0F1A')
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.set_facecolor('#0B0F1A')
        
        months = ['1月', '2月', '3月', '4月', '5月', '6月', 
                  '7月', '8月', '9月', '10月', '11月', '12月']
        effect = np.ones(12)
        effect[0] = 1.12
        effect[1] = 1.15
        effect[2] = 1.08
        effect[6] = 1.10
        effect[7] = 1.10
        effect[9] = 1.08
        
        bars = ax.bar(range(12), effect, color='#FFA940', alpha=0.8)
        ax.axhline(y=1.0, color='#40A9FF', linestyle='--', linewidth=2, alpha=0.5)
        
        ax.set_xticks(range(12))
        ax.set_xticklabels(months, color='#9AA4B2', fontsize=12)
        ax.set_ylabel('效应系数', color='#9AA4B2', fontsize=16)
        ax.tick_params(axis='y', colors='#9AA4B2')
        ax.set_ylim(0.95, 1.20)
        ax.grid(True, alpha=0.2, color='#2B3A55')
        
        ax.text(0.5, 0.95, '节假日效应修正', ha='center', va='top', 
                fontsize=28, color='#EAECEF', 
                transform=ax.transAxes, fontweight='bold')
        ax.text(0.5, 0.88, '系数 = 1 + (春运天数/月天数) × (效应-1)', ha='center', 
                fontsize=20, color='#9AA4B2', transform=ax.transAxes)
        
        fig.canvas.draw()
        frame = np.array(fig.canvas.renderer.buffer_rgba())
        plt.close(fig)
        return frame
    
    def create_frame_summary(self, frame_num):
        fig = plt.figure(figsize=(WIDTH/100, HEIGHT/100), dpi=100, facecolor='#0B0F1A')
        fig.patch.set_facecolor('#0B0F1A')
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.set_facecolor('#0B0F1A')
        
        ax.text(0.5, 0.6, '总结', 
                ha='center', va='center', 
                fontsize=56, color='#EAECEF', 
                transform=ax.transAxes, fontweight='bold')
        ax.text(0.5, 0.5, '可解释的预测流水线', 
                ha='center', va='center', 
                fontsize=32, color='#9AA4B2', 
                transform=ax.transAxes)
        
        steps = ['数据预处理', '时间序列构建', '三模型预测', '加权融合', '节假日修正', '增长率校准', '结果输出']
        for i, step in enumerate(steps):
            y = 0.4 - i * 0.06
            ax.text(0.5, y, f'• {step}', ha='center', va='center', 
                    fontsize=22, color='#40A9FF', transform=ax.transAxes)
        
        fig.canvas.draw()
        frame = np.array(fig.canvas.renderer.buffer_rgba())
        plt.close(fig)
        return frame
    
    def generate_all_frames(self):
        print('=' * 60)
        print('生成 3D 教学视频帧')
        print('=' * 60)
        
        frames = []
        
        print('  生成介绍...')
        for i in range(90):
            frames.append(self.create_frame_intro(i))
        
        print('  生成线性回归 3D...')
        for i in range(90):
            frames.append(self.create_frame_3d_linear(i))
        
        print('  生成 Holt-Winters 3D...')
        for i in range(90):
            frames.append(self.create_frame_3d_holtwinters(i))
        
        print('  生成 SARIMA 3D...')
        for i in range(90):
            frames.append(self.create_frame_3d_sarima(i))
        
        print('  生成融合模型...')
        for i in range(90):
            frames.append(self.create_frame_ensemble(i))
        
        print('  生成节假日效应...')
        for i in range(90):
            frames.append(self.create_frame_holiday(i))
        
        print('  生成总结...')
        for i in range(60):
            frames.append(self.create_frame_summary(i))
        
        print(f'✓ 共生成 {len(frames)} 帧')
        return frames
    
    def save_video(self, frames, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        from PIL import Image
        frames_dir = output_path.parent / '3d_frames'
        frames_dir.mkdir(exist_ok=True)
        
        print(f'  保存帧图片...')
        for i, frame in enumerate(frames):
            img = Image.fromarray(frame)
            img.save(frames_dir / f'frame_{i:04d}.png')
        
        print(f'  合成视频...')
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            import subprocess
            cmd = [
                ffmpeg_exe,
                '-y',
                '-framerate', str(FPS),
                '-i', str(frames_dir / 'frame_%04d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-crf', '23',
                str(output_path)
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                print('=' * 60)
                print('✓ 3D 教学视频生成成功！')
                print(f'✓ 文件: {output_path.resolve()}')
                print(f'✓ 大小: {size_mb:.2f} MB')
                print(f'✓ 时长: {len(frames)/FPS:.1f} 秒')
                print('=' * 60)
        except Exception as e:
            print(f'✗ 视频合成失败: {e}')
            print(f'✓ 帧已保存到: {frames_dir}')

def main():
    video = ThreeDDemoVideo()
    frames = video.generate_all_frames()
    video.save_video(frames, 'media/videos/3d_demo/1080p30/CAPM_3D_Demo.mp4')

if __name__ == '__main__':
    main()
