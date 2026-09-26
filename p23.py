# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ==================================================== smoke ==================
sub("""  var PIN_SND   = { maxR: 300,  speed: 760,  color: '200,200,180', w: 1.2,""",
"""  var SMOKE_SND = { maxR: 700,  speed: 900,  color: '200,206,214', w: 2.0,
                    sample: 'smoke', sampleGain: 1.0,
                    aud: { rate: 0.75, cut: 2600, hp: 160, decay: 0.55, body: 0, vol: 0.55 } };
  var PIN_SND   = { maxR: 300,  speed: 760,  color: '200,200,180', w: 1.2,""")

sub("""  var decals = [], impacts = [], deaths = [], nades = [], flags = [];""",
    """  var decals = [], impacts = [], deaths = [], nades = [], flags = [], smokes = [];""")
sub("""    decals = []; impacts = []; deaths = []; nades = []; flags = [];""",
    """    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = [];""")

sub("""      slots: [null, null], slot: 0, reserve: START_RESERVE, meds: 0, nades: 0, level: 0,""",
    """      slots: [null, null], slot: 0, reserve: START_RESERVE, meds: 0, nades: 0, smokes: 0, level: 0,""")

sub("""      e.slot = 0; e.reserve = 140; e.meds = 1; e.nades = 2;""",
    """      e.slot = 0; e.reserve = 140; e.meds = 1; e.nades = 2; e.smokes = 1;""")
sub("""      e.slot = 0; e.reserve = 120; e.meds = 1; e.nades = 2;""",
    """      e.slot = 0; e.reserve = 120; e.meds = 1; e.nades = 2; e.smokes = 1;""")
sub("""      e.slots = [null, null]; e.slot = 0; e.reserve = START_RESERVE; e.meds = 0; e.nades = 0;""",
    """      e.slots = [null, null]; e.slot = 0; e.reserve = START_RESERVE; e.meds = 0; e.nades = 0; e.smokes = 0;""")
sub("""      e.slot = 0; e.reserve = 9999; e.meds = 0; e.nades = 1;""",
    """      e.slot = 0; e.reserve = 9999; e.meds = 0; e.nades = 1; e.smokes = 0;""")

sub("""      } else if (it.type === 'nade') {
        if (e.nades < 3) { e.nades++; loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }""",
"""      } else if (it.type === 'nade') {
        if (e.nades < 3) { e.nades++; loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }
      } else if (it.type === 'smoke') {
        if (e.smokes < 3) { e.smokes++; loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }""")

sub("""    for (i = 0; i < Math.round(counts.med * 0.8); i++) { t2 = spot(); addLoot(t2.x, t2.y, 'nade', null, 1); }""",
"""    for (i = 0; i < Math.round(counts.med * 0.8); i++) { t2 = spot(); addLoot(t2.x, t2.y, 'nade', null, 1); }
    for (i = 0; i < Math.round(counts.med * 0.7); i++) { t2 = spot(); addLoot(t2.x, t2.y, 'smoke', null, 1); }""")

# --- sight blocking -------------------------------------------------------
sub("""  function visibleToPlayer(x, y) {""",
"""  // How much of a line runs through smoke. Enough of it and you see nothing -
  // a glance into the edge of a cloud still works, straight through does not.
  function smokeBlocks(ax, ay, bx, by) {
    if (!smokes.length) return false;
    var dx = bx - ax, dy = by - ay;
    var len2 = dx * dx + dy * dy;
    if (len2 < 1) return false;
    var len = Math.sqrt(len2), total = 0;
    for (var i = 0; i < smokes.length; i++) {
      var sm = smokes[i];
      if (sm.r < 8 || sm.alpha < 0.3) continue;
      var fx = ax - sm.x, fy = ay - sm.y;
      var b2 = 2 * (fx * dx + fy * dy);
      var c2 = fx * fx + fy * fy - sm.r * sm.r;
      var disc = b2 * b2 - 4 * len2 * c2;
      if (disc <= 0) continue;
      disc = Math.sqrt(disc);
      var t1 = clamp((-b2 - disc) / (2 * len2), 0, 1);
      var t2 = clamp((-b2 + disc) / (2 * len2), 0, 1);
      total += (t2 - t1) * len;
      if (total > 52) return true;
    }
    return false;
  }
  // Walls stop movement and bullets; smoke only stops eyes.
  function sightClear(ax, ay, bx, by) {
    return lineClear(ax, ay, bx, by) && !smokeBlocks(ax, ay, bx, by);
  }

  function visibleToPlayer(x, y) {""")

sub("""    return dx * dx + dy * dy < VIEW_R * VIEW_R && lineClear(player.x, player.y, x, y);
  }
  function litVisible(x, y, reach) {
    var dx = x - player.x, dy = y - player.y;
    return dx * dx + dy * dy < reach * reach && lineClear(player.x, player.y, x, y);
  }""",
"""    return dx * dx + dy * dy < VIEW_R * VIEW_R && sightClear(player.x, player.y, x, y);
  }
  function litVisible(x, y, reach) {
    var dx = x - player.x, dy = y - player.y;
    return dx * dx + dy * dy < reach * reach && sightClear(player.x, player.y, x, y);
  }""")

# bots are blinded by it too
sub("""        if (d >= sightR || !lineClear(e.x, e.y, o.x, o.y)) continue;""",
    """        if (d >= sightR || !sightClear(e.x, e.y, o.x, o.y)) continue;""")
sub("""      if (dd < maxRange && Math.abs(diff) < tol && lineClear(e.x, e.y, tt.x, tt.y)) {""",
    """      if (dd < maxRange && Math.abs(diff) < tol && sightClear(e.x, e.y, tt.x, tt.y)) {""")

# --- throwing -------------------------------------------------------------
sub("""  function throwNade(e) {
    if (e.nades <= 0 || e.useT > 0 || !e.alive) return;
    e.nades--;
    nades.push({
      x: e.x + Math.cos(e.ang) * (e.r + 4), y: e.y + Math.sin(e.ang) * (e.r + 4),
      vx: Math.cos(e.ang) * 430, vy: Math.sin(e.ang) * 430,
      fuse: 1.35, spin: Math.random() * 6.2832, owner: e.id
    });
    emit(e.x, e.y, PIN_SND, e.id, 'pin');
  }""",
"""  function throwNade(e, kind) {
    var have = kind === 'smoke' ? e.smokes : e.nades;
    if (have <= 0 || e.useT > 0 || !e.alive || e.down) return;
    if (kind === 'smoke') e.smokes--; else e.nades--;
    nades.push({
      x: e.x + Math.cos(e.ang) * (e.r + 4), y: e.y + Math.sin(e.ang) * (e.r + 4),
      vx: Math.cos(e.ang) * 430, vy: Math.sin(e.ang) * 430,
      fuse: kind === 'smoke' ? 1.05 : 1.35, spin: Math.random() * 6.2832,
      owner: e.id, kind: kind || 'frag'
    });
    emit(e.x, e.y, PIN_SND, e.id, 'pin');
  }

  function popSmoke(g) {
    emit(g.x, g.y, SMOKE_SND, g.owner, 'smoke');
    spark(g.x, g.y, 14, '198,204,212', 150);
    smokes.push({ x: g.x, y: g.y, t: 0, r: 0, maxR: 148, alpha: 0, life: 17 });
  }

  function updateSmoke(dt) {
    for (var i = smokes.length - 1; i >= 0; i--) {
      var sm = smokes[i];
      sm.t += dt;
      sm.r = sm.maxR * Math.min(1, sm.t / 1.3);
      if (sm.t < 1.3) sm.alpha = sm.t / 1.3;
      else if (sm.t > sm.life - 3.5) sm.alpha = Math.max(0, (sm.life - sm.t) / 3.5);
      else sm.alpha = 1;
      if (sm.t >= sm.life) smokes.splice(i, 1);
    }
  }""")

sub("""      if (g.fuse <= 0) { blast(g); nades.splice(i, 1); }""",
    """      if (g.fuse <= 0) { if (g.kind === 'smoke') popSmoke(g); else blast(g); nades.splice(i, 1); }""")

sub("""    updateNades(dt);
    if (MODE.ctf && state === 'play') updateFlags(dt);""",
"""    updateNades(dt);
    updateSmoke(dt);
    if (MODE.ctf && state === 'play') updateFlags(dt);""")

sub("""      else if (k === 'g') throwNade(player);""",
    """      else if (k === 'g') throwNade(player, 'frag');
      else if (k === 'h') throwNade(player, 'smoke');""")

# --- drawing --------------------------------------------------------------
sub("""      var ga2 = PACK_READY ? weaponArtIdx(1) : null;""",
    """      var ga2 = PACK_READY ? weaponArtIdx(gn.kind === 'smoke' ? 0 : 1) : null;""")

sub("""      if (it.type === 'nade') {
        var na = weaponArtIdx(1);""",
"""      if (it.type === 'nade' || it.type === 'smoke') {
        var na = weaponArtIdx(it.type === 'smoke' ? 0 : 1);""")

# the cloud itself, over everything you can see
sub("""    if (zone) {
      ctx.save();
      ctx.beginPath();
      ctx.rect(vx0 - 200, vy0 - 200, (vx1 - vx0) + 400, (vy1 - vy0) + 400);""",
"""    if (smokes.length) {
      ctx.save();
      ctx.clip(poly);
      for (i = 0; i < smokes.length; i++) {
        var sm2 = smokes[i];
        if (sm2.alpha <= 0.01) continue;
        var sg = ctx.createRadialGradient(sm2.x, sm2.y, sm2.r * 0.25, sm2.x, sm2.y, sm2.r);
        sg.addColorStop(0, 'rgba(176,182,190,' + (0.97 * sm2.alpha).toFixed(3) + ')');
        sg.addColorStop(0.72, 'rgba(150,157,166,' + (0.92 * sm2.alpha).toFixed(3) + ')');
        sg.addColorStop(1, 'rgba(126,133,142,0)');
        ctx.fillStyle = sg;
        ctx.beginPath(); ctx.arc(sm2.x, sm2.y, sm2.r, 0, 6.2832); ctx.fill();
      }
      ctx.restore();
    }

    if (zone) {
      ctx.save();
      ctx.beginPath();
      ctx.rect(vx0 - 200, vy0 - 200, (vx1 - vx0) + 400, (vy1 - vy0) + 400);""")

# --- HUD ------------------------------------------------------------------
sub("""    var nb2 = $('nadesN'), nbx = $('nadesBox');
    if (nb2) nb2.textContent = player.nades;
    if (nbx) nbx.className = 'meds' + (player.nades ? '' : ' none');""",
"""    var nb2 = $('nadesN'), nbx = $('nadesBox');
    if (nb2) nb2.textContent = player.nades;
    if (nbx) nbx.className = 'meds' + (player.nades ? '' : ' none');
    var sb2 = $('smokesN'), sbx = $('smokesBox');
    if (sb2) sb2.textContent = player.smokes;
    if (sbx) sbx.className = 'meds' + (player.smokes ? '' : ' none');""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p23 applied')
