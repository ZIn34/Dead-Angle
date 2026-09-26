# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ---------------------------------------------------------------- grenades --
sub("""  var DEATH_SND = { maxR: 620, speed: 820,""",
"""  var NADE_SND  = { maxR: 1900, speed: 1100, color: '255,150,60', w: 3.4,
                    aud: { rate: 0.40, cut: 1500, hp: 45, decay: 0.75, body: 52, vol: 1.0 } };
  var PIN_SND   = { maxR: 300,  speed: 760,  color: '200,200,180', w: 1.2,
                    aud: { rate: 2.3, cut: 5200, hp: 1100, decay: 0.05, body: 0, vol: 0.22 } };
  var DEATH_SND = { maxR: 620, speed: 820,""")

sub("""  var decals = [], impacts = [], deaths = [];""",
    """  var decals = [], impacts = [], deaths = [], nades = [];""")
sub("""    decals = []; impacts = []; deaths = [];""",
    """    decals = []; impacts = []; deaths = []; nades = [];""")

sub("""      slots: [null, null], slot: 0, reserve: START_RESERVE, meds: 0, level: 0,""",
    """      slots: [null, null], slot: 0, reserve: START_RESERVE, meds: 0, nades: 0, level: 0,""")

# loadouts carry a couple of grenades
sub("""      e.slot = 0; e.reserve = 140; e.meds = 1;""",
    """      e.slot = 0; e.reserve = 140; e.meds = 1; e.nades = 2;""")
sub("""      e.slot = 0; e.reserve = 120; e.meds = 1;""",
    """      e.slot = 0; e.reserve = 120; e.meds = 1; e.nades = 2;""")
sub("""      e.slots = [null, null]; e.slot = 0; e.reserve = START_RESERVE; e.meds = 0;""",
    """      e.slots = [null, null]; e.slot = 0; e.reserve = START_RESERVE; e.meds = 0; e.nades = 0;""")
sub("""      e.slot = 0; e.reserve = 9999; e.meds = 0;""",
    """      e.slot = 0; e.reserve = 9999; e.meds = 0; e.nades = 1;""")

# picked up like stims
sub("""      } else if (it.type === 'med') {
        if (e.meds < 3) { e.meds++; loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }""",
"""      } else if (it.type === 'med') {
        if (e.meds < 3) { e.meds++; loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }
      } else if (it.type === 'nade') {
        if (e.nades < 3) { e.nades++; loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }""")

sub("""    for (i = 0; i < counts.med; i++) { t2 = spot(); addLoot(t2.x, t2.y, 'med', null, 1); }""",
"""    for (i = 0; i < counts.med; i++) { t2 = spot(); addLoot(t2.x, t2.y, 'med', null, 1); }
    for (i = 0; i < Math.round(counts.med * 0.8); i++) { t2 = spot(); addLoot(t2.x, t2.y, 'nade', null, 1); }""")

# --- throwing and detonation ---
sub("""  function useMed(e) {""",
"""  function throwNade(e) {
    if (e.nades <= 0 || e.useT > 0 || !e.alive) return;
    e.nades--;
    nades.push({
      x: e.x + Math.cos(e.ang) * (e.r + 4), y: e.y + Math.sin(e.ang) * (e.r + 4),
      vx: Math.cos(e.ang) * 430, vy: Math.sin(e.ang) * 430,
      fuse: 1.35, spin: Math.random() * 6.2832, owner: e.id
    });
    emit(e.x, e.y, PIN_SND, e.id, 'pin');
  }

  function blast(g) {
    var R = 135;
    emit(g.x, g.y, NADE_SND, g.owner, 'shot');
    spark(g.x, g.y, 34, '255,186,90', 420);
    spark(g.x, g.y, 18, '150,150,150', 180);
    if (FX.impact_metal) {
      impacts.push({ x: g.x, y: g.y, ang: Math.random() * 6.2832, t: 0, scale: 2.6, fx: 'impact_metal' });
    }
    flashes.push({ x: g.x, y: g.y, ang: 0, t: 0.22, max: 0.22, tint: '#ffcf7a', scale: 3.2 });
    for (var i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e.alive) continue;
      var d = Math.sqrt((e.x - g.x) * (e.x - g.x) + (e.y - g.y) * (e.y - g.y));
      if (d > R || !lineClear(g.x, g.y, e.x, e.y)) continue;
      var dmg = 88 * (1 - d / R) + 14;
      damage(e, dmg, g.owner, Math.atan2(e.y - g.y, e.x - g.x));
    }
    if (dist({ x: g.x, y: g.y }, player) < R * 1.6) shake = Math.min(shake + 9, 14);
  }

  function updateNades(dt) {
    for (var i = nades.length - 1; i >= 0; i--) {
      var g = nades[i];
      g.fuse -= dt;
      g.spin += dt * 9;
      var nx = g.x + g.vx * dt, ny = g.y + g.vy * dt;
      if (wallAt(nx, g.y)) { g.vx = -g.vx * 0.42; nx = g.x; }
      if (wallAt(g.x, ny)) { g.vy = -g.vy * 0.42; ny = g.y; }
      g.x = nx; g.y = ny;
      var damp = Math.pow(0.12, dt);          // skids to a stop
      g.vx *= damp; g.vy *= damp;
      if (g.fuse <= 0) { blast(g); nades.splice(i, 1); }
    }
  }

  function useMed(e) {""")

sub("""    updateBullets(dt);
    updateSounds(dt);""",
"""    updateBullets(dt);
    updateNades(dt);
    updateSounds(dt);""")

# --- controls ---
sub("""      else if (k === 'f') useMed(player);""",
    """      else if (k === 'f') useMed(player);
      else if (k === 'g') throwNade(player);""")

# --- drawn on the ground, inside the lit region ---
sub("""    for (i = 0; i < corpses.length; i++) {
      ctx.fillStyle = 'rgba(255,77,141,.30)';""",
"""    for (i = 0; i < nades.length; i++) {
      var gn = nades[i];
      var ga2 = PACK_READY ? weaponArtIdx(1) : null;
      ctx.save();
      ctx.translate(gn.x, gn.y);
      ctx.rotate(gn.spin);
      if (ga2) {
        var gb2 = ga2.b, gw2 = gb2[2] - gb2[0], gh2 = gb2[3] - gb2[1];
        var dh2 = 13, dw2 = dh2 * (gw2 / gh2);
        ctx.drawImage(ga2.img, gb2[0], gb2[1], gw2, gh2, -dw2 / 2, -dh2 / 2, dw2, dh2);
      } else {
        ctx.fillStyle = '#5c6b32';
        ctx.beginPath(); ctx.arc(0, 0, 5, 0, 6.2832); ctx.fill();
      }
      ctx.restore();
      if (gn.fuse < 0.55 && Math.floor(gn.fuse * 12) % 2 === 0) {
        ctx.fillStyle = 'rgba(255,90,60,.9)';
        ctx.beginPath(); ctx.arc(gn.x, gn.y, 3, 0, 6.2832); ctx.fill();
      }
    }

    for (i = 0; i < corpses.length; i++) {
      ctx.fillStyle = 'rgba(255,77,141,.30)';""")

# a direct handle on a pack weapon slot, for the grenade art
sub("""  // Where a weapon's artwork lives: the pack sheet, or our own stand-in.""",
"""  function weaponArtIdx(i) {
    if (!PACK_IMG.weapons || !PACK.weapons || !PACK.weapons[i]) return null;
    return { img: PACK_IMG.weapons, b: PACK.weapons[i] };
  }

  // Where a weapon's artwork lives: the pack sheet, or our own stand-in.""")

# loot icon for a grenade
sub("""      var ico = PACK_IMG[it.type === 'ammo' ? 'icon_ammo' : 'icon_med'];""",
"""      if (it.type === 'nade') {
        var na = weaponArtIdx(1);
        if (na) {
          var nb = na.b, nw = nb[2] - nb[0], nh = nb[3] - nb[1];
          var nhh = 15, nww = nhh * (nw / nh);
          ctx.drawImage(na.img, nb[0], nb[1], nw, nh, it.x - nww / 2, it.y - nhh / 2, nww, nhh);
          ctx.globalAlpha = 1;
          return;
        }
      }
      var ico = PACK_IMG[it.type === 'ammo' ? 'icon_ammo' : 'icon_med'];""")

# --- HUD ---
sub("""    elMedsN.textContent = player.meds;
    elMedsBox.className = 'meds' + (player.meds ? '' : ' none');""",
"""    elMedsN.textContent = player.meds;
    elMedsBox.className = 'meds' + (player.meds ? '' : ' none');
    var nb2 = $('nadesN'), nbx = $('nadesBox');
    if (nb2) nb2.textContent = player.nades;
    if (nbx) nbx.className = 'meds' + (player.nades ? '' : ' none');""")

# the blast flash is bigger than a muzzle flash
sub("""        var fs = 0.5 * (fl.scale || 1);""",
    """        var fs = 0.5 * (fl.scale || 1);""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p17 applied')
