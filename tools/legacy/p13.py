# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# The pack ships loose limbs and no walk frames, so the cycle is driven here:
# legs rock, arms swing in opposition, the torso sways and the gun rides the
# hands. Drawing the pieces live costs five blits instead of one, which is
# nothing, and it means recoil and stride react to what the fighter is doing.
sub("""  function charFor(e) {
    var sl = curSlot(e);
    var key = e.skin + '|' + (sl ? sl.key : 'none');
    var cv = charCache[key];
    if (!cv) { cv = buildChar(e.skin, sl ? sl.key : null); charCache[key] = cv; }
    return cv;
  }""",
"""  function charFor(e) {
    var sl = curSlot(e);
    var key = e.skin + '|' + (sl ? sl.key : 'none');
    var cv = charCache[key];
    if (!cv) { cv = buildChar(e.skin, sl ? sl.key : null); charCache[key] = cv; }
    return cv;
  }

  // Draw a fighter limb by limb, posed for this instant.
  function drawPacked(e) {
    var parts = PACK.skins[e.skin % PACK.skins.length];
    var sheet = PACK_IMG.skins;
    if (!parts || !sheet) return false;

    var stride = e.moving ? Math.sin(e.animT * 8.5) : Math.sin(matchTime * 1.7 + e.id) * 0.18;
    var kick = e.animFire > 0 ? (e.animFire / 0.17) * 7 : 0;   // recoil, pushed back
    var k = (e.r * CHAR.draw) / CHAR.H;

    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.rotate(e.ang + Math.PI / 2);          // the kit is drawn facing up
    ctx.scale(k, k);
    ctx.translate(-CHAR.W / 2, -CHAR.H / 2);  // into composing-canvas space

    function limb(idx, dx, dy, rot) {
      var b = parts[idx];
      if (!b) return;
      var w = b[2] - b[0], h = b[3] - b[1];
      ctx.save();
      ctx.translate(CHAR.cx + dx, CHAR.cy + dy);
      if (rot) ctx.rotate(rot);
      ctx.drawImage(sheet, b[0], b[1], w, h, -w / 2, -h / 2, w, h);
      ctx.restore();
    }

    limb(1, stride * 4, CHAR.legsY, stride * 0.11);                                  // legs rock
    limb(4, -CHAR.armX + stride * 2, CHAR.armY - stride * 4 + kick, CHAR.armRot + stride * 0.09);
    limb(0, stride * 2, CHAR.torsoY, stride * 0.03);                                 // torso sway

    var sl = curSlot(e);
    var art = sl ? weaponArt(sl.key) : null;
    if (art) {
      var wb = art.b, ww = wb[2] - wb[0], wh = wb[3] - wb[1];
      var m = (WEAP_MUL[sl.key] || 1) * CHAR.gunS;
      ctx.save();
      ctx.translate(CHAR.cx, CHAR.cy + CHAR.gripY + kick - wh * m / 2);
      ctx.rotate(Math.PI);
      ctx.drawImage(art.img, wb[0], wb[1], ww, wh, -ww * m / 2, -wh * m / 2, ww * m, wh * m);
      ctx.restore();
    }

    limb(3, CHAR.armX + stride * 2, CHAR.armY + stride * 4 + kick, CHAR.armRot - stride * 0.09);
    limb(2, stride * 1.5, CHAR.headY, 0);                                            // head last
    ctx.restore();
    return true;
  }""")

sub("""      var cv = charFor(e);
      ctx.save();
      ctx.translate(e.x, e.y);
      ctx.rotate(e.ang + Math.PI / 2);        // the kit is drawn facing up
      var ch = e.r * CHAR.draw, cwd = ch * (cv.width / cv.height);
      ctx.drawImage(cv, -cwd / 2, -ch / 2, cwd, ch);
      ctx.restore();""",
"""      drawPacked(e);""")

sub("""    silenced: { name: 'RIFLE',    dmg: 16, pellets: 1, interval: 0.115,  mag: 14,""",
    """    silenced: { name: 'RIFLE',    dmg: 16, pellets: 1, interval: 0.115,  mag: 30,""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p13 applied')
