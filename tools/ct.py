# -*- coding: utf-8 -*-
"""Compose a character the way the game does, so offsets can be tuned by
looking at the result instead of guessing."""
import json, sys
from PIL import Image

P = json.load(open('assets/pack.json'))
skins = Image.open('assets/skins.png').convert('RGBA')
weaps = Image.open('assets/weapons.png').convert('RGBA')

CHAR = dict(W=200, H=300, cx=100, cy=195,
            legsY=26, torsoY=4, headY=-2,
            armX=42, armY=-18, armRot=180,
            gripY=-62, gunS=70)
WEAP_IDX = {'pistol': 2, 'smg': 3, 'silenced': 3, 'shotgun': 4, 'rifle': 4}

for a in sys.argv[1:]:
    if '=' in a:
        k, v = a.split('=', 1)
        CHAR[k] = int(v)


def part(canvas, idx, skin, dx, dy, rot=0):
    b = P['skins'][skin][idx]
    im = skins.crop((b[0], b[1], b[2], b[3]))
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(im, (int(CHAR['cx'] + dx - im.size[0] / 2),
                                int(CHAR['cy'] + dy - im.size[1] / 2)))


def compose(skin, weapon):
    c = Image.new('RGBA', (CHAR['W'], CHAR['H']), (0, 0, 0, 0))
    part(c, 1, skin, 0, CHAR['legsY'])
    part(c, 4, skin, -CHAR['armX'], CHAR['armY'], CHAR['armRot'])
    part(c, 0, skin, 0, CHAR['torsoY'])
    if weapon:
        b = P['weapons'][WEAP_IDX[weapon]]
        im = weaps.crop((b[0], b[1], b[2], b[3]))
        k = CHAR['gunS'] / 100.0
        im = im.resize((max(1, int(im.size[0] * k)), max(1, int(im.size[1] * k))), Image.LANCZOS)
        # anchor the grip at the hands so a pistol and a shotgun both sit right
        im = im.rotate(180)      # pack weapons are drawn muzzle-down
        c.alpha_composite(im, (int(CHAR['cx'] - im.size[0] / 2),
                               int(CHAR['cy'] + CHAR['gripY'] - im.size[1])))
    part(c, 3, skin, CHAR['armX'], CHAR['armY'], CHAR['armRot'])
    part(c, 2, skin, 0, CHAR['headY'])
    return c


sheet = Image.new('RGBA', (CHAR['W'] * 4, CHAR['H']), (30, 36, 46, 255))
for i, w in enumerate(['pistol', 'smg', 'shotgun', None]):
    sheet.alpha_composite(compose(i, w), (CHAR['W'] * i, 0))
sheet.save('ct.png')
print('ct.png', sheet.size, CHAR)
