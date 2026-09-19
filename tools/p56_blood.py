# -*- coding: utf-8 -*-
"""Better blood: directional spray, droplets that land and stain, pools under
the fallen, drips from the badly hurt, green for the infected, and a switch."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- setting ------------------------------------------------------------------
sub("""var SET = { vol: 66, music: 45, dead: 18, shake: true, minimap: true };""",
    """var SET = { vol: 66, music: 45, dead: 18, shake: true, minimap: true, blood: true };""")
sub("""[['setShake', 'shake'], ['setMap', 'minimap']]""", """[['setShake', 'shake'], ['setMap', 'minimap'], ['setBlood', 'blood']]""")
s = s.replace("""[['setShake', 'shake'], ['setMap', 'minimap']]""", """[['setShake', 'shake'], ['setMap', 'minimap'], ['setBlood', 'blood']]""")

# ---- the system -----------------------------------------------------------------
sub("""  function fire(e) {""", r"""  // ---- blood ------------------------------------------------------------
  // Droplets are thrown along the shot, arc through the air and land as
  // stains that stay on the ground. The fallen leave a spreading pool; the
  // badly hurt leave drips behind them. The infected bleed a dark green.
  var drops = [], splats = [], SPLAT_MAX = 320, splatArt = null;
  var BLOOD_RED = ['#6e0b10', '#8a1016', '#a3161c'], BLOOD_ZOMB = ['#2f4312', '#3f5a18', '#557522'];
  function bakeSplats() {
    // a few irregular stain shapes, drawn once and stamped from then on
    splatArt = { red: [], zomb: [] };
    [['red', BLOOD_RED], ['zomb', BLOOD_ZOMB]].forEach(function (pal) {
      for (var v = 0; v < 6; v++) {
        var c = document.createElement('canvas'); c.width = c.height = 96;
        var g = c.getContext('2d');
        g.translate(48, 48);
        g.fillStyle = pal[1][0];
        var n = 7 + (v % 3) * 2;
        g.beginPath();
        for (var k = 0; k <= n; k++) {                        // a lumpy blob
          var a = k / n * 6.2832, rr0 = 22 + ((v * 37 + k * 53) % 11);
          var px = Math.cos(a) * rr0, py = Math.sin(a) * rr0 * (0.8 + (v % 2) * 0.2);
          if (k === 0) g.moveTo(px, py); else g.quadraticCurveTo(Math.cos(a - 3.1416 / n) * (rr0 + 6), Math.sin(a - 3.1416 / n) * (rr0 + 4), px, py);
        }
        g.fill();
        g.fillStyle = pal[1][1];                                // wetter middle
        g.beginPath(); g.ellipse(-3, -2, 14, 11, v, 0, 6.2832); g.fill();
        g.fillStyle = pal[1][0];
        for (var d = 0; d < 9; d++) {                           // flecks thrown clear
          var da = (v * 1.7 + d * 0.9), dr = 28 + ((d * 29 + v * 11) % 16);
          g.beginPath(); g.arc(Math.cos(da) * dr, Math.sin(da) * dr, 1.5 + (d % 3), 0, 6.2832); g.fill();
        }
        splatArt[pal[0]].push(c);
      }
    });
  }
  function bloodOf(e) { return (e && isZombie(e)) ? 'zomb' : 'red'; }
  function addSplat(x, y, r, pal, kind) {
    if (!SET.blood) return;
    if (splats.length >= SPLAT_MAX) splats.shift();
    splats.push({ x: x, y: y, r: r, ang: Math.random() * 6.2832, v: rnd(6), pal: pal, t: 0,
                  grow: kind === 'pool' ? 2.4 : 0.12, kind: kind || 'drop' });
  }
  // x, y: where; ang: the way the round was travelling; amount: how hard
  function bleed(x, y, ang, amount, big, pal) {
    if (netRole === 'host' && netHostLive()) netEv.push(['g', Math.round(x), Math.round(y), +(ang || 0).toFixed(2), Math.round(amount), big ? 1 : 0, pal || 'red']);
    if (!SET.blood) { spark(x, y, big ? 10 : 4, '170,150,150', 120); return; }
    pal = pal || 'red';
    if (ang === undefined || ang === null || isNaN(ang)) ang = Math.random() * 6.2832;
    var n = Math.min(26, 4 + Math.round(amount / 5) + (big ? 12 : 0));
    for (var i = 0; i < n; i++) {
      // most of it goes out the far side, a little back toward the shooter
      var back = Math.random() < 0.18;
      var a = ang + (back ? Math.PI : 0) + rr(-0.55, 0.55) * (big ? 1.8 : 1);
      var sp = rr(60, big ? 260 : 210) * (back ? 0.5 : 1);
      if (drops.length > 260) drops.shift();
      drops.push({ x: x, y: y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, z: rr(6, 14), vz: rr(20, 90),
                   sz: rr(1.3, big ? 3.6 : 2.8), pal: pal });
    }
    addSplat(x + Math.cos(ang) * 4, y + Math.sin(ang) * 4, big ? 9 : rr(5, 8), pal, 'drop');
    if (big) addSplat(x, y, 28 + rr(0, 8), pal, 'pool');
  }
  function goreTick(dt) {
    var i;
    for (i = drops.length - 1; i >= 0; i--) {
      var d = drops[i];
      d.vz -= 420 * dt; d.z += d.vz * dt;
      var nx = d.x + d.vx * dt, ny = d.y + d.vy * dt;
      if (wallAt(nx, ny)) { d.vx *= -0.2; d.vy *= -0.2; nx = d.x; ny = d.y; }   // spatters on the wall
      d.x = nx; d.y = ny;
      d.vx *= Math.pow(0.35, dt); d.vy *= Math.pow(0.35, dt);
      if (d.z <= 0) { addSplat(d.x, d.y, d.sz * rr(1.2, 2.2), d.pal, 'drop'); drops.splice(i, 1); }
    }
    for (i = 0; i < splats.length; i++) splats[i].t += dt;
    // the badly hurt leave a trail
    for (i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e.alive || e.air || e.hp >= 40 || !e.moving) continue;
      e.dripT = (e.dripT || 0) - dt;
      if (e.dripT <= 0) {
        e.dripT = rr(0.18, 0.4) * (0.5 + e.hp / 80);
        addSplat(e.x + rr(-4, 4), e.y + rr(-4, 4), rr(1.8, 3.4), bloodOf(e), 'drop');
      }
    }
    // the downed keep bleeding where they lie
    for (i = 0; i < ents.length; i++) {
      var dn = ents[i];
      if (!dn.alive || !dn.down) continue;
      dn.dripT = (dn.dripT || 0) - dt;
      if (dn.dripT <= 0) { dn.dripT = rr(0.6, 1.1); addSplat(dn.x + rr(-6, 6), dn.y + rr(-6, 6), rr(3, 6), bloodOf(dn), 'drop'); }
    }
  }
  function drawSplats() {
    if (!splats.length) return;
    if (!splatArt) bakeSplats();
    for (var i = 0; i < splats.length; i++) {
      var p = splats[i];
      // stains spread for a moment, then slowly dry and fade over a minute or two
      var grow = Math.min(1, p.t / p.grow);
      var r = p.r * (p.kind === 'pool' ? (0.25 + 0.75 * (1 - Math.pow(1 - grow, 2))) : (0.6 + 0.4 * grow));
      var a = p.t < 60 ? 0.92 : Math.max(0, 0.92 - (p.t - 60) / 90);
      if (a <= 0.02) continue;
      var art = splatArt[p.pal][p.v];
      ctx.save();
      ctx.globalAlpha = a;
      ctx.translate(p.x, p.y); ctx.rotate(p.ang);
      var sc = r / 26;
      ctx.drawImage(art, -48 * sc, -48 * sc, 96 * sc, 96 * sc);
      ctx.restore();
    }
  }
  function drawDrops() {
    for (var i = 0; i < drops.length; i++) {
      var d = drops[i], col = (d.pal === 'zomb' ? BLOOD_ZOMB : BLOOD_RED)[1];

      ctx.fillStyle = 'rgba(0,0,0,.25)';                        // its shadow on the ground
      ctx.beginPath(); ctx.arc(d.x + d.z * 0.3, d.y + d.z * 0.3, d.sz * 0.8, 0, 6.2832); ctx.fill();
      ctx.fillStyle = col;
      ctx.beginPath(); ctx.arc(d.x, d.y - d.z * 0.5, d.sz, 0, 6.2832); ctx.fill();
    }
  }

  function fire(e) {""")

# ---- hooks: hits, downs, deaths --------------------------------------------------
sub("""    spark(e.x, e.y, 5, '255,77,141', 140);
    if (FX.blood) {""", """    bleed(e.x, e.y, ang, amount, false, bloodOf(e));
    e.lastHitAng = ang;
    if (FX.blood) {""")
sub("""        spark(e.x, e.y, 10, '255,77,141', 150);
        emit(e.x, e.y, MOVE_SND.hit, e.id, 'hit');""", """        bleed(e.x, e.y, e.lastHitAng, 30, false, bloodOf(e));
        emit(e.x, e.y, MOVE_SND.hit, e.id, 'hit');""")
sub("""    corpses.push({ x: e.x, y: e.y });
    spark(e.x, e.y, 16, '255,77,141', 220);""", """    corpses.push({ x: e.x, y: e.y });
    bleed(e.x, e.y, e.lastHitAng, 60, true, bloodOf(e));""")
# the old sprite splat stays for big hits only - the new stains do the rest
sub("""    if (FX.blood) {
      if (decals.length > 90) decals.shift();""", """    if (FX.blood && SET.blood && amount >= 30) {
      if (decals.length > 90) decals.shift();""")
sub("""    if (FX.death) {
      if (deaths.length > 60) deaths.shift();""", """    if (FX.death && SET.blood) {
      if (deaths.length > 60) deaths.shift();""")

# ---- ticking: host and guest ---------------------------------------------------
sub("""    for (var p = parts.length - 1; p >= 0; p--) {
      var pt = parts[p];
      pt.life -= dt;
      if (pt.life <= 0) { parts.splice(p, 1); continue; }
      pt.x += pt.vx * dt; pt.y += pt.vy * dt;
      pt.vx *= 0.92; pt.vy *= 0.92;
    }""", """    for (var p = parts.length - 1; p >= 0; p--) {
      var pt = parts[p];
      pt.life -= dt;
      if (pt.life <= 0) { parts.splice(p, 1); continue; }
      pt.x += pt.vx * dt; pt.y += pt.vy * dt;
      pt.vx *= 0.92; pt.vy *= 0.92;
    }
    goreTick(dt);""")
sub("""    for (i = decals.length - 1; i >= 0; i--) decals[i].t += dt;""",
    """    for (i = decals.length - 1; i >= 0; i--) decals[i].t += dt;
    goreTick(dt);""")
sub("""      else if (q[0] === 'f') feed(q[1], q[2]);""", """      else if (q[0] === 'f') feed(q[1], q[2]);
      else if (q[0] === 'g') bleed(q[1], q[2], q[3], q[4], !!q[5], q[6]);""")
# a new match starts clean
sub("""    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = []; secTick = 0;""",
    """    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = []; secTick = 0;
    drops = []; splats = [];""")
sub("""    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = [];
    dmgMarks = []; shake = 0;""", """    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = [];
    drops = []; splats = [];
    dmgMarks = []; shake = 0;""")

# ---- drawing: stains on the ground, droplets in the air --------------------------
sub("""    if (FX.death) {
      var dSh = FX.death, dSplit = dSh.split || dSh.frames;""", """    drawSplats();
    if (FX.death) {
      var dSh = FX.death, dSplit = dSh.split || dSh.frames;""")
sub("""    for (i = 0; i < parts.length; i++) {
      var pp = parts[i];
      ctx.fillStyle = 'rgba(' + pp.color + ',' + (pp.life / pp.max).toFixed(3) + ')';
      ctx.fillRect(pp.x - pp.sz / 2, pp.y - pp.sz / 2, pp.sz, pp.sz);
    }""", """    for (i = 0; i < parts.length; i++) {
      var pp = parts[i];
      ctx.fillStyle = 'rgba(' + pp.color + ',' + (pp.life / pp.max).toFixed(3) + ')';
      ctx.fillRect(pp.x - pp.sz / 2, pp.y - pp.sz / 2, pp.sz, pp.sz);
    }
    drawDrops();""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

h = io.open(H, encoding='utf-8').read()
a = """<div class="setrow"><span>MINIMAP</span>"""
if a not in h:
    raise SystemExit('HTML PATTERN NOT FOUND')
h = h.replace(a, """<div class="setrow"><span>BLOOD</span><button class="tgl" id="setBlood" type="button">ON</button></div>
        """ + a, 1)
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p56 applied')
