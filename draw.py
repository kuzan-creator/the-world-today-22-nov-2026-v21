#!/usr/bin/env python3
"""The World Today - Sunday 22 November 2026. Draws a 1024x1024 newspaper
front page summing up the day's world news, rendered at 2048 and downscaled.
All pictures are original vector-style drawings made in code; no photos,
no copied artwork. Deterministic: no random module anywhere."""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
S = 2  # supersample factor; canvas is 2048, final image 1024
W = H = 1024 * S

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
SERIF_B = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
SERIF = os.path.join(FONT_DIR, "DejaVuSerif.ttf")
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
SANS_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

CREAM = (247, 241, 222)
PAPER2 = (242, 233, 205)
INK = (24, 24, 28)
NAVY = (22, 35, 63)
RED = (168, 28, 32)
RED_D = (132, 18, 24)
GREY = (90, 86, 76)
LINE = (180, 172, 148)

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def vgrad(w, h, top, bottom):
    """Vertical gradient as an RGB image (numpy, deterministic)."""
    t = np.linspace(0.0, 1.0, h, dtype=np.float64)[:, None, None]
    top_a = np.array(top, dtype=np.float64)[None, None, :]
    bot_a = np.array(bottom, dtype=np.float64)[None, None, :]
    arr = top_a + (bot_a - top_a) * t
    arr = np.repeat(arr, w, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def hgrad(w, h, left, right):
    t = np.linspace(0.0, 1.0, w, dtype=np.float64)[None, :, None]
    l = np.array(left, dtype=np.float64)[None, None, :]
    r = np.array(right, dtype=np.float64)[None, None, :]
    arr = l + (r - l) * t
    arr = np.repeat(arr, h, axis=0)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def grain(img, strength=10):
    """Deterministic sine-hash grain tiled over the image."""
    tile = 256
    yy, xx = np.mgrid[0:tile, 0:tile]
    vals = np.sin(xx * 12.9898 + yy * 78.233) * 43758.5453
    frac = vals - np.floor(vals)
    noise = Image.fromarray((frac * 255).astype(np.uint8), "L").convert("RGB")
    tiled = Image.new("RGB", img.size)
    for y in range(0, img.size[1], tile):
        for x in range(0, img.size[0], tile):
            tiled.paste(noise, (x, y))
    return Image.blend(img, tiled, strength / 255.0)


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, xy, text, fnt, max_w, fill, leading=None, max_lines=None):
    lines = wrap(draw, text, fnt, max_w)
    if max_lines:
        lines = lines[:max_lines]
    if leading is None:
        leading = int(fnt.size * 1.22)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def chip(draw, box, text, fnt, bg, fg=(255, 255, 255)):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=6, fill=bg)
    tw = draw.textlength(text, font=fnt)
    th = fnt.size
    draw.text(((x0 + x1 - tw) / 2, y0 + (y1 - y0 - th) / 2 - 2), text,
              font=fnt, fill=fg)


def sun_glow(draw, cx, cy, r, colour):
    for i in range(5, 0, -1):
        rr = r * i / 5.0
        a = int(60 / i)
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                     fill=(colour[0], colour[1], colour[2]))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)


# ---------------------------------------------------------------- scenes
# Each scene painter draws into a box (x0, y0, x1, y1) on the big canvas.
# They are simple original flat illustrations: gradients, silhouettes,
# flames, smoke and highlights, all drawn with Pillow primitives.

def scene_cop31(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (168, 214, 226), (238, 240, 214)), (x0, y0))
    # globe
    gx, gy, gr = x0 + int(w * 0.20), y0 + int(h * 0.42), int(h * 0.34)
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(52, 130, 170))
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], outline=(255, 255, 255), width=4)
    for dx, dy, rr in [(-18, -14, 16), (20, 8, 20), (-6, 22, 12)]:
        d.ellipse([gx + dx - rr, gy + dy - rr, gx + dx + rr, gy + dy + rr],
                  fill=(96, 178, 110))
    # thermometer
    tx = x0 + int(w * 0.44)
    d.rounded_rectangle([tx, y0 + 18, tx + 22, y0 + h - 60], radius=11,
                        fill=(240, 240, 235), outline=(120, 40, 40), width=3)
    d.rectangle([tx + 5, y0 + h - 110, tx + 17, y0 + h - 62], fill=(214, 60, 48))
    d.ellipse([tx - 8, y0 + h - 78, tx + 30, y0 + h - 40], fill=(214, 60, 48))
    # clock
    cx, cy, cr = x0 + int(w * 0.86), y0 + int(h * 0.34), int(h * 0.30)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(250, 248, 240),
              outline=(40, 40, 40), width=4)
    d.line([cx, cy, cx, cy - cr + 10], fill=(30, 30, 30), width=5)
    d.line([cx, cy, cx + cr - 16, cy + 8], fill=(30, 30, 30), width=5)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(168, 28, 32))
    # negotiating table with delegates
    ty = y0 + int(h * 0.74)
    d.rectangle([x0 + int(w * 0.30), ty, x1 - 14, ty + 16], fill=(122, 82, 52))
    for i, col in enumerate([(214, 60, 48), (52, 130, 170), (240, 180, 60),
                             (96, 178, 110), (150, 90, 160), (230, 120, 40)]):
        px = x0 + int(w * (0.34 + i * 0.10))
        d.ellipse([px, ty - 34, px + 26, ty - 8], fill=(245, 220, 190))
        d.rectangle([px - 4, ty - 10, px + 30, ty], fill=col)


def scene_kryvyi(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (16, 20, 46), (96, 48, 78)), (x0, y0))
    for sx, sy in [(60, 26), (180, 50), (320, 20), (470, 44), (560, 18)]:
        d.ellipse([x0 + sx - 3, y0 + sy - 3, x0 + sx + 3, y0 + sy + 3],
                  fill=(255, 255, 220))
    # missile trails
    for mx, my, ln in [(120, 10, 130), (300, 4, 150), (480, 14, 120)]:
        d.line([x0 + mx, y0 + my, x0 + mx - ln // 2, y0 + my + ln],
               fill=(255, 220, 150), width=5)
        d.ellipse([x0 + mx - 6, y0 + my - 6, x0 + mx + 6, y0 + my + 6],
                  fill=(255, 240, 190))
    # skyline
    base = y1 - 8
    bx = x0 + 8
    for bw, bh in [(70, 90), (56, 120), (80, 74), (60, 132), (74, 96), (66, 110)]:
        d.rectangle([bx, base - bh, bx + bw, base], fill=(12, 14, 34))
        for wy in range(base - bh + 12, base - 10, 22):
            for wx in range(bx + 10, bx + bw - 8, 20):
                if (wx + wy) % 3:
                    d.rectangle([wx, wy, wx + 7, wy + 9], fill=(255, 214, 120))
        bx += bw + 10
    # fires at the foot of the buildings
    for fx in [x0 + 120, x0 + 330, x0 + 520]:
        for k, (fr, col) in enumerate([(26, (255, 120, 30)), (18, (255, 190, 60)),
                                       (10, (255, 240, 140))]):
            d.ellipse([fx - fr, base - 26 - k * 4, fx + fr, base - 2],
                      fill=col)


def scene_bahrain(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (64, 34, 66), (214, 110, 52)), (x0, y0))
    sun_glow(d, x0 + int(w * 0.78), y0 + int(h * 0.30), 34, (255, 196, 110))
    # smoke
    for sx, sy, sr in [(150, 60, 34), (200, 52, 30), (260, 62, 30)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(52, 44, 52))
    # industrial tanks
    base = y0 + int(h * 0.78)
    for tx, tw in [(30, 90), (140, 110), (270, 80)]:
        d.rectangle([x0 + tx, base - 70, x0 + tx + tw, base], fill=(210, 208, 198))
        d.rectangle([x0 + tx, base - 70, x0 + tx + tw, base - 52],
                    fill=(170, 168, 158))
        d.rectangle([x0 + tx + 12, base - 92, x0 + tx + 30, base - 70],
                    fill=(150, 148, 138))
    # flames on the tanks
    for fx in [x0 + 75, x0 + 195, x0 + 310]:
        for fr, col in [(24, (255, 110, 26)), (16, (255, 180, 60)),
                        (9, (255, 235, 140))]:
            d.polygon([(fx - fr, base - 66), (fx, base - 66 - fr - 16),
                       (fx + fr, base - 66)], fill=col)
    # sea and ship
    d.rectangle([x0, base, x1, y1], fill=(28, 52, 88))
    d.rectangle([x0, base, x1, base + 8], fill=(70, 110, 160))
    d.polygon([(x0 + 380, base + 12), (x0 + 600, base + 12), (x0 + 584, base + 38),
               (x0 + 396, base + 38)], fill=(30, 30, 40))
    d.rectangle([x0 + 470, base - 8, x0 + 500, base + 12], fill=(30, 30, 40))
    for wx in range(x0 + 20, x1 - 20, 46):
        d.line([wx, base + 30, wx + 24, base + 30], fill=(90, 140, 190), width=3)


def scene_sparta(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (70, 110, 150), (20, 44, 78)), (x0, y0))
    for sx, sy, sr in [(90, 26, 22), (130, 26, 18), (170, 30, 18)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(70, 66, 72))
    # ship hull
    base = y0 + int(h * 0.72)
    d.polygon([(x0 + 30, base), (x0 + w - 30, base), (x0 + w - 60, base + 34),
               (x0 + 60, base + 34)], fill=(150, 40, 36))
    d.rectangle([x0 + 90, base - 34, x0 + w - 110, base], fill=(214, 208, 196))
    d.rectangle([x0 + 150, base - 58, x0 + 230, base - 34], fill=(170, 60, 48))
    for wx in range(x0 + 100, x0 + w - 120, 30):
        d.rectangle([wx, base - 26, wx + 12, base - 12], fill=(40, 60, 90))
    # flames amidships
    for fx in [x0 + 190, x0 + 240]:
        for fr, col in [(18, (255, 110, 26)), (12, (255, 180, 60)),
                        (6, (255, 235, 140))]:
            d.polygon([(fx - fr, base - 34), (fx, base - 34 - fr - 12),
                       (fx + fr, base - 34)], fill=col)
    d.rectangle([x0, base + 34, x1, y1], fill=(16, 40, 74))
    for wx in range(x0 + 10, x1 - 10, 40):
        d.line([wx, y1 - 12, wx + 20, y1 - 12], fill=(90, 140, 190), width=3)


def scene_regions(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (20, 26, 56), (70, 60, 90)), (x0, y0))
    base = y1 - 6
    bx = x0 + 6
    for bw, bh in [(52, 66), (44, 88), (58, 56), (48, 96), (54, 72)]:
        d.rectangle([bx, base - bh, bx + bw, base], fill=(14, 16, 38))
        for wy in range(base - bh + 10, base - 8, 18):
            d.rectangle([bx + 8, wy, bx + 16, wy + 7], fill=(255, 210, 110))
        bx += bw + 8
    for fx in [x0 + 90, x0 + 210, x0 + 300]:
        for fr, col in [(16, (255, 120, 30)), (10, (255, 190, 70))]:
            d.ellipse([fx - fr, base - 20, fx + fr, base - 2], fill=col)
    # radar arcs
    cx, cy = x0 + w - 40, y0 + 30
    for r in (18, 30, 42):
        d.arc([cx - r, cy - r, cx + r, cy + r], 0, 180,
              fill=(140, 220, 160), width=3)


def scene_gaza(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (226, 214, 178), (190, 160, 120)), (x0, y0))
    base = y0 + int(h * 0.74)
    for bx, bw, bh in [(10, 90, 80), (120, 70, 92), (210, 80, 64)]:
        d.rectangle([x0 + bx, base - bh, x0 + bx + bw, base], fill=(150, 132, 104))
        for wy in range(base - bh + 12, base - 8, 20):
            d.rectangle([x0 + bx + 10, wy, x0 + bx + 20, wy + 10],
                        fill=(70, 62, 50))
    # aid truck
    d.rectangle([x0 + 130, base - 34, x0 + 250, base - 6], fill=(240, 240, 235))
    d.rectangle([x0 + 250, base - 26, x0 + 290, base - 6], fill=(220, 90, 60))
    for wx in (150, 200, 268):
        d.ellipse([x0 + wx - 9, base - 8, x0 + wx + 9, base + 10], fill=(30, 30, 30))
    d.rectangle([x0 + 140, base - 30, x0 + 240, base - 22], fill=(60, 120, 70))
    # smoke
    for sx, sy, sr in [(300, 30, 20), (330, 26, 18), (350, 34, 16)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(120, 112, 100))


def scene_jerusalem(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (238, 226, 196), (206, 182, 140)), (x0, y0))
    base = y0 + int(h * 0.78)
    d.rectangle([x0, base - 70, x1, base], fill=(214, 196, 158))
    for ax in (40, 140, 240):
        d.pieslice([x0 + ax, base - 66, x0 + ax + 70, base - 6], 180, 360,
                   fill=(120, 100, 70))
        d.rectangle([x0 + ax, base - 36, x0 + ax + 70, base], fill=(120, 100, 70))
    # two flags
    for fx, col in [(x0 + 60, (30, 90, 170)), (x0 + 250, (30, 90, 170))]:
        d.line([fx, y0 + 14, fx, base - 70], fill=(60, 60, 60), width=3)
        d.polygon([(fx, y0 + 14), (fx + 44, y0 + 22), (fx, y0 + 34)], fill=col)
    sun_glow(d, x0 + int(w * 0.82), y0 + 34, 20, (255, 200, 110))


def scene_basra(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (40, 34, 44), (120, 70, 40)), (x0, y0))
    # fireball
    fx, fy = x0 + int(w * 0.55), y0 + int(h * 0.42)
    for r, col in [(46, (255, 110, 26)), (34, (255, 160, 50)), (20, (255, 220, 120))]:
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=col)
    for sx, sy, sr in [(90, 28, 20), (130, 24, 22), (300, 34, 18)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(46, 40, 44))
    base = y0 + int(h * 0.80)
    for tx in (20, 90, 240):
        d.rectangle([x0 + tx, base - 64, x0 + tx + 46, base], fill=(180, 176, 164))
        d.rectangle([x0 + tx + 8, base - 84, x0 + tx + 20, base - 64],
                    fill=(150, 146, 134))
    d.rectangle([x0, base, x1, y1], fill=(24, 22, 26))


def scene_sinaloa(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (240, 190, 120), (170, 110, 60)), (x0, y0))
    d.polygon([(x0, y0 + 90), (x0 + 120, y0 + 30), (x0 + 240, y0 + 90),
               (x0 + 360, y0 + 40), (x1, y0 + 90), (x1, y1), (x0, y1)],
              fill=(150, 96, 52))
    d.polygon([(x0, y0 + 110), (x0 + 160, y0 + 70), (x0 + 320, y0 + 110),
               (x1, y0 + 80), (x1, y1), (x0, y1)], fill=(120, 76, 42))
    # road
    d.polygon([(x0 + 40, y1), (x0 + 170, y0 + 100), (x0 + 210, y0 + 100),
               (x0 + 340, y1)], fill=(60, 56, 52))
    for fy in range(y0 + 110, y1 - 6, 22):
        d.rectangle([x0 + 180, fy, x0 + 188, fy + 10], fill=(240, 220, 120))
    # helicopter
    hx, hy = x0 + 250, y0 + 34
    d.ellipse([hx - 26, hy - 10, hx + 26, hy + 10], fill=(40, 44, 52))
    d.rectangle([hx - 70, hy - 3, hx + 70, hy + 1], fill=(40, 44, 52))
    d.rectangle([hx + 26, hy - 4, hx + 52, hy + 2], fill=(40, 44, 52))
    # roadblock flames
    for fx in [x0 + 90, x0 + 300]:
        for fr, col in [(12, (255, 110, 26)), (7, (255, 190, 70))]:
            d.polygon([(fx - fr, y1 - 8), (fx, y1 - 8 - fr - 10),
                       (fx + fr, y1 - 8)], fill=col)


def scene_hormuz(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (150, 190, 220), (240, 210, 150)), (x0, y0))
    # land masses
    d.polygon([(x0, y0), (x0 + 110, y0), (x0 + 90, y0 + 60), (x0, y0 + 70)],
              fill=(214, 196, 140))
    d.polygon([(x1, y0 + 40), (x1, y1), (x0 + 240, y1), (x0 + 280, y0 + 60)],
              fill=(214, 196, 140))
    d.rectangle([x0, y0 + 60, x1, y1], fill=(36, 90, 140))
    for wy in range(y0 + 80, y1 - 8, 18):
        d.line([x0 + 10, wy, x0 + 60, wy], fill=(90, 150, 200), width=3)
        d.line([x0 + 260, wy + 8, x0 + 330, wy + 8], fill=(90, 150, 200), width=3)
    # tankers
    for tx in (90, 190):
        d.polygon([(x0 + tx, y0 + 96), (x0 + tx + 90, y0 + 96),
                   (x0 + tx + 78, y0 + 116), (x0 + tx + 12, y0 + 116)],
                  fill=(40, 40, 48))
        d.rectangle([x0 + tx + 30, y0 + 80, x0 + tx + 48, y0 + 96],
                    fill=(40, 40, 48))
    # drones
    for dx, dy in [(300, 26), (330, 44)]:
        d.ellipse([x0 + dx - 8, y0 + dy - 3, x0 + dx + 8, y0 + dy + 3],
                  fill=(30, 30, 36))
        d.line([x0 + dx - 16, y0 + dy, x0 + dx + 16, y0 + dy],
               fill=(30, 30, 36), width=2)


def scene_bomber(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (250, 190, 110), (120, 140, 190)), (x0, y0))
    sun_glow(d, x0 + 300, y0 + 40, 26, (255, 220, 130))
    # jet turning away: fuselage, swept wings, tail
    jx, jy = x0 + 150, y0 + 62
    d.polygon([(jx - 70, jy), (jx + 60, jy - 12), (jx + 86, jy - 6),
               (jx + 60, jy + 6), (jx - 60, jy + 10)], fill=(52, 56, 66))
    d.polygon([(jx - 10, jy), (jx + 30, jy - 34), (jx + 44, jy - 30),
               (jx + 20, jy + 2)], fill=(40, 44, 54))
    d.polygon([(jx - 10, jy + 4), (jx + 24, jy + 30), (jx + 36, jy + 26),
               (jx + 16, jy + 6)], fill=(40, 44, 54))
    # dotted flight path turning back
    for i in range(10):
        px = x0 + 30 + i * 26
        py = y0 + 100 - int(18 * math.sin(i * 0.55))
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 255, 255))
    d.rectangle([x0, y1 - 22, x1, y1], fill=(36, 80, 130))
    for wx in range(x0 + 10, x1 - 10, 44):
        d.line([wx, y1 - 10, wx + 22, y1 - 10], fill=(120, 170, 220), width=3)


def scene_bolsonaro(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (226, 236, 240), (180, 200, 210)), (x0, y0))
    # wall cross
    d.rectangle([x0 + 300, y0 + 12, x0 + 322, y0 + 56], fill=(200, 60, 60))
    d.rectangle([x0 + 288, y0 + 24, x0 + 334, y0 + 40], fill=(200, 60, 60))
    # bed
    base = y0 + int(h * 0.78)
    d.rectangle([x0 + 30, base - 26, x0 + 300, base - 10], fill=(240, 244, 246))
    d.rectangle([x0 + 30, base - 10, x0 + 300, base], fill=(90, 110, 130))
    d.rectangle([x0 + 30, base - 52, x0 + 70, base - 26], fill=(240, 244, 246))
    d.ellipse([x0 + 44, base - 72, x0 + 70, base - 46], fill=(232, 200, 170))
    d.rectangle([x0 + 70, base - 48, x0 + 290, base - 26], fill=(70, 130, 170))
    # monitor with ECG trace
    d.rectangle([x0 + 250, y0 + 16, x0 + 340, y0 + 64], fill=(24, 34, 44))
    pts = []
    for i in range(41):
        px = x0 + 256 + i * 2
        py = y0 + 44 - (16 if i == 20 else (8 if i in (18, 22) else 0))
        pts.append((px, py))
    d.line(pts, fill=(90, 230, 140), width=3)


def scene_estonia(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    CANVAS.paste(vgrad(w, h, (190, 210, 228), (150, 170, 190)), (x0, y0))
    base = y0 + int(h * 0.76)
    # fence
    for fx in range(x0 + 10, x1 - 10, 26):
        d.line([fx, base - 62, fx, base], fill=(70, 76, 84), width=4)
    d.line([x0, base - 58, x1, base - 58], fill=(70, 76, 84), width=4)
    d.line([x0, base - 30, x1, base - 30], fill=(70, 76, 84), width=4)
    # Estonian flag
    d.rectangle([x0 + 40, y0 + 14, x0 + 120, y0 + 30], fill=(40, 110, 200))
    d.rectangle([x0 + 40, y0 + 30, x0 + 120, y0 + 46], fill=(20, 20, 24))
    d.rectangle([x0 + 40, y0 + 46, x0 + 120, y0 + 62], fill=(240, 240, 240))
    # barrier
    d.rectangle([x0 + 170, base - 34, x0 + 320, base - 18], fill=(230, 60, 50))
    d.rectangle([x0 + 170, base - 18, x0 + 320, base - 10], fill=(240, 240, 240))
    d.rectangle([x0, base, x1, y1], fill=(110, 120, 110))
    d.line([x0 + 150, base + 16, x0 + 190, base + 16], fill=(240, 240, 240),
           width=4)


SCENES = {
    1: scene_cop31, 2: scene_kryvyi, 3: scene_bahrain, 4: scene_sparta,
    5: scene_regions, 6: scene_gaza, 7: scene_jerusalem, 8: scene_basra,
    9: scene_sinaloa, 10: scene_hormuz, 11: scene_bomber,
    12: scene_bolsonaro, 13: scene_estonia,
}


# ---------------------------------------------------------------- content
HEROES = [
    dict(n=1, tag="COP31: DEAL CLOSE", place="ANTALYA, TURKEY \u00b7 CLIMATE",
         head="COP31 talks close in on a final deal",
         body="A new package lands after a fight over fossil fuels; states have until 03:00 GMT to object. (Reuters)",
         src="Summit president \u00b7 Reuters"),
    dict(n=2, tag="KRYVYI RIH: 2 DEAD, 73 HURT", place="KRYVYI RIH, UKRAINE \u00b7 WAR",
         head="Missiles kill a boy of 7 in Zelenskyy's home city",
         body="Three ballistic missiles and 148 drones hit overnight; a boy of 7 and a paramedic die. (Ukrinform)",
         src="Officials' count \u00b7 Ukrinform"),
    dict(n=3, tag="BAHRAIN: STRUCK", place="MANAMA, BAHRAIN \u00b7 IRAN WAR",
         head="Iran claims strikes on US bases in Bahrain",
         body="The IRGC says missiles and drones hit two Patriot radars; Bahrain reports a site burned. (Al Jazeera)",
         src="Bahrain govt \u00b7 Al Jazeera"),
]

MEDIUMS = [
    dict(n=4, tag="SHIP ABLAZE", place="GULF OF FINLAND",
         head="Russian cargo ship burns after drone strike",
         src="Finnish forces \u00b7 BBC"),
    dict(n=5, tag="NINE REGIONS HIT", place="KYIV, UKRAINE",
         head="Russia hits nine regions in one night",
         src="Live updates \u00b7 Ukrinform"),
    dict(n=6, tag="4 KILLED", place="GAZA",
         head="Four killed in Gaza as the ceasefire strains",
         src="Witnesses \u00b7 QNA"),
    dict(n=7, tag="COALITION TALKS", place="JERUSALEM",
         head="Eisenkot invites Likud to marathon talks",
         src="Party statement \u00b7 Straits Times"),
    dict(n=8, tag="4 DEAD, 35 HURT", place="BASRA, IRAQ",
         head="Fire at Hartha power station kills four",
         src="Security officials \u00b7 Reuters"),
    dict(n=9, tag="11 DEAD", place="SINALOA, MEXICO",
         head="'El Chapo Isidro' caught in raid",
         src="Security chief \u00b7 Reuters"),
    dict(n=10, tag="TANKERS HIT", place="STRAIT OF HORMUZ",
         head="Two tankers struck off Oman as Gulf burns",
         src="Maritime reports \u00b7 Reuters"),
    dict(n=11, tag="170 KM OUT", place="MANILA, PHILIPPINES",
         head="Chinese bomber turns back from Manila",
         src="Defence reports \u00b7 Reports"),
    dict(n=12, tag="BOLSONARO: ICU", place="BRASILIA, BRAZIL",
         head="Bolsonaro in intensive care, stable",
         src="Hospital \u00b7 Reuters"),
    dict(n=13, tag="1 DEC", place="TALLINN, ESTONIA",
         head="Estonia to shut its Russia border on 1 Dec",
         src="Border guard \u00b7 Reuters"),
]

# (number, place, text, outlet) - the 22 more stories, two columns of 11.
MORE = [
    ("14", "Denmark", "Expels Russian attache over rapper plot", "Guardian"),
    ("15", "Germany", "IG Metall widens halt in 23 Nov national strike", "Reuters"),
    ("16", "Moldova", "Reports a Russian airspace breach", "Kyiv Ind."),
    ("17", "Portugal", "Thousands march in Lisbon on living costs", "Reuters"),
    ("18", "Saudi Arabia", "Air defences down a missile", "Investing.com"),
    ("19", "Lebanon", "Aoun demands Israeli withdrawal", "Al Jazeera"),
    ("20", "Iran", "President warns of a 'silent economic war'", "Al Jazeera"),
    ("21", "US", "FBI looks into apparent hack of its crime database", "BBC"),
    ("22", "US", "Teen gamer and mother help FBI rescue a girl", "BBC"),
    ("23", "US", "Midterm loss corners Vance as 2028 field widens", "ST"),
    ("24", "US", "First child measles death in Virginia since 1978", "Reports"),
    ("25", "US", "Hegseth tightens US-Canada defence ties", "Washington Post"),
    ("26", "Myanmar", "Quake of 4.1 strikes in the early hours", "NCS"),
    ("27", "Japan", "To train live-fire at Indian facilities, a first", "Reports"),
    ("28", "Australia", "Fred Nile, ex-NSW MP, dies aged 92", "ABC"),
    ("29", "India", "Modi opens Nitish Setu bridge in Bihar", "PTI"),
    ("30", "Nigeria", "Boat of funeral mourners capsizes; 24 dead", "NEMA"),
    ("31", "Somalia", "Expels the UAE ambassador, recalls envoy", "Reports"),
    ("32", "Ethiopia", "~700,000 displaced by fighting in the south", "Sat"),
    ("33", "Geneva", "Killer-robot talks end with no binding rules", "AP"),
    ("34", "Space", "Voyager-1 reaches one light-day from Earth", "NASA"),
    ("35", "Tennis", "Zverev v Alcaraz in today's ATP Finals", "TOI"),
]

# list number colour per story region (same palette as REGIONS)
MORE_COLOR = {}
for _n in ("14", "15", "16", "17", "33"):
    MORE_COLOR[_n] = (22, 72, 140)      # EUROPE blue
for _n in ("18", "19", "20"):
    MORE_COLOR[_n] = (168, 28, 32)      # MIDDLE EAST red
for _n in ("21", "22", "23", "24", "25"):
    MORE_COLOR[_n] = (30, 110, 70)      # AMERICAS green
for _n in ("26", "27", "28", "29"):
    MORE_COLOR[_n] = (196, 120, 30)     # ASIA-PACIFIC yellow
for _n in ("30", "31", "32"):
    MORE_COLOR[_n] = (120, 90, 40)      # AFRICA brown
for _n in ("34", "35"):
    MORE_COLOR[_n] = (90, 60, 120)      # WORLD purple
del _n

REGIONS = [
    ("EUROPE 9", (22, 72, 140)), ("MIDDLE EAST 8", (168, 28, 32)),
    ("AMERICAS 7", (30, 110, 70)), ("ASIA-PACIFIC 5", (196, 120, 30)),
    ("AFRICA 3", (120, 90, 40)), ("WORLD 3", (90, 60, 120)),
]

STRIP = [
    ("~200", "nations at COP31"),
    ("03:00", "GMT objection deadline"),
    ("148", "drones overnight"),
    ("73", "injured in Kryvyi Rih"),
    ("16", "crew evacuated"),
    ("2", "Patriot radars claimed"),
]

# ---------------------------------------------------------------- map
NA = [(-168, 66), (-140, 70), (-125, 72), (-110, 68), (-95, 69), (-85, 66),
      (-80, 73), (-65, 62), (-55, 52), (-60, 47), (-70, 42), (-75, 35),
      (-80, 32), (-85, 29), (-90, 21), (-97, 16), (-105, 20), (-115, 28),
      (-125, 40), (-125, 49), (-140, 60), (-155, 58), (-165, 60)]
SA = [(-80, 9), (-75, 11), (-62, 9), (-52, 5), (-50, 0), (-44, -3), (-35, -8),
      (-40, -20), (-48, -28), (-57, -38), (-65, -45), (-70, -54), (-73, -50),
      (-73, -37), (-70, -20), (-80, -5)]
AF = [(-17, 15), (-10, 31), (-5, 35), (10, 37), (20, 32), (32, 31), (35, 28),
      (43, 12), (51, 11), (48, 0), (40, -10), (35, -18), (32, -29), (26, -34),
      (19, -35), (15, -27), (12, -18), (9, 4), (-8, 4)]
EU = [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 58), (8, 57), (18, 56),
      (21, 55), (24, 59), (28, 60), (30, 70), (40, 68), (55, 69), (70, 73),
      (90, 75), (110, 74), (130, 72), (150, 70), (170, 66), (178, 65),
      (170, 60), (162, 56), (158, 52), (142, 50), (140, 40), (135, 35),
      (130, 32), (127, 35), (122, 38), (120, 32), (115, 23), (108, 18),
      (105, 9), (100, 8), (98, 12), (95, 16), (92, 21), (88, 22), (80, 13),
      (77, 8), (72, 20), (66, 25), (60, 25), (57, 26), (52, 28), (48, 30),
      (44, 29), (40, 32), (36, 36), (30, 36), (27, 40), (23, 40), (19, 42),
      (12, 44), (8, 44), (3, 43), (-2, 37), (-9, 37)]
AU = [(113, -22), (114, -32), (120, -34), (130, -32), (140, -38), (147, -39),
      (150, -37), (153, -27), (146, -19), (142, -11), (136, -12), (132, -12),
      (126, -14), (122, -17)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-2, 58), (0, 53)]
JP = [(130, 31), (133, 34), (137, 35), (140, 38), (141, 42), (143, 44), (140, 40)]
NZ = [(167, -45), (172, -41), (175, -38), (178, -37), (174, -41)]
LAND = [NA, SA, AF, EU, AU, UK, JP, NZ]

PINS = {  # story number -> (lon, lat), nudged apart where they crowd
    1: (24.0, 38.5), 2: (37.0, 46.0), 3: (48.5, 21.0), 4: (17.0, 63.0),
    5: (19.5, 51.0), 6: (30.0, 28.5), 7: (38.0, 36.5), 8: (48.5, 30.0),
    9: (-108.5, 25.6), 10: (62.0, 24.0), 11: (121.0, 14.6),
    12: (-47.9, -15.8), 13: (28.5, 57.5),
}

# pin colour = story region, same palette as the list numbers (MORE_COLOR)
PIN_COLOR = {
    1: (90, 60, 120),    # WORLD purple (Antalya)
    2: (22, 72, 140), 4: (22, 72, 140), 5: (22, 72, 140),
    13: (22, 72, 140),  # EUROPE blue
    3: (168, 28, 32), 6: (168, 28, 32), 7: (168, 28, 32),
    8: (168, 28, 32), 10: (168, 28, 32),  # MIDDLE EAST red
    9: (30, 110, 70), 12: (30, 110, 70),  # AMERICAS green
    11: (196, 120, 30),  # ASIA-PACIFIC yellow (Manila)
}


def point_in_poly(lon, lat, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xin = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < xin:
                inside = not inside
    return inside


def draw_map(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(127, 179, 213))
    d.rectangle([x0, y0, x1, y1], outline=LINE, width=2)
    mw, mh = x1 - x0, y1 - y0
    for poly in LAND:
        pts = [(x0 + (lon + 180) / 360.0 * mw, y0 + (84 - lat) / 168.0 * mh)
               for lon, lat in poly]
        d.polygon(pts, fill=(200, 212, 186))
        d.line(pts + [pts[0]], fill=INK, width=3, joint="curve")
    for num, (lon, lat) in PINS.items():
        px = x0 + (lon + 180) / 360.0 * mw
        py = y0 + (84 - lat) / 168.0 * mh
        r = 12
        d.ellipse([px - r - 2, py - r - 2, px + r + 2, py + r + 2],
                  fill=(255, 255, 255))
        d.ellipse([px - r, py - r, px + r, py + r], fill=PIN_COLOR[num],
                  outline=(255, 255, 255), width=2)
        t = str(num)
        tw = d.textlength(t, font=font(SANS_B, 17))
        d.text((px - tw / 2, py - 9), t, font=font(SANS_B, 17),
               fill=(255, 255, 255))


# ---------------------------------------------------------------- build
CANVAS = None


def build():
    global CANVAS
    img = Image.new("RGB", (W, H), CREAM)
    CANVAS = img
    # paper gradient wash
    wash = vgrad(W, H, (250, 246, 230), (240, 230, 200))
    img = Image.blend(img, wash, 0.55)
    d = ImageDraw.Draw(img, "RGBA")
    mx = 36

    # top bar
    d.rectangle([0, 0, W, 54], fill=NAVY)
    d.text((mx, 12), "THE WORLD IN ONE DAY", font=font(SANS_B, 28),
           fill=(255, 255, 255))
    right = "35 STORIES \u00b7 6 REGIONS \u00b7 EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    tw = d.textlength(right, font=font(SANS_B, 24))
    d.text((W - mx - tw, 15), right, font=font(SANS_B, 24), fill=(220, 225, 240))

    # title
    title = "Sunday 22 November 2026"
    tf = font(SERIF_B, 116)
    tw = d.textlength(title, font=tf)
    d.text(((W - tw) / 2, 64), title, font=tf, fill=INK)
    sub = ("Climate deal in sight at COP31 \u00b7 Missiles kill a boy of 7 in "
           "Kryvyi Rih \u00b7 Iran claims strikes on US bases in Bahrain")
    sf = font(SERIF_I, 33)
    tw = d.textlength(sub, font=sf)
    d.text(((W - tw) / 2, 192), sub, font=sf, fill=RED_D)

    # number strip
    y0, y1 = 238, 322
    d.line([mx, y0, W - mx, y0], fill=INK, width=3)
    d.line([mx, y1, W - mx, y1], fill=INK, width=3)
    cell = (W - 2 * mx) / 6
    for i, (num, lab) in enumerate(STRIP):
        cx = mx + cell * i
        nf = font(SANS_B, 58)
        tw = d.textlength(num, font=nf)
        d.text((cx + (cell - tw) / 2, y0 + 4), num, font=nf, fill=RED)
        lf = font(SANS, 20)
        tw = d.textlength(lab, font=lf)
        d.text((cx + (cell - tw) / 2, y0 + 58), lab, font=lf, fill=GREY)
        if i:
            d.line([cx, y0 + 8, cx, y1 - 8], fill=LINE, width=2)

    # region bar
    y0, y1 = 334, 372
    x = mx
    total = W - 2 * mx
    for name, col in REGIONS:
        seg = total / 6
        d.rectangle([x, y0, x + seg - 3, y1], fill=col)
        rf = font(SANS_B, 25)
        tw = d.textlength(name, font=rf)
        d.text((x + (seg - tw) / 2, y0 + 7), name, font=rf, fill=(255, 255, 255))
        x += seg

    # heroes
    hy0, hy1 = 384, 760
    hw = 640
    for i, hro in enumerate(HEROES):
        x0 = mx + i * (hw + 28)
        x1 = x0 + hw
        SCENES[hro["n"]](d, x0, hy0, x1, hy0 + 200)
        d.rectangle([x0, hy0, x1, hy0 + 200], outline=(60, 60, 60), width=3)
        chip(d, (x0 + 8, hy0 + 8, x0 + 8 + d.textlength(hro["tag"], font=font(SANS_B, 24)) + 22, hy0 + 40),
             hro["tag"], font(SANS_B, 24), RED)
        chip(d, (x0 + 8, hy0 + 200 - 36, x0 + 8 + d.textlength(hro["src"], font=font(SANS_B, 22)) + 22, hy0 + 200 - 8),
             hro["src"], font(SANS_B, 22), (20, 20, 24))
        pf = font(SANS_B, 24)
        d.text((x0, hy0 + 210), hro["place"], font=pf, fill=RED)
        nf = font(SERIF_B, 42)
        draw_wrapped(d, (x0, hy0 + 238), hro["head"], nf, hw, INK,
                     leading=46, max_lines=2)
        bf = font(SANS, 25)
        draw_wrapped(d, (x0, hy0 + 330), hro["body"], bf, hw, (50, 48, 44),
                     leading=30, max_lines=2)
        # story number badge
        n = str(hro["n"])
        d.ellipse([x1 - 44, hy0 + 210, x1 - 4, hy0 + 250], fill=RED)
        tw = d.textlength(n, font=font(SANS_B, 26))
        d.text((x1 - 24 - tw / 2, hy0 + 214), n, font=font(SANS_B, 26),
               fill=(255, 255, 255))

    # medium cards, two rows of five
    cw, gap = 380, 12
    for row in range(2):
        for col in range(5):
            m = MEDIUMS[row * 5 + col]
            x0 = mx + col * (cw + gap)
            x1 = x0 + cw
            y0 = 776 + row * 248
            y1 = y0 + 132
            SCENES[m["n"]](d, x0, y0, x1, y1)
            d.rectangle([x0, y0, x1, y1], outline=(60, 60, 60), width=2)
            chip(d, (x0 + 6, y0 + 6, x0 + 6 + d.textlength(m["tag"], font=font(SANS_B, 20)) + 16, y0 + 30),
                 m["tag"], font(SANS_B, 20), RED)
            chip(d, (x0 + 6, y1 - 28, x0 + 6 + d.textlength(m["src"], font=font(SANS_B, 18)) + 16, y1 - 6),
                 m["src"], font(SANS_B, 18), (20, 20, 24))
            d.text((x0, y1 + 8), m["place"], font=font(SANS_B, 21), fill=RED)
            draw_wrapped(d, (x0, y1 + 32), m["head"], font(SERIF_B, 29), cw,
                         INK, leading=33, max_lines=2)
            n = str(m["n"])
            d.ellipse([x1 - 34, y1 + 6, x1 - 4, y1 + 36], fill=RED)
            tw = d.textlength(n, font=font(SANS_B, 22))
            d.text((x1 - 19 - tw / 2, y1 + 9), n, font=font(SANS_B, 22),
                   fill=(255, 255, 255))

    # map + also-on list
    my0 = 1284
    d.text((mx, my0), "WHERE IT HAPPENED", font=font(SANS_B, 26), fill=INK)
    d.text((mx, my0 + 30), "pins match story numbers", font=font(SANS, 21),
           fill=GREY)
    lx = 664
    d.text((lx, my0), "ALSO ON SUNDAY 22 NOVEMBER \u2014 22 MORE STORIES",
           font=font(SANS_B, 26), fill=INK)
    d.line([mx, my0 + 56, W - mx, my0 + 56], fill=INK, width=3)
    draw_map(d, mx, my0 + 66, 628, 1804)
    # list in two columns
    col_w = 660
    for ci in range(2):
        cx = lx + ci * (col_w + 16)
        for ri in range(11):
            num, place, text, outlet = MORE[ci * 11 + ri]
            iy = my0 + 68 + ri * 44
            nf = font(SANS_B, 23)
            d.text((cx, iy), num, font=nf, fill=MORE_COLOR[num])
            tf = font(SANS, 18)
            line = "%s: %s (%s)" % (place, text, outlet)
            lines = wrap(d, line, tf, col_w - 52)
            yy = iy + 2
            for ln in lines[:2]:
                d.text((cx + 52, yy), ln, font=tf, fill=INK)
                yy += 20
    # date check
    by0, by1 = 1840, 1956
    d.rectangle([mx, by0, W - mx, by1], outline=RED, width=4)
    d.rectangle([mx, by0, W - mx, by1], fill=(255, 244, 240))
    d.rectangle([mx, by0, W - mx, by1], outline=RED, width=4)
    d.text((mx + 16, by0 + 8), "DATE CHECK", font=font(SANS_B, 26), fill=RED)
    dc = ("Wires read to 04:00 UTC, Sunday 22 November 2026. Every story here "
          "was reported, or was still developing, in the Sunday news cycle. "
          "Left out as other days' news: the 400-drone, 110-missile barrage on "
          "Ukraine (overnight 19\u201320 Nov); the Peru quake (Fri 20 Nov, 19:09 "
          "local); missiles landing in Poland (20 Nov); the Kerch Bridge strikes "
          "(17\u201318 Nov); the Shenzhen summit, the GTA VI launch and the "
          "Anthropic market debut (all 19 Nov).")
    draw_wrapped(d, (mx + 16, by0 + 38), dc, font(SANS, 22), W - 2 * mx - 32,
                 INK, leading=25, max_lines=3)
    # sources + footer
    d.text((mx, 1968),
           "Sources: Reuters, BBC, Al Jazeera, AP, CNN, Guardian, Straits Times, "
           "Kyiv Independent, ABC, Times of India, Ukrinform. Pictures and map: "
           "original, drawn in code.",
           font=font(SANS, 20), fill=GREY)
    d.line([mx, 2000, W - mx, 2000], fill=LINE, width=2)
    d.text((mx, 2010), "THE WORLD IN ONE DAY", font=font(SANS_B, 22), fill=INK)
    foot = "SUNDAY 22 NOVEMBER 2026 \u00b7 ONE PAGE"
    tw = d.textlength(foot, font=font(SANS_B, 22))
    d.text((W - mx - tw, 2010), foot, font=font(SANS_B, 22), fill=INK)

    img = grain(img, strength=9)
    out = img.resize((1024, 1024), Image.LANCZOS)
    # JPEG keeps the file well under the 1 MiB limit; the rules allow a JPEG
    # under the name entry.png (format is read from the first bytes).
    out.save(os.path.join(HERE, "entry.png"), "JPEG", quality=90,
             optimize=True)
    print("saved", os.path.join(HERE, "entry.png"))


if __name__ == "__main__":
    build()
