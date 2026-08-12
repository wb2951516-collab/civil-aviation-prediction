import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, FancyBboxPatch
from pathlib import Path
import sys

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

BG_COLOR = '#0B0F1A'
TEXT_COLOR = '#EAECEF'
MUTED_COLOR = '#9AA4B2'
ACCENT_COLOR = '#40A9FF'
MODEL_COLORS = {
    'Linear': '#5CDBD3',
    'Holt-Winters': '#B37FEB',
    'SARIMA': '#FF85C0',
    'Ensemble': '#73D13D'
}

FIGSIZE = (19.2, 10.8)
DPI = 100
FPS = 30

class ScienceDemoVideo:
    def __init__(self, output_path='media/videos/alternative/1080p30/CAPM_Alternative.mp4'):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.fig = None
        self.artists = []
        self.current_frame = 0
        
    def create_figure(self):
        self.fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor=BG_COLOR)
        self.fig.patch.set_facecolor(BG_COLOR)
        return self.fig
    
    def clear_frame(self):
        if self.fig:
            self.fig.clear()
    
    def add_title(self, text, subtitle=None):
        ax = self.fig.add_axes([0.1, 0.85, 0.8, 0.1])
        ax.axis('off')
        ax.set_facecolor(BG_COLOR)
        title = ax.text(0.5, 0.6, text, ha='center', va='center', 
                       fontsize=42, color=TEXT_COLOR, fontweight='bold')
        if subtitle:
            sub = ax.text(0.5, 0.2, subtitle, ha='center', va='center', 
                         fontsize=24, color=MUTED_COLOR)
            return [title, sub]
        return [title]
    
    def add_pipeline(self, steps):
        ax = self.fig.add_axes([0.05, 0.4, 0.9, 0.4])
        ax.axis('off')
        ax.set_facecolor(BG_COLOR)
        
        n_steps = len(steps)
        box_width = 0.9 / n_steps - 0.02
        boxes = []
        
        for i, (title, subtitle) in enumerate(steps):
            x = 0.05 + i * (box_width + 0.02)
            box = FancyBboxPatch((x, 0.1), box_width, 0.6, 
                                 boxstyle="round,pad=0.02", 
                                 facecolor='#121826', edgecolor=ACCENT_COLOR, 
                                 linewidth=2)
            ax.add_patch(box)
            boxes.append(box)
            
            t1 = ax.text(x + box_width/2, 0.5, title, ha='center', va='center',
                        fontsize=20, color=TEXT_COLOR)
            t2 = ax.text(x + box_width/2, 0.3, subtitle, ha='center', va='center',
                        fontsize=14, color=MUTED_COLOR)
            boxes.extend([t1, t2])
        
        return boxes
    
    def add_chart(self, data_dict):
        ax = self.fig.add_axes([0.1, 0.15, 0.75, 0.55])
        ax.set_facecolor(BG_COLOR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(MUTED_COLOR)
        ax.spines['left'].set_color(MUTED_COLOR)
        ax.tick_params(axis='x', colors=MUTED_COLOR, labelsize=12)
        ax.tick_params(axis='y', colors=MUTED_COLOR, labelsize=12)
        
        months = np.arange(1, 13)
        lines = []
        
        for name, data in data_dict.items():
            if name in MODEL_COLORS:
                line, = ax.plot(months, data, color=MODEL_COLORS[name], 
                               linewidth=3, label=name)
                lines.append(line)
        
        ax.set_xlabel('月份', color=MUTED_COLOR, fontsize=14)
        ax.set_ylabel('旅客运输量', color=MUTED_COLOR, fontsize=14)
        ax.set_xticks(months)
        ax.legend(loc='upper right', facecolor=BG_COLOR, edgecolor=MUTED_COLOR, 
                 labelcolor=TEXT_COLOR, fontsize=12)
        
        return lines
    
    def add_formula(self, formula_text, x=0.5, y=0.25):
        ax = self.fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.set_facecolor('none')
        text = ax.text(x, y, formula_text, ha='center', va='center',
                      fontsize=28, color=MUTED_COLOR,
                      bbox=dict(facecolor='#121826', edgecolor=MUTED_COLOR, 
                               boxstyle='round,pad=0.3'))
        return [text]
    
    def generate_sample_data(self):
        np.random.seed(42)
        base = 7000 + np.sin(np.linspace(0, 4*np.pi, 12)) * 800
        linear = base + np.linspace(0, 600, 12)
        hw = base + np.sin(np.linspace(0, 3*np.pi, 12)) * 400
        sarima = base + np.cos(np.linspace(0, 5*np.pi, 12)) * 300
        ensemble = 0.4 * hw + 0.3 * sarima + 0.3 * linear
        return {
            'Linear': linear,
            'Holt-Winters': hw,
            'SARIMA': sarima,
            'Ensemble': ensemble
        }
    
    def create_frames(self):
        frames = []
        
        data = self.generate_sample_data()
        
        self.create_figure()
        self.add_title('民航旅客运输量预测模型', '科学演示视频 - 第二版')
        for _ in range(60):
            frames.append(np.array(self.fig.canvas.renderer.buffer_rgba()))
        self.clear_frame()
        
        self.create_figure()
        self.add_title('项目工作流程', '从数据到预测结果的完整链路')
        self.add_pipeline([
            ('数据输入', 'Excel/手动'),
            ('时间序列', '月频数据'),
            ('模型预测', '三模型并行'),
            ('融合修正', '加权/节假日'),
            ('结果输出', '表格/报告')
        ])
        for _ in range(90):
            frames.append(np.array(self.fig.canvas.renderer.buffer_rgba()))
        self.clear_frame()
        
        self.create_figure()
        self.add_title('核心预测模型', 'Linear / Holt-Winters / SARIMA')
        self.add_chart({k: v for k, v in data.items() if k != 'Ensemble'})
        for _ in range(90):
            frames.append(np.array(self.fig.canvas.renderer.buffer_rgba()))
        self.clear_frame()
        
        self.create_figure()
        self.add_title('模型融合', '加权集成学习')
        self.add_chart(data)
        self.add_formula('ŷ = 0.4×HW + 0.3×SARIMA + 0.3×Linear')
        for _ in range(90):
            frames.append(np.array(self.fig.canvas.renderer.buffer_rgba()))
        self.clear_frame()
        
        self.create_figure()
        self.add_title('节假日效应修正', '春运等特殊时期调整')
        self.add_formula('系数 = 1 + (春运天数/月天数) × (效应-1)', y=0.5)
        self.add_formula('预测值 = 原始值 × 效应系数', y=0.3)
        for _ in range(60):
            frames.append(np.array(self.fig.canvas.renderer.buffer_rgba()))
        self.clear_frame()
        
        self.create_figure()
        self.add_title('总结', '可解释的预测流水线')
        self.add_pipeline([
            ('数据', '预处理'),
            ('模型', '预测'),
            ('修正', '优化'),
            ('输出', '应用')
        ])
        for _ in range(60):
            frames.append(np.array(self.fig.canvas.renderer.buffer_rgba()))
        
        plt.close(self.fig)
        return frames
    
    def render(self):
        print('=' * 60)
        print('开始生成第二版视频（Matplotlib 版本）')
        print('=' * 60)
        
        frames = self.create_frames()
        
        print(f'✓ 共生成 {len(frames)} 帧')
        print(f'✓ 预计时长: {len(frames)/FPS:.1f} 秒')
        
        try:
            import matplotlib.animation as animation
            from matplotlib.animation import FFMpegWriter
            
            self.create_figure()
            
            def update_frame(i):
                pass
            
            writer = FFMpegWriter(fps=FPS, codec='libx264', 
                                  bitrate='5000k', 
                                  extra_args=['-pix_fmt', 'yuv420p'])
            
            fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor=BG_COLOR)
            
            with writer.saving(fig, str(self.output_path), DPI):
                for i, frame in enumerate(frames):
                    if i % 30 == 0:
                        print(f'  处理进度: {i/len(frames)*100:.1f}% ({i}/{len(frames)})')
                    ax = fig.add_axes([0, 0, 1, 1])
                    ax.axis('off')
                    ax.imshow(frame)
                    writer.grab_frame()
                    fig.clear()
            
            plt.close(fig)
            
            size_mb = self.output_path.stat().st_size / (1024 * 1024)
            print('=' * 60)
            print('✓ 第二版视频生成成功！')
            print(f'✓ 输出文件: {self.output_path.resolve()}')
            print(f'✓ 文件大小: {size_mb:.2f} MB')
            print('=' * 60)
            
        except Exception as e:
            print(f'✗ 视频合成失败: {e}')
            print('正在保存帧为图片序列...')
            
            frame_dir = self.output_path.parent / 'frames'
            frame_dir.mkdir(exist_ok=True)
            
            from PIL import Image
            for i, frame in enumerate(frames):
                img = Image.fromarray(frame)
                img.save(frame_dir / f'frame_{i:04d}.png')
            
            print(f'✓ 帧已保存到: {frame_dir}')
            print('提示: 使用 FFmpeg 合成:')
            print(f'ffmpeg -framerate {FPS} -i {frame_dir}/frame_%04d.png -c:v libx264 -pix_fmt yuv420p {self.output_path}')

if __name__ == '__main__':
    video = ScienceDemoVideo()
    video.render()
