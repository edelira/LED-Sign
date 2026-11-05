#!/usr/bin/env python3
"""Mock-ups of the 192x64 sign's clock / weather / trash screens.

Pillow draws each screen one pixel per LED, using the firmware's Silkscreen
font, colours, coordinates and drawing rules (ESPHome text alignment, circle
and line algorithms), so text widths and layout match the sign. NumPy then
turns every pixel into a round LED dot on a dark background.

    python3 mockups/render.py          # writes mockups/img/*.png + sheet.png

"current_*" screens are ports of esphome/led-sign.yaml as it is today;
"idea_*" screens are layout ideas, not in the firmware.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "img")
FONT = os.path.join(HERE, "fonts", "Silkscreen-Regular.ttf")
W, H = 192, 64

# Firmware colours (color: block in led-sign.yaml) and a few inline ones.
AMBER = (255, 176, 60)
RED = (255, 40, 30)
WHITE = (235, 225, 200)
DIM = (150, 120, 70)
GRAY = (70, 70, 70)
CYAN = (60, 200, 255)
GREEN = (40, 230, 80)
LINE_C = (35, 30, 25)
SUN = (255, 200, 40)
CLOUD = (170, 170, 190)
RAIN_C = (60, 140, 255)
BLACK = (0, 0, 0)

FONTS = {s: ImageFont.truetype(FONT, s) for s in (8, 16, 32)}
CAP = {8: 4, 16: 7, 32: 13}   # rows above the capitals, as in the firmware


def lround(v):
    return int(math.floor(v + 0.5)) if v >= 0 else -int(math.floor(-v + 0.5))


def frac(v):
    return v - math.floor(v)


def scale(c, k):
    return tuple(int(x * k) for x in c)


class Sign:
    """A tiny subset of ESPHome's Display API."""

    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.buf = np.zeros((h, w, 3), np.uint8)
        self.clip = None

    # ---- primitives ----
    def start_clipping(self, l, t, r, b):
        self.clip = (l, t, r, b)

    def end_clipping(self):
        self.clip = None

    def px(self, x, y, c):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        if self.clip:
            l, t, r, b = self.clip
            if not (l <= x < r and t <= y < b):
                return
        self.buf[y, x] = c

    def rect(self, x, y, w, h, c):        # filled_rectangle
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x1, y1, x2, y2, c):    # Bresenham, both ends included
        dx, dy = abs(x2 - x1), -abs(y2 - y1)
        sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
        err = dx + dy
        while True:
            self.px(x1, y1, c)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    def fcircle(self, cx, cy, r, c):      # ESPHome's filled_circle
        dx, dy, err = -r, 0, 2 - 2 * r
        while True:
            for x in range(cx + dx, cx - dx + 1):
                self.px(x, cy + dy, c)
                self.px(x, cy - dy, c)
            e2 = err
            if e2 < dy:
                dy += 1
                err += dy * 2 + 1
                if -dx == dy and e2 <= dx:
                    e2 = 0
            if e2 > dx:
                dx += 1
                err += dx * 2 + 1
            if dx > 0:
                break

    # ---- text ----
    def text_w(self, size, s):
        return int(FONTS[size].getlength(s))

    def print(self, x, y, size, c, align, s):
        """it.print(): align is e.g. 'TOP_LEFT', 'CENTER', 'TOP_RIGHT'."""
        f = FONTS[size]
        asc, desc = f.getmetrics()
        w, h = self.text_w(size, s), asc + desc
        if align.endswith("RIGHT"):
            x -= w
        elif align.endswith("CENTER") or align == "CENTER":
            x -= w // 2
        if align.startswith("CENTER"):
            y -= h // 2
        elif align.startswith("BOTTOM"):
            y -= h
        mask = Image.new("1", (self.w, self.h))
        d = ImageDraw.Draw(mask)
        d.fontmode = "1"
        d.text((x, y + asc), s, font=f, fill=1, anchor="ls")
        ys, xs = np.nonzero(np.asarray(mask))
        for yy, xx in zip(ys, xs):
            self.px(int(xx), int(yy), c)

    def txt(self, x, y, size, c, align, s):
        """The firmware's txt(): y is the top of the capitals."""
        self.print(x, y - CAP[size], size, c, align, s)

    # ---- output ----
    def image(self):
        return Image.fromarray(self.buf, "RGB")


# ---------------------------------------------------------------------------
# Weather icons, ported from the firmware's wx_icon / wx_small lambdas.
# t = seconds on the animation clock (picks the frame).

def cloud_at(it, x, oy, col):
    it.fcircle(x - 6, 12 + oy, 5, col)
    it.fcircle(x + 2, 9 + oy, 7, col)
    it.fcircle(x + 9, 13 + oy, 4, col)
    it.rect(x - 6, 13 + oy, 15, 5, col)


def wx_icon(it, cx, oy, code, lvl, h, t=1.3):
    lvl = max(0, min(lvl, 2))
    fall = max(2, h - 18)
    dark = (110, 110, 130)

    def drops(n, speed, slant, ln):
        for i in range(n):
            ph = frac(i * 0.618)
            p = frac(t * speed + ph)
            x = cx - 11 + (i * 7) % 25 + slant
            dx = int(-slant * p * 3)
            y = oy + 18 + int(p * fall)
            it.line(x + dx, y, x + dx - 1 - slant // 2, y + ln, RAIN_C)

    def flakes(n, speed, sway, big):
        for i in range(n):
            ph = frac(i * 0.618 + 0.3)
            p = frac(t * speed + ph)
            x = cx - 12 + (i * 9) % 27 + lround(sway * math.sin(p * 4 * math.pi + ph * 6))
            y = oy + 18 + int(p * fall)
            it.px(x, y, (255, 255, 255))
            if big and i % 3 == 0:
                it.px(x + 1, y, (255, 255, 255))

    it.start_clipping(cx - 31, oy, cx + 32, oy + h + 1)
    if code == 100:                                   # clear night
        it.fcircle(cx - 2, 10 + oy, 7, (230, 230, 200))
        it.fcircle(cx + 2, 7 + oy, 6, BLACK)
        for i, (sx, sy) in enumerate([(-20, 3), (14, 2), (18, 14), (-16, 16), (11, 22), (-24, 10)]):
            b = 90 + int(165 * abs(math.sin(t * 1.5 + i * 1.3)))
            it.px(cx + sx, oy + sy, (b, b, b))
    elif code == 0:                                   # sunny
        b = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(t * math.pi / 2))
        ray = (int(255 * b), int(200 * b), int(40 * b))
        it.fcircle(cx, 10 + oy, 6, SUN)
        for k in range(8):
            a = k * math.pi / 4
            for r in range(8, 11):
                it.px(cx + lround(r * math.cos(a)), 10 + oy + lround(r * math.sin(a)), ray)
    elif code == 2:                                   # partly cloudy
        it.fcircle(cx - 6, 10 + oy, 6, SUN)
        cloud_at(it, cx + lround(3 * math.sin(t * math.pi / 2)), oy, CLOUD)
    elif 71 <= code <= 86:                            # snow
        cloud_at(it, cx, oy, CLOUD)
        flakes([5, 10, 18][lvl], 0.5 if lvl == 2 else 0.25, [1.0, 1.5, 2.5][lvl], lvl == 2)
    elif code >= 51 and code < 95:                    # rain
        cloud_at(it, cx, oy, dark if lvl == 2 else CLOUD)
        drops([5, 10, 18][lvl], [0.25, 0.5, 0.75][lvl], lvl, 2 + lvl)
    else:                                             # cloudy
        cloud_at(it, cx - 8 + lround(2 * math.sin(t * 1.6)), oy - 1, dark)
        cloud_at(it, cx + 2 + lround(3 * math.sin(t * 1.6 + 2)), oy + 3, CLOUD)
    it.end_clipping()


def wx_small(it, cx, cy, code):
    if code == 100:
        it.fcircle(cx, cy, 4, (230, 230, 200))
        it.fcircle(cx + 2, cy - 2, 3, BLACK)
        return
    if code <= 2:
        it.fcircle(cx if code == 0 else cx - 3, cy if code == 0 else cy - 2, 4 if code == 0 else 3, SUN)
    if code >= 1:
        it.fcircle(cx - 3, cy + 1, 3, CLOUD)
        it.fcircle(cx + 2, cy - 1, 4, CLOUD)
        it.rect(cx - 4, cy + 1, 10, 3, CLOUD)
    if 51 <= code <= 67 or 80 <= code <= 82:
        for i in (-3, 0, 3):
            it.px(cx + i, cy + 6, RAIN_C)


def can_icon(it, x, y, c, bg, lid_open=False):
    """8x11 trash can (the music screen's tag icon, a bit taller)."""
    if lid_open:
        it.line(x, y + 1, x + 5, y - 2, c)
        it.line(x, y + 2, x + 5, y - 1, c)
    else:
        it.rect(x, y, 7, 2, c)
    it.rect(x + 1, y + 2, 5, 9, c)
    it.hline(x + 2, y + 4, 3, bg)
    it.hline(x + 2, y + 7, 3, bg)


def temp_color(f):
    """Cold blue -> green -> amber -> red, for temperature-coloured marks."""
    stops = [(20, (60, 120, 255)), (40, (60, 200, 255)), (55, (40, 230, 80)),
             (70, (255, 176, 60)), (85, (255, 40, 30))]
    if f <= stops[0][0]:
        return stops[0][1]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if f <= t1:
            k = (f - t0) / (t1 - t0)
            return tuple(int(a + (b - a) * k) for a, b in zip(c0, c1))
    return stops[-1][1]


# ---------------------------------------------------------------------------
# Screens. Sample data: Thu Nov 5 is pickup day, so Wed Nov 4 is trash night.

def current_clock(it, hm, ampm, date):
    """Firmware: clock on the first two panels (full screen, no bars)."""
    it.print(128 // 2 - 6, 26, 32, AMBER, "CENTER", hm)
    it.print(126, 8, 8, DIM, "TOP_RIGHT", ampm)
    it.print(64, 54, 8, DIM, "CENTER", date)


def current_wx():
    it = Sign()
    current_clock(it, "2:47", "PM", "Thu Nov 05")
    cx = 160
    wx_icon(it, cx, 0, 2, 0, 20)
    it.txt(cx, 21, 16, WHITE, "TOP_CENTER", "58F")
    it.txt(cx, 35, 8, WHITE, "TOP_CENTER", "PARTLY")
    it.txt(cx, 43, 8, WHITE, "TOP_CENTER", "CLOUDY")
    it.txt(cx, 55, 8, DIM, "TOP_CENTER", "64/41")
    return it


def current_tmrw():
    it = Sign()
    current_clock(it, "8:15", "PM", "Wed Nov 04")
    cx = 160
    it.txt(cx, 2, 8, DIM, "TOP_CENTER", "TOMORROW")
    wx_icon(it, cx, 8, 61, 1, 26)
    it.txt(cx, 40, 8, WHITE, "TOP_CENTER", "RAIN")
    it.txt(cx, 52, 8, AMBER, "TOP_CENTER", "52/38")
    return it


def current_trash():
    it = Sign()
    current_clock(it, "8:15", "PM", "Wed Nov 04")
    cx = 160
    can, rib = (60, 160, 90), (30, 90, 50)
    it.rect(cx - 3, 4, 7, 2, can)
    it.rect(cx - 11, 6, 23, 3, can)
    it.rect(cx - 9, 10, 19, 22, can)
    for x in range(cx - 5, cx + 6, 5):
        it.rect(x, 13, 1, 16, rib)
    it.txt(cx, 40, 8, WHITE, "TOP_CENTER", "TRASH")
    it.txt(cx, 52, 8, AMBER, "TOP_CENTER", "TOMORROW")
    return it


def idea_tiles():
    """1. One job per panel: stacked time | calendar page | weather."""
    it = Sign()
    it.txt(30, 6, 32, AMBER, "TOP_CENTER", "02")
    it.txt(30, 29, 8, DIM, "TOP_CENTER", "PM")
    it.txt(30, 38, 32, WHITE, "TOP_CENTER", "47")
    # Calendar page.
    it.rect(72, 4, 48, 11, (150, 25, 20))
    it.txt(96, 7, 8, WHITE, "TOP_CENTER", "NOV")
    it.rect(72, 15, 48, 31, (28, 24, 20))
    it.txt(96, 20, 32, WHITE, "TOP_CENTER", "5")
    it.txt(96, 53, 8, DIM, "TOP_CENTER", "THURSDAY")
    cx = 160
    wx_icon(it, cx, 0, 2, 0, 20)
    it.txt(cx, 23, 16, WHITE, "TOP_CENTER", "58F")
    it.txt(cx, 40, 8, WHITE, "TOP_CENTER", "PT CLOUDY")
    it.txt(cx, 53, 8, DIM, "TOP_CENTER", "64/41")
    return it


def idea_strip():
    """2. Big clock and weather on top, a segmented status strip below."""
    it = Sign()
    it.txt(64, 10, 32, AMBER, "TOP_CENTER", "8:15")
    it.txt(122, 10, 8, DIM, "TOP_RIGHT", "PM")
    wx_icon(it, 162, 0, 3, 0, 22)
    it.txt(162, 28, 16, WHITE, "TOP_CENTER", "47F")
    y = 50
    segs = [(0, 54, (28, 24, 20)), (54, 66, (10, 25, 60)), (120, 72, (15, 60, 30))]
    for x, w, bg in segs:
        it.rect(x, y, w, 14, bg)
    it.txt(27, y + 5, 8, WHITE, "TOP_CENTER", "WED 4")
    wx_small(it, 63, y + 6, 61)
    it.txt(73, y + 5, 8, (140, 190, 255), "TOP_LEFT", "52/38")
    can_icon(it, 125, y + 2, (60, 200, 100), (15, 60, 30))
    it.txt(136, y + 5, 8, (60, 200, 100), "TOP_LEFT", "TRASH AM")
    return it


def idea_now_tmrw():
    """3. Clock panel plus NOW and TMRW cards side by side."""
    it = Sign()
    it.txt(32, 12, 16, AMBER, "TOP_CENTER", "8:15")
    it.txt(32, 28, 8, DIM, "TOP_CENTER", "PM")
    it.txt(32, 44, 8, DIM, "TOP_CENTER", "WED NOV 4")
    for x in (64, 128):
        it.vline(x, 4, 56, LINE_C)
    # NOW
    it.txt(96, 2, 8, DIM, "TOP_CENTER", "NOW")
    wx_icon(it, 96, 8, 3, 0, 24)
    it.txt(96, 36, 16, WHITE, "TOP_CENTER", "47F")
    it.txt(96, 53, 8, DIM, "TOP_CENTER", "CLOUDY")
    # TMRW, with a blue "colder" arrow next to the header
    it.txt(156, 2, 8, DIM, "TOP_CENTER", "TMRW")
    for i in range(3):
        it.hline(172 + i, 2 + i, 5 - 2 * i, RAIN_C)
    wx_icon(it, 160, 8, 61, 1, 24, t=2.1)
    it.txt(160, 36, 16, WHITE, "TOP_CENTER", "52/38")
    it.txt(160, 53, 8, (140, 190, 255), "TOP_CENTER", "RAIN 80%")
    return it


def idea_sparkline():
    """4. Clock + weather on top, next 24 h of temperature along the bottom."""
    it = Sign()
    it.txt(60, 6, 32, AMBER, "TOP_CENTER", "2:47")
    it.txt(124, 6, 8, DIM, "TOP_RIGHT", "PM")
    it.txt(64, 33, 8, DIM, "TOP_CENTER", "THU NOV 5")
    wx_icon(it, 160, 0, 2, 0, 20)
    it.txt(160, 22, 16, WHITE, "TOP_CENTER", "58F")
    it.txt(160, 36, 8, DIM, "TOP_CENTER", "64/41")
    # 24 hourly temps from 3 PM, rain 9 AM .. 1 PM tomorrow.
    temps = [58, 57, 55, 52, 50, 48, 47, 46, 45, 44, 43, 42, 41, 41, 42, 44, 47,
             49, 50, 51, 51, 52, 52, 51, 50]
    rain = set(range(18, 23))
    lo, hi, y0, y1 = 38, 60, 62, 53
    for x in range(W):
        h = x / 8
        i = min(int(h), 23)
        tf = temps[i] + (temps[i + 1] - temps[i]) * (h - i)
        y = round(y0 - (tf - lo) / (hi - lo) * (y0 - y1))
        c = temp_color(tf)
        it.vline(x, y + 1, 64 - y - 1, scale(c, 0.12))
        it.px(x, y, c)
        if i in rain and x % 2 == 0:
            it.px(x, 63, RAIN_C)
    for hx, lab in ((0, "NOW"), (48, "9P"), (96, "3A"), (144, "9A")):
        it.txt(hx + (1 if hx == 0 else 0), 46, 8, GRAY, "TOP_LEFT" if hx == 0 else "TOP_CENTER", lab)
    it.vline(0, 52, 12, WHITE)
    return it


def idea_sky():
    """5. Sky background with the sun's path from sunrise to sunset."""
    it = Sign()
    horizon = 50
    top, low = (4, 6, 26), (70, 28, 6)
    for y in range(horizon):
        k = (y / (horizon - 1)) ** 1.6
        it.hline(0, y, W, tuple(int(a + (b - a) * k) for a, b in zip(top, low)))
    it.hline(0, horizon, W, (90, 50, 15))
    # Sunrise 6:29 AM at x=6, sunset 4:33 PM at x=186; now 4:21 PM.
    def arc(f):
        return 6 + f * 180, horizon - 1 - 44 * (1 - (2 * f - 1) ** 2)
    for k in range(0, 61):
        x, y = arc(k / 60)
        if k % 2 == 0:
            it.px(round(x), round(y), (110, 80, 40))
    sx, sy = arc(0.98)
    it.start_clipping(0, 0, W, horizon)
    it.fcircle(round(sx), round(sy), 5, (120, 70, 10))
    it.fcircle(round(sx), round(sy), 3, SUN)
    it.end_clipping()
    it.txt(96, 14, 32, WHITE, "TOP_CENTER", "4:21")
    it.txt(3, 55, 8, DIM, "TOP_LEFT", "THU NOV 5")
    it.txt(96, 55, 8, WHITE, "TOP_CENTER", "58F")
    it.txt(189, 55, 8, AMBER, "TOP_RIGHT", "SUNSET 4:33")
    return it


def idea_trash_alarm():
    """6. Trash night, escalated: bins still in at 9:30 PM, green border pulse."""
    it = Sign()
    g = (40, 200, 90)
    it.rect(0, 0, W, 1, g)
    it.rect(0, H - 1, W, 1, g)
    it.rect(0, 0, 1, H, g)
    it.rect(W - 1, 0, 1, H, g)
    current_clock(it, "9:30", "PM", "Wed Nov 04")
    cx = 160
    can, rib = (60, 160, 90), (30, 90, 50)
    # Lid flipped open.
    for d in range(3):
        it.line(cx - 11, 8 + d, cx + 3, 1 + d, can)
    it.rect(cx - 9, 10, 19, 22, can)
    for x in range(cx - 5, cx + 6, 5):
        it.rect(x, 13, 1, 16, rib)
    it.txt(cx, 40, 8, WHITE, "TOP_CENTER", "BINS OUT")
    it.txt(cx, 52, 8, AMBER, "TOP_CENTER", "TONIGHT")
    return it


def idea_night():
    """7. Late night: dim red clock only, tiny moon and temperature."""
    it = Sign()
    it.txt(96, 16, 32, (110, 14, 6), "TOP_CENTER", "1:12")
    it.fcircle(176, 52, 3, (60, 14, 6))
    it.fcircle(178, 50, 2, BLACK)
    it.txt(168, 50, 8, (60, 14, 6), "TOP_RIGHT", "41F")
    return it


def idea_morning():
    """8. Morning briefing on pickup day."""
    it = Sign()
    it.txt(32, 6, 16, AMBER, "TOP_CENTER", "7:05")
    it.txt(32, 21, 8, DIM, "TOP_CENTER", "AM  THU 5")
    it.rect(2, 34, 60, 26, (15, 60, 30))
    can_icon(it, 6, 41, (60, 200, 100), (15, 60, 30))
    it.txt(38, 40, 8, (60, 200, 100), "TOP_CENTER", "TRASH")
    it.txt(38, 50, 8, (60, 200, 100), "TOP_CENTER", "DAY")
    it.vline(66, 4, 56, LINE_C)
    rows = [
        (8, lambda y: wx_small(it, 78, y + 2, 2), "64/41 PT CLOUDY", WHITE),
        (26, lambda y: it.fcircle(78, y + 3, 2, RAIN_C), "RAIN 10% TODAY", (140, 190, 255)),
        (44, lambda y: it.rect(75, y, 7, 6, AMBER), "JACKET: YES", AMBER),
    ]
    for y, icon, label, c in rows:
        icon(y)
        it.txt(90, y, 8, c, "TOP_LEFT", label)
    return it


SCREENS = [
    ("current_wx", "Now: clock + weather card (2:47 PM)", current_wx),
    ("current_tmrw", "Now: TOMORROW card after 7 PM", current_tmrw),
    ("current_trash", "Now: TRASH card, night before pickup", current_trash),
    ("idea1_tiles", "Idea 1: one job per panel", idea_tiles),
    ("idea2_strip", "Idea 2: big clock + status strip", idea_strip),
    ("idea3_now_tmrw", "Idea 3: NOW and TMRW cards", idea_now_tmrw),
    ("idea4_sparkline", "Idea 4: 24 h temperature line", idea_sparkline),
    ("idea5_sky", "Idea 5: sky + sun path", idea_sky),
    ("idea6_trash_alarm", "Idea 6: trash night, escalated", idea_trash_alarm),
    ("idea7_night", "Idea 7: late-night dim red", idea_night),
    ("idea8_morning", "Idea 8: pickup-day morning brief", idea_morning),
]


# ---------------------------------------------------------------------------
# LED look: every pixel becomes a soft round dot; unlit LEDs stay faintly visible.

def led(img, s=6, bg=(10, 10, 11), off=(26, 26, 28)):
    a = np.asarray(img, np.float32) / 255
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:s, 0:s]
    c = (s - 1) / 2
    dot = np.clip(s * 0.40 - np.hypot(yy - c, xx - c) + 0.5, 0, 1)
    mask = np.tile(dot, (h, w))[..., None]
    big = np.repeat(np.repeat(a, s, 0), s, 1)
    lit = np.maximum(big ** 0.85, np.array(off) / 255)   # LEDs look brighter than sRGB
    out = np.array(bg) / 255 * (1 - mask) + lit * mask
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    label_f = ImageFont.truetype("DejaVuSans.ttf", 22)
    tiles = []
    for name, title, fn in SCREENS:
        im = led(fn().image())
        im.save(os.path.join(OUT, name + ".png"))
        tiles.append((title, im))
    # Contact sheet, one screen per row.
    tw, th = tiles[0][1].size
    pad, lab = 24, 34
    sheet = Image.new("RGB", (tw + 2 * pad, len(tiles) * (th + lab + pad) + pad), (32, 32, 34))
    d = ImageDraw.Draw(sheet)
    y = pad
    for title, im in tiles:
        d.text((pad, y), title, font=label_f, fill=(220, 220, 220))
        sheet.paste(im, (pad, y + lab))
        y += th + lab + pad
    sheet.save(os.path.join(OUT, "sheet.png"))
    print("wrote", len(tiles), "screens to", OUT)


if __name__ == "__main__":
    main()
