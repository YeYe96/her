#!/usr/bin/env python3
"""
临时脚本: 创建 Amadeus Logo 占位图
"""
from PIL import Image, ImageDraw, ImageFont

# 创建一个 512x512 的图像 (深色主题)
img = Image.new('RGB', (512, 512), color='#1a1a2e')

# 创建绘图对象
draw = ImageDraw.Draw(img)

# 绘制一个圆形边框
draw.ellipse([64, 64, 448, 448], outline='#16a085', width=8)

# 绘制文字 "A" (Amadeus 的首字母)
try:
    # 尝试使用系统字体
    font = ImageFont.truetype("arial.ttf", 280)
except:
    # 如果找不到字体,使用默认字体
    font = ImageFont.load_default()

# 计算文字位置 (居中)
text = "A"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (512 - text_width) // 2
y = (512 - text_height) // 2 - 20

# 绘制文字
draw.text((x, y), text, fill='#16a085', font=font)

# 保存图像
img.save('miniprogram/assets/amadeus_logo.png')
print("Logo placeholder created successfully: miniprogram/assets/amadeus_logo.png")
