# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ------------------------------------------------- 1. rifle fires faster ----
sub("""    silenced: { name: 'RIFLE',    dmg: 16, pellets: 1, interval: 0.20,""",
    """    silenced: { name: 'RIFLE',    dmg: 16, pellets: 1, interval: 0.115,""")

# ------------------------------------------------- 2. a sniper of its own ---
sub("""  function buildChar(skin, weaponKey) {""",
"""  // The pack ships three guns, so the sniper gets a stand-in drawn in the same
  // language: flat fills, heavy black outline, muzzle down like the rest.
  function makeSniper() {
    var W = 30, H = 208;
    var c = document.createElement('canvas');
    c.width = W; c.height = H;
    var g = c.getContext('2d');
    g.lineJoin = 'round';
    g.strokeStyle = '#000';
    g.lineWidth = 4;
    function slab(x, y, w, h, fill, r) {
      g.beginPath();
      if (g.roundRect) g.roundRect(x, y, w, h, r || 3);
      else g.rect(x, y, w, h);
      g.fillStyle = fill;
      g.fill();
      g.stroke();
    }
    slab(6, 168, 18, 36, '#8a9099', 4);      // muzzle brake, at the bottom
    slab(11, 96, 8, 80, '#9aa1aa', 3);       // barrel
    slab(9, 92, 12, 26, '#4a4a4a', 3);       // magazine
    slab(5, 30, 20, 70, '#2a2a2a', 5);       // receiver
    slab(7, 4, 16, 34, '#6b5030', 6);        // stock
    slab(3, 44, 24, 16, '#1c1c1c', 5);       // scope body
    slab(9, 38, 12, 8, '#3c4f63', 3);        // scope lens
    return c;
  }

  // Where a weapon's artwork lives: the pack sheet, or our own stand-in.
  function weaponArt(key) {
    if (key === 'rifle' && PACK_IMG.sniper) {
      var sc = PACK_IMG.sniper;
      return { img: sc, b: [0, 0, sc.width, sc.height] };
    }
    if (!PACK_IMG.weapons || !PACK.weapons) return null;
    var wi = WEAP_IDX[key];
    var b = PACK.weapons[wi === undefined ? 2 : wi];
    return b ? { img: PACK_IMG.weapons, b: b } : null;
  }

  function buildChar(skin, weaponKey) {""")

sub("""    grab('skins', cfg.skins);
    grab('weapons', cfg.weapons);""",
"""    grab('skins', cfg.skins);
    grab('weapons', cfg.weapons);
    PACK_IMG.sniper = makeSniper();""")

sub("""    if (weaponKey && PACK_IMG.weapons && PACK.weapons) {
      var wi = WEAP_IDX[weaponKey];
      var wb = PACK.weapons[wi === undefined ? 2 : wi];
      if (wb) {
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
      }
    }""",
"""    var art = weaponKey ? weaponArt(weaponKey) : null;
    if (art) {
      var wb = art.b;
      var ww = wb[2] - wb[0], wh = wb[3] - wb[1];
      var m = (WEAP_MUL[weaponKey] || 1) * CHAR.gunS;
      // Grip stays at the hands; the sprite is turned 180 so the barrel
      // leads, because the pack draws every weapon pointing down.
      g.save();
      g.translate(CHAR.cx, CHAR.cy + CHAR.gripY - wh * m / 2);
      g.rotate(Math.PI);
      g.drawImage(art.img, wb[0], wb[1], ww, wh, -ww * m / 2, -wh * m / 2, ww * m, wh * m);
      g.restore();
    }""")

sub("""    var wi = WEAP_IDX[sl.key];
    var wb = PACK.weapons[wi === undefined ? 2 : wi];
    if (!wb) return base;
    var h = (wb[3] - wb[1]) * (WEAP_MUL[sl.key] || 1) * CHAR.gunS;""",
"""    var art = weaponArt(sl.key);
    if (!art) return base;
    var h = (art.b[3] - art.b[1]) * (WEAP_MUL[sl.key] || 1) * CHAR.gunS;""")

sub("""      if (it.type === 'gun' && PACK_IMG.weapons && PACK.weapons) {
        var gi = WEAP_IDX[it.key];
        var gb = PACK.weapons[gi === undefined ? 2 : gi];
        if (gb) {
          var gw = gb[2] - gb[0], gh = gb[3] - gb[1];
          var dh = 20, dw = dh * (gw / gh);
          ctx.save();
          ctx.translate(it.x, it.y);
          ctx.rotate(it.spin || 0);
          ctx.drawImage(PACK_IMG.weapons, gb[0], gb[1], gw, gh, -dw / 2, -dh / 2, dw, dh);
          ctx.restore();
          ctx.globalAlpha = 1;
          return;
        }
      }""",
"""      if (it.type === 'gun') {
        var ga = weaponArt(it.key);
        if (ga) {
          var gb = ga.b;
          var gw = gb[2] - gb[0], gh = gb[3] - gb[1];
          var dh = 20, dw = dh * (gw / gh);
          ctx.save();
          ctx.translate(it.x, it.y);
          ctx.rotate(it.spin || 0);
          ctx.drawImage(ga.img, gb[0], gb[1], gw, gh, -dw / 2, -dh / 2, dw, dh);
          ctx.restore();
          ctx.globalAlpha = 1;
          return;
        }
      }""")

# ------------------------------------------- 3. world keeps its own ground --
sub("""    var packed = PACK_READY && PACK;
    var grassy = !packed && (mode === 'br' && mapKind === 'world');""",
"""    // The world map keeps its dirt; everywhere else takes the pack's tiles.
    var grassy = (mode === 'br' && mapKind === 'world');
    var packed = PACK_READY && PACK && !grassy;""")

# ------------------------------------------- 4. yellow tracers --------------
sub("""      ctx.strokeStyle = b.owner === player.id ? 'rgba(160,255,240,.9)' : 'rgba(255,190,120,.9)';
      ctx.lineWidth = 1.8 / zoom;
      ctx.beginPath();
      ctx.moveTo(b.x, b.y);
      ctx.lineTo(b.x - b.vx * 0.016, b.y - b.vy * 0.016);
      ctx.stroke();""",
"""      // every round draws the same yellow streak with a hot core
      var tailX = b.x - b.vx * 0.019, tailY = b.y - b.vy * 0.019;
      ctx.strokeStyle = 'rgba(255,198,52,.55)';
      ctx.lineWidth = 3.6 / zoom;
      ctx.beginPath(); ctx.moveTo(b.x, b.y); ctx.lineTo(tailX, tailY); ctx.stroke();
      ctx.strokeStyle = 'rgba(255,247,196,.95)';
      ctx.lineWidth = 1.3 / zoom;
      ctx.beginPath(); ctx.moveTo(b.x, b.y); ctx.lineTo(tailX, tailY); ctx.stroke();""")

# ------------------------------------------- 5. closer camera ---------------
sub("""  var VIEW_BASE = 310;             // sight radius the camera zoom is built around""",
    """  var VIEW_BASE = 250;             // sight radius the camera zoom is built around""")
sub("""  var VIEW_R = VIEW_BASE;          // current sight radius, set per match""",
    """  var VIEW_R = VIEW_BASE;          // current sight radius, set per match""")

# bots shouldn't out-see the player now that sight is shorter
sub("""    { react: 0.52, spread: 0.105, sight: 230,""", """    { react: 0.52, spread: 0.105, sight: 195,""")
sub("""    { react: 0.28, spread: 0.050, sight: 285,""", """    { react: 0.28, spread: 0.050, sight: 235,""")
sub("""    { react: 0.14, spread: 0.022, sight: 345,""", """    { react: 0.14, spread: 0.022, sight: 285,""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p11 applied')
