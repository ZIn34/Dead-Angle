# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

sub("""      fireT: 0, reloadT: 0, stepT: 0, useT: 0, respawnT: 0, meleeT: 0, swingT: 0,""",
    """      fireT: 0, reloadT: 0, stepT: 0, useT: 0, respawnT: 0, meleeT: 0, swingT: 0, throwT: 0,""")

sub("""      if (e.meleeT > 0) e.meleeT -= dt;
      if (e.swingT > 0) e.swingT -= dt;""",
"""      if (e.meleeT > 0) e.meleeT -= dt;
      if (e.swingT > 0) e.swingT -= dt;
      if (e.throwT > 0) e.throwT -= dt;""")

sub("""    var a = (ang === undefined) ? e.ang : ang;
    var v = power || 560;""",
"""    var a = (ang === undefined) ? e.ang : ang;
    var v = power || 560;
    e.throwT = 0.34;""")

# the throwing arm comes over the shoulder and the body turns into it
sub("""    var kick = e.animFire > 0 ? (e.animFire / 0.17) * 7 : 0;   // recoil, pushed back""",
"""    var kick = e.animFire > 0 ? (e.animFire / 0.17) * 7 : 0;   // recoil, pushed back
    var lob = e.throwT > 0 ? Math.sin((1 - e.throwT / 0.34) * Math.PI) : 0;""")

sub("""    limb(4, -CHAR.armX + stride * 2, CHAR.armY - stride * 4 + kick, CHAR.armRot + stride * 0.09);
    limb(0, stride * 2, CHAR.torsoY, stride * 0.03);                                 // torso sway""",
"""    limb(4, -CHAR.armX + stride * 2 - lob * 5, CHAR.armY - stride * 4 + kick + lob * 8, CHAR.armRot + stride * 0.09);
    limb(0, stride * 2 + lob * 4, CHAR.torsoY, stride * 0.03 + lob * 0.12);          // torso turns into it""")

sub("""    limb(3, CHAR.armX + stride * 2, CHAR.armY + stride * 4 + kick, CHAR.armRot - stride * 0.09);""",
    """    limb(3, CHAR.armX + stride * 2 + lob * 7, CHAR.armY + stride * 4 + kick - lob * 34, CHAR.armRot - stride * 0.09 - lob * 1.15);""")

# ---------------------------------------------------------------- contact ---
# On maps this size a random destination means they almost never meet, so they
# were wandering instead of fighting. Give them somebody to walk towards.
sub("""          if (want) goal = want;
          else {
            var ft2 = floorTiles[rnd(floorTiles.length)];""",
"""          if (!want && Math.random() < 0.7) {
            var hunt = [];
            for (var hq = 0; hq < ents.length; hq++) {
              var ho = ents[hq];
              if (ho.alive && foes(e, ho)) hunt.push(ho);
            }
            if (hunt.length) {
              var mark = hunt[rnd(hunt.length)];
              want = { x: mark.x + rr(-140, 140), y: mark.y + rr(-140, 140) };
            }
          }
          if (want) goal = want;
          else {
            var ft2 = floorTiles[rnd(floorTiles.length)];""")

# and let them see a little further than the camera shows you
sub("""    { react: 0.52, spread: 0.105, sight: 195,""", """    { react: 0.52, spread: 0.105, sight: 225,""")
sub("""    { react: 0.28, spread: 0.050, sight: 235,""", """    { react: 0.28, spread: 0.050, sight: 275,""")
sub("""    { react: 0.14, spread: 0.022, sight: 285,""", """    { react: 0.14, spread: 0.022, sight: 330,""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p30 applied')
