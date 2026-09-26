# -*- coding: utf-8 -*-
"""Turn the single muzzle-flash artwork into an 8-frame sheet.

The game anchors a flash by the LEFT edge of the frame, vertically centred, at
the muzzle - so every frame keeps the barrel end pinned there and the flash
blooms out to the right.
"""
import os
from PIL import Image

SRC = os.path.expanduser('~/Downloads/Screenshot_2026-08-06_161737-removebg-preview (1).png')
OUT = 'assets/flash.png'

im = Image.open(SRC).convert('RGBA')
print('source', im.size)

bb = im.getbbox()
im = im.crop(bb)
print('cropped to content', im.size)

# the game draws a frame at half its pixel size, and a flash should read as
# roughly a third of the character's height - so bring the art down to suit
BASE = 0.58
im = im.resize((max(1, int(im.size[0] * BASE)), max(1, int(im.size[1] * BASE))), Image.LANCZOS)
print('scaled for the game', im.size)

W, H = im.size
SCALE = [0.42, 0.78, 1.00, 1.06, 0.98, 0.84, 0.64, 0.44]
ALPHA = [0.95, 1.00, 1.00, 0.94, 0.80, 0.60, 0.38, 0.18]
N = len(SCALE)

FW = int(round(W * 1.06)) + 2
FH = int(round(H * 1.06)) + 2
sheet = Image.new('RGBA', (FW * N, FH), (0, 0, 0, 0))

for i in range(N):
    sc, al = SCALE[i], ALPHA[i]
    w = max(1, int(round(W * sc)))
    h = max(1, int(round(H * sc)))
    f = im.resize((w, h), Image.LANCZOS)
    if al < 1:
        a = f.getchannel('A').point(lambda v: int(v * al))
        f.putalpha(a)
    # barrel end pinned to the left edge, centred vertically
    sheet.alpha_composite(f, (i * FW, (FH - h) // 2))

sheet.save(OUT)
print('%s  %dx%d  frame %dx%d  %d frames' % (OUT, sheet.size[0], sheet.size[1], FW, FH, N))
