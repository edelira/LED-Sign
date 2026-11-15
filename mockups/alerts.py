"""Animated mock-up of the alert screens (flash + card), as a GIF and a still.

    python3 mockups/alerts.py          # writes mockups/img/alerts.gif / .png

machine() mirrors the firmware's machine lambda in esphome/led-sign.yaml.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import *
from PIL import Image, ImageDraw, ImageFont

ORANGE = (255, 110, 20)
RING = (70, 70, 90)
PANEL = (110, 110, 130)

def sc(c, b):
    return tuple(int(v * max(0.0, min(b, 1.0))) for v in c)

AQUA = (0, 190, 255)
WARM = (255, 120, 20)
ALERT = (255, 45, 40)
SOFT = (240, 240, 255)
ACCENT = {"washer": AQUA, "dryer": WARM, "door": ALERT}

def machine(it, x, y, k, t, kind):
    """Neon-outline front-loader in the alert's colour, 26x29 at k=1."""
    acc = ACCENT[kind]
    R = lambda a, b, w, h, c: it.rect(x + a * k, y + b * k, w * k, h * k, c)
    C = lambda a, b, r, c: it.fcircle(x + a * k, y + b * k, r * k, c)
    R(0, 0, 26, 28, acc)                       # outline ...
    R(1, 1, 24, 26, sc(acc, 0.10))             # ... around a dark body
    R(1, 5, 24, 1, acc)                        # control panel line
    R(3, 2, 2, 2, SOFT); R(7, 2, 2, 2, sc(acc, 0.6)); R(17, 2, 6, 2, sc(acc, 0.6))
    R(3, 28, 3, 1, sc(acc, 0.5)); R(20, 28, 3, 1, sc(acc, 0.5))
    C(13, 17, 8, acc)                          # door ring
    if kind == "washer":
        C(13, 17, 6, (0, 25, 70))
        R(8, 19, 4, 3, (255, 70, 90)); R(11, 18, 4, 4, (255, 210, 60)); R(14, 20, 4, 2, (60, 230, 120))
        # Glint sweeping across the glass
        g = frac(t / 1.5) * 20 - 4
        for j in range(-6, 7):
            gx = 7 + g + j * -0.6
            if (gx - 13) ** 2 + j * j <= 36:
                R(lround(gx), 17 + j, 1, 1, SOFT)
        # Sparkles popping on the machine and just off its corners
        spots = [(4, 9), (21, 12), (5, 23), (22, 24), (12, 8), (-4, 6), (30, 18), (-5, 22)]
        for i, (sx, sy) in enumerate(spots):
            b = math.sin(2 * math.pi * (t / 1.5 + i * 0.37))
            if b > 0.2:
                R(sx, sy, 1, 1, sc(SOFT, b))
                if b > 0.6:
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        R(sx + dx, sy + dy, 1, 1, sc(SOFT, b * 0.6))
                if b > 0.9:
                    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                        R(sx + dx, sy + dy, 1, 1, sc(acc, 0.7))
    elif kind == "dryer":
        b = 0.65 + 0.35 * math.sin(2 * math.pi * t / 1.5)
        C(13, 17, 6, sc((255, 70, 0), b))
        C(13, 17, 3, sc((255, 190, 40), b))
        for i, col in enumerate([SOFT, (0, 220, 255), (60, 230, 120)]):
            a = 2 * math.pi * (t / 3 + i / 3)
            R(12 + lround(4 * math.cos(a)), 16 + lround(4 * math.sin(a)), 2, 2, col)
        for sx in (-4, 29):
            for j in range(20):
                if (j + int(t * 8)) % 6 < 4:
                    R(sx + lround(math.sin(j / 2.5 + 2 * math.pi * t / 1.5)), 6 + j, 1, 1,
                      sc((255, 200, 40) if j < 8 else WARM, 0.5 + j / 40))
    else:
        C(13, 17, 6, (6, 10, 16))
        for i, (mx, my) in enumerate([(10, 15), (15, 19), (12, 21), (16, 14), (9, 19)]):
            R(mx, my, 1, 1, sc((80, 255, 80), 0.5 + 0.5 * math.sin(2 * math.pi * (t / 1.5 + i * 0.2))))
        p = frac(t / 1.0)
        R(13, 24 + int(p * 4), 1, 2, AQUA)
        R(9, 29, 9, 1, AQUA)
        if frac(t / 1.0) < 0.6:
            C(24, 2, 4, (255, 200, 40))
            R(24, 0, 1, 3, BLACK); R(24, 4, 1, 1, BLACK)
        return
    C(23, 25, 4, (40, 230, 90))
    for (a, b_), (c, d) in (((21, 25), (22, 26)), ((22, 26), (25, 23))):
        it.line(x + a * k, y + b_ * k, x + c * k, y + d * k, BLACK)
        if k > 1: it.line(x + a * k, y + b_ * k + 1, x + c * k, y + d * k + 1, BLACK)

def flash(kind, l1, l2, t):
    it = Sign()
    acc = ACCENT[kind]
    per = [(x, 0) for x in range(W)] + [(W - 1, y) for y in range(1, H)] + \
          [(x, H - 1) for x in range(W - 2, -1, -1)] + [(0, y) for y in range(H - 2, 0, -1)]
    for i, (x, y) in enumerate(per):                                  # marching border
        if (i - int(t * 16)) % 8 < 4: it.px(x, y, acc)
    machine(it, 12, 3, 2, t, kind)
    it.print(134, 22, 16, acc, "CENTER", l1)
    it.print(134, 44, 16, WHITE, "CENTER", l2)
    return it

def card(kind, l1, l2, t, hm, ampm):
    it = Sign()
    current_clock(it, hm, ampm, "Sun Nov 15")
    machine(it, 147, 4, 1, t, kind)
    it.txt(160, 40, 8, ACCENT[kind], "TOP_CENTER", l1)
    it.txt(160, 52, 8, WHITE, "TOP_CENTER", l2)
    return it

ROWS = [("washer", "WASHER", "DONE", "9:42", "PM"),
        ("dryer", "DRYER", "DONE", "2:47", "PM"),
        ("door", "WASHER", "OPEN DOOR", "11:30", "PM")]
S, PAD, LAB = 4, 20, 34
font = ImageFont.load_default(size=20)
def frame(t):
    tw, th = W * S, H * S
    img = Image.new("RGB", (2 * tw + 3 * PAD, len(ROWS) * (th + PAD) + LAB + PAD), (18, 18, 20))
    d = ImageDraw.Draw(img)
    d.text((PAD, PAD - 6), "New alert: whole sign, 10 seconds", fill=(220, 220, 220), font=font)
    d.text((tw + 2 * PAD, PAD - 6), "Then: a card taking turns with the weather", fill=(220, 220, 220), font=font)
    for r, (kind, l1, l2, hm, ap) in enumerate(ROWS):
        y = LAB + PAD + r * (th + PAD)
        img.paste(led(flash(kind, l1, l2, t).image(), s=S), (PAD, y))
        img.paste(led(card(kind, l1, l2, t, hm, ap).image(), s=S), (tw + 2 * PAD, y))
    return img
N, DUR = 36, 3.0
frames = [frame(i * DUR / N) for i in range(N)]
out = os.path.join(OUT, "alerts")
frames[7].save(out + ".png")
pal = frames[7].quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE)
q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
q[0].save(out + ".gif", save_all=True, append_images=q[1:], duration=int(DUR * 1000 / N), loop=0, optimize=False)
