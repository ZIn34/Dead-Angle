# -*- coding: utf-8 -*-
"""Render the throw pose across its timeline, using the same maths as the game.
The character faces UP, so forward is -Y."""
import json, math
from PIL import Image

P = json.load(open('assets/pack.json'))
skins = Image.open('assets/skins.png').convert('RGBA')
weaps = Image.open('assets/weapons.png').convert('RGBA')

W, H, CX, CY = 200, 300, 100, 195
legsY, torsoY, headY = 26, 4, -2
armX, armY, armRot = 42, -18, 180
gripY, gunS = -62, 0.70
SKIN = 1


def pose(tp):
    """reach: + is forward.  twist: arm splay."""
    if tp < 0:
        return 0.0, 0.0
    if tp < 0.35:
        a = tp / 0.35
        return -13.0 * a, -0.30 * a                 # wind up, arm drops back
    b = (tp - 0.35) / 0.65
    sw = math.sin(b * math.pi * 0.85)
    return -13.0 * (1 - b) + 42.0 * sw, -0.30 * (1 - b) + 0.55 * sw


def limb(canvas, idx, dx, dy, rot_deg):
    b = P['skins'][SKIN][idx]
    im = skins.crop((b[0], b[1], b[2], b[3]))
    if rot_deg:
        im = im.rotate(rot_deg, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(im, (int(CX + dx - im.size[0] / 2), int(CY + dy - im.size[1] / 2)))


def frame(tp):
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    reach, twist = pose(tp)
    td = math.degrees(twist)
    limb(c, 1, 0, legsY, 0)
    limb(c, 4, -armX - reach * 0.12, armY + reach * 0.18, armRot)
    limb(c, 0, reach * 0.10, torsoY, td * 0.25)
    b = P['weapons'][3]
    im = weaps.crop((b[0], b[1], b[2], b[3])).rotate(180)
    k = gunS
    im = im.resize((max(1, int(im.size[0] * k)), max(1, int(im.size[1] * k))), Image.LANCZOS)
    c.alpha_composite(im, (int(CX - im.size[0] / 2), int(CY + gripY - im.size[1])))
    limb(c, 3, armX + reach * 0.16, armY - reach, armRot + td)      # throwing arm
    limb(c, 2, 0, headY, 0)
    return c


steps = [-1, 0.15, 0.35, 0.5, 0.65, 0.8, 1.0]
sheet = Image.new('RGBA', (W * len(steps), H), (30, 36, 46, 255))
for i, tp in enumerate(steps):
    sheet.alpha_composite(frame(tp), (W * i, 0))
sheet.save('ct2.png')
print('ct2.png', sheet.size, 'frames', steps)
