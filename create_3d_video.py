import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import imageio_ffmpeg
import subprocess

WIDTH, HEIGHT = 1920, 1080
FPS = 30
BG_COLOR = (11, 15, 26)
TEXT_COLOR = (234, 236, 239)
MUTED_COLOR = (154, 164, 178)
ACCENT_COLOR = (64, 169, 255)

def get_font(size):
    try:
        return ImageFont.truetype("msyh.ttc", size)
    except:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

def create_3d_visualization(frame_num, scene_type):
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    if scene_type == 'intro':
        draw.text((WIDTH//2, 300), '民航旅客运输量预测模型', 
                   font=get_font(64), fill=TEXT_COLOR, anchor='mm')
        draw.text((WIDTH//2, 400), '3D 科学演示视频', 
                   font=get_font(36), fill=MUTED_COLOR, anchor='mm')
        draw.text((WIDTH//2, 500), '核心数学原理可视化', 
                   font=get_font(28), fill=ACCENT_COLOR, anchor='mm')
    
    elif scene_type == 'linear':
        draw.text((WIDTH//2, 100), '线性回归模型', 
                   font=get_font(48), fill=TEXT_COLOR, anchor='mt')
        draw.text((WIDTH//2, 170), 'y = β₀ + β₁x', 
                   font=get_font(32), fill=MUTED_COLOR, anchor='mt')
        
        grid_size = 50
        for i in range(20):
            y = 300 + i * 30
            draw.line((200, y, WIDTH-200, y, fill=(43, 58, 85), width=1)
            x = 200 + i * 80
            draw.line((x, 300, x, HEIGHT-200, fill=(43, 58, 85), width=1)
        
        x_points = np.linspace(200, WIDTH-200, 100)
        y_points = HEIGHT//2 - 200 * np.sin((x_points - 200) / 300 * np.pi)
        
        points = list(zip(x_points.astype(int), y_points.astype(int)))
        for i in range(len(points)-1):
            draw.line((points[i], points[i+1], fill=(92, 219, 211), width=4)
    
    elif scene_type == 'holtwinters':
        draw.text((WIDTH//2, 100), 'Holt-Winters 指数平滑', 
                   font=get_font(48), fill=TEXT_COLOR, anchor='mt')
        draw.text((WIDTH//2, 170), '水平(L) + 趋势(T) + 季节性(S)', 
                   font=get_font(28), fill=MUTED_COLOR, anchor='mt')
        
        for wave1 = [(300 + 200 * np.sin(np.linspace(0, 4*np.pi, 100))
        for i, y in enumerate(wave1):
            x = 200 + i * 15
            if 0 <= y < HEIGHT:
                draw.ellipse((x-3, int(y+3, x+3, int(y-3, fill=(179, 127, 235))
    
    elif scene_type == 'sarima':
        draw.text((WIDTH//2, 100), 'SARIMA 模型', 
                   font=get_font(48), fill=TEXT_COLOR, anchor='mt')
        draw.text((WIDTH//2, 170), '季节性自回归综合移动平均', 
                   font=get_font(28), fill=MUTED_COLOR, anchor='mt')
        
        for i in range(12):
            x = 200 + i * 130
            y = 500 + 150 * np.sin(i * 0.8)
            draw.ellipse((x-8, y-8, x+8, y+8, fill=(255, 133, 192))
            if i > 0:
                prev_x = 200 + (i-1) * 130
                prev_y = 500 + 150 * np.sin((i-1) * 0.8)
                draw.line((prev_x, prev_y, x, y, fill=(255, 133, 192), width=3)
    
    elif scene_type == 'ensemble':
        draw.text((WIDTH//2, 100), '模型加权融合', 
                   font=get_font(48), fill=TEXT_COLOR, anchor='mt')
        draw.text((WIDTH//2, 170), 'ŷ = 0.4×HW + 0.3×SARIMA + 0.3×Linear', 
                   font=get_font(28), fill=MUTED_COLOR, anchor='mt')
        
        colors = [(92, 219, 211), (179, 127, 235), (255, 133, 192), (115, 209, 61)]
        labels = ['Linear', 'Holt-Winters', 'SARIMA', 'Ensemble']
        
        for i, (color, label) in enumerate(zip(colors, labels)):
            x = 300
            y = 300 + i * 80
            draw.rectangle((x, y, x+60, y+40), fill=color)
            draw.text((x+80, y+20), label, font=get_font(24), fill=TEXT_COLOR, anchor='lm')
    
    elif scene_type == 'holiday':
        draw.text((WIDTH//2, 100), '节假日效应修正', 
                   font=get_font(48), fill=TEXT_COLOR, anchor='mt')
        draw.text((WIDTH//2, 170), '系数 = 1 + (春运天数/月天数) × (效应-1)', 
                   font=get_font(28), fill=MUTED_COLOR, anchor='mt')
        
        months = ['1月', '2月', '3月', '4月', '5月', '6月', 
                  '7月', '8月', '9月', '10月', '11月', '12月']
        effects = [1.12, 1.15, 1.08, 1.0, 1.0, 1.0, 
                   1.10, 1.10, 1.0, 1.08, 1.0, 1.0]
        
        for i, (month, effect) in enumerate(zip(months, effects)):
            x = 150 + i * 140
            bar_height = int((effect - 0.95) * 1000)
            draw.rectangle((x, HEIGHT-150-bar_height, x+100, HEIGHT-150), 
                          fill=(255, 169, 64), alpha=0.8)
            draw.text((x+50, HEIGHT-130), month, font=get_font(20), fill=MUTED_COLOR, anchor='mt')
    
    elif scene_type == 'summary':
        draw.text((WIDTH//2, 300), '总结', 
                   font=get_font(72), fill=TEXT_COLOR, anchor='mm')
        draw.text((WIDTH//2, 420), '可解释的预测流水线', 
                   font=get_font(40), fill=MUTED_COLOR, anchor='mm')
        
        steps = ['数据预处理', '时间序列构建', '三模型预测', '加权融合', '节假日修正', '增长率校准', '结果输出']
        for i, step in enumerate(steps):
            y = 520 + i * 45
            draw.text((WIDTH//2, y), '• ' + step, font=get_font(28), fill=ACCENT_COLOR, anchor='mm')
    
    return img

def generate_frames():
    print('=' * 60)
    print('生成 3D 教学视频')
    print('=' * 60)
    
    frames = []
    
    scenes = [
        ('intro', 90),
        ('linear', 90),
        ('holtwinters', 90),
        ('sarima', 90),
        ('ensemble', 90),
        ('holiday', 90),
        ('summary', 60),
    ]
    
    total_frames = sum(count for _, count in scenes)
    current = 0
    
    for scene_type, count in scenes:
        print(f'  生成 {scene_type}...')
        for i in range(count):
            frames.append(create_3d_visualization(i, scene_type))
            current += 1
            if current % 30 == 0:
                print(f'    进度: {current}/{total_frames}')
    
    print(f'✓ 共生成 {len(frames)} 帧')
    return frames

def save_video(frames, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    frames_dir = output_path.parent / '3d_frames'
    frames_dir.mkdir(exist_ok=True)
    
    print(f'  保存帧图片...')
    for i, frame in enumerate(frames):
        frame.save(frames_dir / f'frame_{i:04d}.png')
    
    print(f'  合成视频...')
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
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
    frames = generate_frames()
    save_video(frames, 'media/videos/3d_demo/1080p30/CAPM_3D_Demo.mp4')

if __name__ == '__main__':
    main()
