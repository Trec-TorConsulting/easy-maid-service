#!/usr/bin/env python3
"""Generate Easy Maid Service starter brand assets (raster).

Run:  ../.venv-assets/bin/python generate_assets.py
Produces PNG icons + favicon.ico from a single supersampled badge mark.
This is a STARTING POINT — replace with final artwork when available.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

# Brand palette — natural green tones
GREEN_TOP = (91, 176, 122)   # #5BB07A  fresh sage
GREEN_BOT = (30, 79, 58)     # #1E4F3A  deep forest
GREEN_TEXT = (30, 79, 58)    # #1E4F3A  deep forest (wordmark)
MINT = (198, 246, 213)       # #C6F6D5  soft mint accent
WHITE = (255, 255, 255)
SLATE = (26, 46, 37)         # #1A2E25  natural dark green-gray

# Backwards-compatible aliases used below
TEAL_TOP = GREEN_TOP
TEAL_BOT = GREEN_BOT
TEAL_TEXT = GREEN_TEXT
AMBER = MINT

SS = 4  # supersample factor


def load_font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


def vgradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1) if h > 1 else 0
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        d.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def star4(draw, cx, cy, outer, inner, fill):
    pts = []
    for i in range(8):
        ang = math.pi / 2 - i * (math.pi / 4)
        rad = outer if i % 2 == 0 else inner
        pts.append((cx + rad * math.cos(ang), cy - rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def make_mark(size):
    """Return an RGBA badge mark of the given size."""
    s = size * SS
    badge = vgradient(s, s, TEAL_TOP, TEAL_BOT)

    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, s - 1, s - 1], radius=int(s * 0.24), fill=255
    )

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img.paste(badge, (0, 0), mask)
    draw = ImageDraw.Draw(img)

    # Monogram "EM"
    font = load_font(int(s * 0.40))
    text = "EM"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (s - tw) / 2 - bbox[0]
    ty = (s - th) / 2 - bbox[1] + int(s * 0.03)
    draw.text((tx, ty), text, font=font, fill=WHITE)

    # Sparkles (fresh/clean cue)
    star4(draw, s * 0.75, s * 0.24, s * 0.11, s * 0.038, MINT)
    star4(draw, s * 0.86, s * 0.40, s * 0.045, s * 0.016, WHITE)

    return img.resize((size, size), Image.LANCZOS)


def make_wordmark():
    mark_size = 240
    mark = make_mark(mark_size)
    gap = 40
    pad = 36

    f1 = load_font(132)
    f2 = load_font(60)
    line1 = "Easy Maid"
    line2 = "S E R V I C E"

    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    w1 = d.textbbox((0, 0), line1, font=f1)[2]
    w2 = d.textbbox((0, 0), line2, font=f2)[2]
    text_w = int(max(w1, w2))

    W = pad + mark_size + gap + text_w + pad
    H = pad + mark_size + pad
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(mark, (pad, (H - mark_size) // 2))

    draw = ImageDraw.Draw(canvas)
    text_x = pad + mark_size + gap
    draw.text((text_x, H // 2 - 128), line1, font=f1, fill=TEAL_TEXT)
    draw.text((text_x, H // 2 + 40), line2, font=f2, fill=SLATE)
    return canvas


def main():
    mark512 = make_mark(512)
    mark512.save(os.path.join(HERE, "logo-mark.png"))
    make_mark(192).save(os.path.join(HERE, "icon-192.png"))
    make_mark(512).save(os.path.join(HERE, "icon-512.png"))
    make_mark(180).save(os.path.join(HERE, "apple-touch-icon.png"))

    # favicon.png (broad-compatibility raster) + multi-size favicon.ico
    make_mark(48).save(os.path.join(HERE, "favicon.png"))
    mark256 = make_mark(256)
    mark256.save(
        os.path.join(HERE, "favicon.ico"),
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
    )

    make_wordmark().save(os.path.join(HERE, "logo-full.png"))
    print("Generated:", ", ".join(sorted(
        f for f in os.listdir(HERE)
        if f.endswith((".png", ".ico"))
    )))


if __name__ == "__main__":
    main()
