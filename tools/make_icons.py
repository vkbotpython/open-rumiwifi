"""Рисует иконки расширения (без сторонних изображений).

Запуск: python tools/make_icons.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

SIZE = 512
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extension', 'img')


def gradient(size):
    img = Image.new('RGB', (size, size))
    top = (47, 124, 246)
    bottom = (18, 58, 140)
    for y in range(size):
        t = y / (size - 1)
        color = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(size):
            img.putpixel((x, y), color)
    return img


def rounded_mask(size, radius):
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def font(size):
    for name in ('arialbd.ttf', 'segoeuib.ttf', 'DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_icon():
    base = gradient(SIZE).convert('RGBA')
    draw = ImageDraw.Draw(base)

    cx, cy = 256, 300
    for radius, width in ((72, 26), (126, 26), (180, 26)):
        box = [cx - radius, cy - radius, cx + radius, cy + radius]
        draw.arc(box, start=225, end=315, fill=(255, 255, 255, 255), width=width)
    draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=(255, 255, 255, 255))

    text = 'RU'
    fnt = font(150)
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((SIZE - tw) / 2 - bbox[0], 372 - bbox[1]), text, font=fnt, fill=(255, 255, 255, 255))

    icon = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    icon.paste(base, (0, 0), rounded_mask(SIZE, 112))
    return icon


def main():
    os.makedirs(OUT, exist_ok=True)
    icon = draw_icon()
    for px in (128, 48, 32, 16):
        icon.resize((px, px), Image.LANCZOS).save(os.path.join(OUT, f'icon_{px}.png'))
    icon.save(os.path.join(OUT, 'icon.png'))
    print('icons written to', OUT)


if __name__ == '__main__':
    main()
