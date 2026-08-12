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

def draw_centered_text(draw, y, text, size=48, color=TEXT_COLOR):
    font = get_font(size)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (WIDTH - text_width) // 2
    draw.text((x, y), text, font=font, fill=color)
    return y + bbox[3] - bbox[1] + 10

def create_intro_frame():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    y = 300
    y = draw_centered_text(draw, y, '民航旅客运输量预测模型', 64)
    y = draw_centered_text(draw, y + 40, '3D 科学演示视频', 36, MUTED_COLOR)
    y = draw_centered_text(draw, y + 40, '核心数学原理可视化', 28, ACCENT_COLOR)
    
    return img

def create_linear_frame():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    y = 80
    y = draw_centered_text(draw, y, '线性回归模型', 48)
    y = draw_centered_text(draw, y + 20, 'y = β₀ + β₁x', 32, MUTED_COLOR)
    
    for i in range(15):
        draw.line((200, 300 + i * 50, WIDTH-200, 300 + i * 50), fill=(43, 58, 85), width=1)
        draw.line((200 + i * 110, 300, 200 + i * 110, HEIGHT-200), fill=(43, 58, 85), width=1)
    
    x_points = np.linspace(200, WIDTH-200, 50)
    y_points = HEIGHT//2 - 150 * np.sin((x_points - 200) / 400 * np.pi)
    
    points = list(zip(x_points.astype(int), y_points.astype(int)))
    for i in range(len(points)-1):
        draw.line((points[i], points[i+1]), fill=(92, 219, 211), width=5)
    
    return img

def create_holtwinters_frame():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    y = 80
    y = draw_centered_text(draw, y, 'Holt-Winters 指数平滑', 48)
    y = draw_centered_text(draw, y + 20, '水平(L) + 趋势(T) + 季节性(S)', 28, MUTED_COLOR)
    
    x_points = np.linspace(200, WIDTH-200, 100)
    y_points = HEIGHT//2 - 200 * np.sin((x_points - 200) / 200 * np.pi)
    
    for i, y_val in enumerate(y_points):
        x = int(x_points[i])
        draw.ellipse((x-4, y_val-4, x+4, y_val+4), fill=(179, 127, 235))
    
    return img

def create_sarima_frame():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    y = 80
    y = draw_centered_text(draw, y, 'SARIMA 模型', 48)
    y = draw_centered_text(draw, y + 20, '季节性自回归综合移动平均', 28, MUTED_COLOR)
    
    for i in range(12):
        x = 200 + i * 130
        y_val = 500 + 180 * np.sin(i * 0.7)
        draw.ellipse((x-10, y_val-10, x+10, y_val+10), fill=(255, 133, 192))
        if i > 0:
            prev_x = 200 + (i-1) * 130
            prev_y = 500 + 180 * np.sin((i-1) * 0.7)
            draw.line((prev_x, prev_y, x, y_val), fill=(255, 133, 192), width=4)
    
    return img

def create_ensemble_frame():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    y = 80
    y = draw_centered_text(draw, y, '模型加权融合', 48)
    y = draw_centered_text(draw, y + 20, 'ŷ = 0.4×HW + 0.3×SARIMA + 0.3×Linear', 28, MUTED_COLOR)
    
    colors = [(92, 219, 211), (179, 127, 235), (255, 133, 192), (115, 209, 61)]
    labels = ['Linear', 'Holt-Winters', 'SARIMA', 'Ensemble']
    
    for i, (color, label) in enumerate(zip(colors, labels)):
        x = 350
        y_val = 320 + i * 100
        draw.rectangle((x, y_val, x+80, y_val+50), fill=color)
        draw.text((x+100, y_val+15), label, font=get_font(28), fill=TEXT_COLOR)
    
    return img

def create_holiday_frame():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    y = 80
    y = draw_centered_text(draw, y, '节假日效应修正', 48)
    y = draw_centered_text(draw, y + 20, '系数 = 1 + (春运天数/月天数) × (效应-1)', 28, MUTED_COLOR)
    
    months = ['1月', '2月', '3月', '4月', '5月', '6月', 
              '7月', '8月', '9月', '10月', '11月', '12月']
    effects = [1.12, 1.15, 1.08, 1.0, 1.0, 1.0, 
               1.10, 1.10, 1.0, 1.08, 1.0, 1.0]
    
    for i, (month, effect) in enumerate(zip(months, effects)):
        x = 120 + i * 145
        bar_height = int((effect - 0.95) * 1200)
        draw.rectangle((x, HEIGHT-180-bar_height, x+110, HEIGHT-180), 
                      fill=(255, 169, 64))
        draw.text((x+55, HEIGHT-160), month, font=get_font(22), fill=MUTED_COLOR)
    
    return img

def create_summary_frame():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    y = 280
    y = draw_centered_text(draw, y, '总结', 72)
    y = draw_centered_text(draw, y + 30, '可解释的预测流水线', 40, MUTED_COLOR)
    
    steps = ['数据预处理', '时间序列构建', '三模型预测', '加权融合', '节假日修正', '增长率校准', '结果输出']
    for i, step in enumerate(steps):
        y_val = 480 + i * 50
        draw_centered_text(draw, y_val, '• ' + step, 28, ACCENT_COLOR)
    
    return img

def generate_frames():
    print('=' * 60)
    print('生成 3D 教学视频')
    print('=' * 60)
    
    frames = []
    
    scenes = [
        (create_intro_frame, 90),
        (create_linear_frame, 90),
        (create_holtwinters_frame, 90),
        (create_sarima_frame, 90),
        (create_ensemble_frame, 90),
        (create_holiday_frame, 90),
        (create_summary_frame, 60),
    ]
    
    total_frames = sum(count for _, count in scenes)
    current = 0
    
    for create_func, count in scenes:
        print(f'  生成场景...')
        for i in range(count):
            frames.append(create_func())
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
