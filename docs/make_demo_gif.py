#!/usr/bin/env python3
"""Render docs/demo_raw.txt (real nav2_doctor reports) + docs/demo_events.txt (real nav2_fault_inject log)
into docs/demo.gif, placing each event by its wall-clock time."""
import os
import re

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 15)
COL = {'31': (255, 95, 95), '33': (240, 200, 80), '32': (110, 220, 130)}
W, H, LH = 980, 380, 19
BG, FG, DIM, PANEL = (22, 24, 30), (205, 205, 205), (120, 125, 135), (48, 40, 28)

events = [l for l in open(os.path.join(HERE, 'demo_events.txt')).read().splitlines() if re.match(r'\d\d:\d\d:\d\d ', l)]
reports, cur = [], None                      # reports: (time, lines)
for line in open(os.path.join(HERE, 'demo_raw.txt')).read().splitlines():
    m = re.match(r'--- nav2_doctor (\d\d:\d\d:\d\d)', line)
    if m:
        cur = [line]
        reports.append((m.group(1), cur))
    elif cur is not None and line.strip():
        cur.append(line)


def segs(line):
    out, color = [], FG
    for part in re.split(r'(\x1b\[[0-9;]*m)', line):
        m = re.fullmatch(r'\x1b\[([0-9;]*)m', part)
        if m:
            color = COL.get(m.group(1).split(';')[-1], FG)
        elif part:
            out.append((part, color))
    return out


def frame(i):
    t, lines = reports[i]
    evs = [e for e in events if e[:8] <= t]
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 26], fill=(40, 43, 52))
    d.text((12, 5), 'nav2_fault_inject  +  nav2_doctor        (live Gazebo maze sim, real output)', font=FONT, fill=DIM)
    d.rectangle([0, 30, W, 30 + 2 * LH + 10], fill=PANEL)
    d.text((14, 36), '$ nav2_fault_inject hang parameter_bridge --for 8', font=FONT, fill=(240, 200, 120))
    d.text((14, 36 + LH), evs[-1] if evs else '(not started)', font=FONT, fill=(240, 200, 120) if evs else DIM)
    y = 36 + 2 * LH + 20
    for ln in lines[:12]:
        x = 14
        for text, color in segs(ln):
            d.text((x, y), text, font=FONT, fill=color)
            x += d.textlength(text, font=FONT)
        y += LH
    return img


frames = [frame(i) for i in range(len(reports))]
dur = [700] * len(frames)
dur[-1] = 2500
frames[0].save(os.path.join(HERE, 'demo.gif'), save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=True)
print(len(frames), 'frames')
