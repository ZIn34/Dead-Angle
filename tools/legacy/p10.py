# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# The pack draws its weapons muzzle-down. Turn them around, keeping the grip
# at the hands and the barrel pointing where the character is facing.
sub("""      if (wb) {
        var ww = wb[2] - wb[0], wh = wb[3] - wb[1];
        var m = (WEAP_MUL[weaponKey] || 1) * CHAR.gunS;
        // anchored by the grip, so a pistol and a shotgun both sit in the hands
        g.drawImage(PACK_IMG.weapons, wb[0], wb[1], ww, wh,
                    CHAR.cx - ww * m / 2, CHAR.cy + CHAR.gripY - wh * m, ww * m, wh * m);
      }""",
"""      if (wb) {
        var ww = wb[2] - wb[0], wh = wb[3] - wb[1];
        var m = (WEAP_MUL[weaponKey] || 1) * CHAR.gunS;
        // Grip stays at the hands; the sprite is turned 180 so the barrel
        // leads, because the pack draws every weapon pointing down.
        g.save();
        g.translate(CHAR.cx, CHAR.cy + CHAR.gripY - wh * m / 2);
        g.rotate(Math.PI);
        g.drawImage(PACK_IMG.weapons, wb[0], wb[1], ww, wh,
                    -ww * m / 2, -wh * m / 2, ww * m, wh * m);
        g.restore();
      }""")

# How far in front of the body the barrel actually ends, so shots leave the
# muzzle instead of the chest.
sub("""  function charFor(e) {""",
"""  function muzzleOff(e) {
    var w = curW(e), sl = curSlot(e);
    var base = e.r + 6;
    if (!PACK_READY || !w || !sl || !PACK.weapons) return base;
    var wi = WEAP_IDX[sl.key];
    var wb = PACK.weapons[wi === undefined ? 2 : wi];
    if (!wb) return base;
    var h = (wb[3] - wb[1]) * (WEAP_MUL[sl.key] || 1) * CHAR.gunS;
    var px = -CHAR.gripY + h;                        // canvas pixels forward
    return px / CHAR.H * (e.r * CHAR.draw);
  }

  function charFor(e) {""")

sub("""    var spread = w.spread + (e.bot ? DIFF[difficulty].spread : (e._spd > 200 ? 0.055 : (e._spd > 0 ? 0.022 : 0)));
    var muzzle = e.r + 6;""",
"""    var spread = w.spread + (e.bot ? DIFF[difficulty].spread : (e._spd > 200 ? 0.055 : (e._spd > 0 ? 0.022 : 0)));
    var muzzle = muzzleOff(e);
    // never let a long barrel push the shot through a wall you are hugging
    if (wallAt(e.x + Math.cos(e.ang) * muzzle, e.y + Math.sin(e.ang) * muzzle)) muzzle = e.r + 6;""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p10 applied')
