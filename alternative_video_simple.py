import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import subprocess
import sys

WIDTH, HEIGHT = 1920, 1080
BG_COLOR = (11, 15, 26)
TEXT_COLOR = (234, 236, 239)
MUTED_COLOR = (154, 164, 178)
ACCENT_COLOR = (64, 169, 255)
MODEL_COLORS = {
    'Linear': (92, 219, 211),
    'Holt-Winters': (179, 127, 235),
    'SARIMA': (255, 133, 192),
    'Ensemble': (115, 209, 61)
}

FPS = 30

def get_font(size):
    try:
        return ImageFont.truetype("msyh.ttc", size)
    except:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

def draw_centered_text(draw, y, text, font_size=42, color=TEXT_COLOR, bold=False):
    font = get_font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (WIDTH - text_width) // 2
    draw.text((x, y), text, font=font, fill=color)
    return y + bbox[3] - bbox[1] + 20

def draw_box(draw, x, y, width, height, title, subtitle, fill=(18, 24, 38), outline=ACCENT_COLOR):
    draw.rectangle([x, y, x+width, y+height], fill=fill, outline=outline, width=3)
    font_title = get_font(24)
    font_sub = get_font(18)
    bbox_t = draw.textbbox((0, 0), title, font=font_title)
    tx = x + (width - (bbox_t[2]-bbox_t[0])) // 2
    ty = y + height//3 - (bbox_t[3]-bbox_t[1])//2
    draw.text((tx, ty), title, font=font_title, fill=TEXT_COLOR)
    bbox_s = draw.textbbox((0, 0), subtitle, font=font_sub)
    sx = x + (width - (bbox_s[2]-bbox_s[0]))//2
    sy = y + height*2//3 - (bbox_s[3]-bbox_s[1])//2
    draw.text((sx, sy), subtitle, font=font_sub, fill=MUTED_COLOR)

def create_frame_intro():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    y = 300
    y = draw_centered_text(draw, y, "民航旅客运输量预测模型", font_size=64, bold=True)
    y = draw_centered_text(draw, y + 40, "科学演示视频 - 第二版", font_size=36, color=MUTED_COLOR)
    return img

def create_frame_pipeline():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_centered_text(draw, 80, "项目工作流程", font_size=48, bold=True)
    draw_centered_text(draw, 150, "从数据到预测结果的完整链路", font_size=28, color=MUTED_COLOR)
    steps = [
        ("数据输入", "Excel/手动"),
        ("时间序列", "月频数据"),
        ("模型预测", "三模型并行"),
        ("融合修正", "加权/节假日"),
        ("结果输出", "表格/报告")
    ]
    box_w = 320
    box_h = 150
    spacing = 40
    start_x = (WIDTH - (len(steps)*box_w + (len(steps)-1)*spacing)) // 2
    y = 300
    for i, (title, sub) in enumerate(steps):
        x = start_x + i*(box_w + spacing)
        draw_box(draw, x, y, box_w, box_h, title, sub)
    return img

def create_frame_models():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_centered_text(draw, 80, "核心预测模型", font_size=48, bold=True)
    draw_centered_text(draw, 150, "Linear / Holt-Winters / SARIMA", font_size=28, color=MUTED_COLOR)
    chart_x, chart_y = 200, 250
    chart_w, chart_h = 1520, 600
    draw.rectangle([chart_x, chart_y, chart_x+chart_w, chart_y+chart_h], 
                  fill=(15, 22, 36), outline=(43, 58, 85), width=2)
    months = np.arange(12)
    np.random.seed(42)
    base = 7000 + np.sin(np.linspace(0, 4*np.pi, 12)) * 800
    data = {
        'Linear': base + np.linspace(0, 600, 12),
        'Holt-Winters': base + np.sin(np.linspace(0, 3*np.pi, 12)) * 400,
        'SARIMA': base + np.cos(np.linspace(0, 5*np.pi, 12)) * 300
    }
    y_min, y_max = 6000, 8500
    x_scale = chart_w / 11
    y_scale = chart_h / (y_max - y_min)
    for name, values in data.items():
        color = MODEL_COLORS[name]
        points = []
        for i, val in enumerate(values):
            x = chart_x + i * x_scale
            y = chart_y + chart_h - (val - y_min) * y_scale
            points.append((x, y))
        for i in range(len(points)-1):
            draw.line([points[i], points[i+1]], fill=color, width=4)
        for p in points:
            draw.ellipse([p[0]-6, p[1]-6, p[0]+6, p[1]+6], fill=color)
    legend_x, legend_y = 1500, 280
    for i, (name, color) in enumerate([(k, v) for k, v in MODEL_COLORS.items() if k != 'Ensemble']):
        ly = legend_y + i * 50
        draw.rectangle([legend_x, ly, legend_x+40, ly+30], fill=color)
        draw.text((legend_x+55, ly+5), name, font=get_font(24), fill=TEXT_COLOR)
    return img

def create_frame_ensemble():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_centered_text(draw, 80, "模型融合", font_size=48, bold=True)
    draw_centered_text(draw, 150, "加权集成学习", font_size=28, color=MUTED_COLOR)
    formula = "ŷ = 0.4×HW + 0.3×SARIMA + 0.3×Linear"
    box_w = 800
    box_h = 80
    box_x = (WIDTH - box_w) // 2
    box_y = 250
    draw.rectangle([box_x, box_y, box_x+box_w, box_y+box_h], 
                  fill=(18, 24, 38), outline=MUTED_COLOR, width=2)
    draw_centered_text(draw, box_y + 20, formula, font_size=32, color=MUTED_COLOR)
    return img

def create_frame_holiday():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_centered_text(draw, 80, "节假日效应修正", font_size=48, bold=True)
    draw_centered_text(draw, 150, "春运等特殊时期调整", font_size=28, color=MUTED_COLOR)
    formulas = [
        "系数 = 1 + (春运天数/月天数) × (效应-1)",
        "预测值 = 原始值 × 效应系数"
    ]
    for i, formula in enumerate(formulas):
        box_w = 700
        box_h = 70
        box_x = (WIDTH - box_w) // 2
        box_y = 300 + i * 120
        draw.rectangle([box_x, box_y, box_x+box_w, box_y+box_h], 
                      fill=(18, 24, 38), outline=MUTED_COLOR, width=2)
        draw_centered_text(draw, box_y + 18, formula, font_size=28, color=MUTED_COLOR)
    return img

def create_frame_summary():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_centered_text(draw, 80, "总结", font_size=48, bold=True)
    draw_centered_text(draw, 150, "可解释的预测流水线", font_size=28, color=MUTED_COLOR)
    steps = [
        ("数据", "预处理"),
        ("模型", "预测"),
        ("修正", "优化"),
        ("输出", "应用")
    ]
    box_w = 380
    box_h = 180
    spacing = 60
    start_x = (WIDTH - (len(steps)*box_w + (len(steps)-1)*spacing)) // 2
    y = 320
    for i, (title, sub) in enumerate(steps):
        x = start_x + i*(box_w + spacing)
        draw_box(draw, x, y, box_w, box_h, title, sub)
    return img

def generate_frames():
    frames = []
    frames.extend([create_frame_intro()] * 60)
    frames.extend([create_frame_pipeline()] * 90)
    frames.extend([create_frame_models()] * 90)
    frames.extend([create_frame_ensemble()] * 90)
    frames.extend([create_frame_holiday()] * 60)
    frames.extend([create_frame_summary()] * 60)
    return frames

def save_frames(frames, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        frame.save(output_dir / f"frame_{i:04d}.png")
    return output_dir

def create_video_with_ffmpeg(frames_dir, output_path, fps=FPS):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        cmd = [
            'ffmpeg', '-y',
            '-framerate', str(fps),
            '-i', str(frames_dir / 'frame_%04d.png'),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"FFmpeg 错误: {e}")
        return False

def main():
    print('=' * 60)
    print('开始生成第二版视频（PIL + FFmpeg）')
    print('=' * 60)
    
    frames = generate_frames()
    print(f'✓ 共生成 {len(frames)} 帧')
    print(f'✓ 预计时长: {len(frames)/FPS:.1f} 秒')
    
    frames_dir = Path('media/videos/alternative/frames')
    output_path = Path('media/videos/alternative/1080p30/CAPM_Alternative.mp4')
    
    print('\n正在保存帧...')
    save_frames(frames, frames_dir)
    print(f'✓ 帧已保存到: {frames_dir}')
    
    print('\n正在尝试使用 FFmpeg 合成视频...')
    success = create_video_with_ffmpeg(frames_dir, output_path)
    
    if success and output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print('=' * 60)
        print('✓ 第二版视频生成成功！')
        print(f'✓ 输出文件: {output_path.resolve()}')
        print(f'✓ 文件大小: {size_mb:.2f} MB')
        print('=' * 60)
    else:
        print('\n提示: FFmpeg 不可用或视频合成失败')
        print(f'✓ 帧图片已保存在: {frames_dir}')
        print('\n如需合成视频，请安装 FFmpeg 后运行:')
        print(f'ffmpeg -framerate {FPS} -i {frames_dir}/frame_%04d.png -c:v libx264 -pix_fmt yuv420p {output_path}')

if __name__ == '__main__':
    main()
