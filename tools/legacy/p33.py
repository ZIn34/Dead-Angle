# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# A single carrier on a map this size meant you never met one. Start with a
# handful and keep feeding them in, faster as the clock runs down.
sub("""    if (MODE.zombies) {
      ents.forEach(function (e, idx) { e.team = 0; e.skin = idx % 16; });
      var patient = 1 + rnd(Math.max(1, fieldN - 1));     // never the player
      ents[patient].team = 1;
      ents[patient].skin = ZOMBIE_SKIN;
      zombClock = MODE.clock;
    } else if (MODE.teams) {""",
"""    if (MODE.zombies) {
      ents.forEach(function (e, idx) { e.team = 0; e.skin = idx % 16; });
      var seeds = Math.max(3, Math.round(fieldN * 0.22));
      for (var zs = 0; zs < seeds; zs++) {
        var patient = 1 + rnd(Math.max(1, fieldN - 1));   // never the player
        ents[patient].team = 1;
        ents[patient].skin = ZOMBIE_SKIN;
      }
      zombClock = MODE.clock;
      zombSpawnT = 4;
    } else if (MODE.teams) {""")

sub("""  var zombClock = 0;""",
"""  var zombClock = 0, zombSpawnT = 0;
  var ZOMB_CAP = 22;

  // Feed another one in, somewhere well away from the living.
  function spawnZombie() {
    var live = 0;
    for (var i = 0; i < ents.length; i++) if (ents[i].alive && ents[i].team === 1) live++;
    if (live >= ZOMB_CAP || ents.length > 70) return;
    var t = pickRespawnTile(player);
    var z = makeEnt(t, false, 'WALKER ' + (ents.length + 1));
    z.team = 1;
    ents.push(z);
    placeEnt(z, t);            // loadout reads the team, so it comes up empty-handed
    z.skin = ZOMBIE_SKIN;
    return z;
  }""")

sub("""    if (MODE.zombies && state === 'play') {
      zombClock -= dt;
      var living = 0;""",
"""    if (MODE.zombies && state === 'play') {
      zombClock -= dt;
      zombSpawnT -= dt;
      if (zombSpawnT <= 0) {
        var gone = 1 - clamp(zombClock / MODE.clock, 0, 1);   // 0 at the start, 1 at the end
        zombSpawnT = 5.2 - 3.9 * gone;
        spawnZombie();
        if (gone > 0.45) spawnZombie();                        // in pairs later on
        if (gone > 0.8) spawnZombie();
      }
      var living = 0;""")

# count what is actually on its feet rather than how many have turned
sub("""      elZone.textContent = (player.team === 1 ? 'INFECTED \\u00b7 ' : 'SURVIVE \\u00b7 ')
        + fmtTime(zombClock) + ' \\u00b7 ' + alive1 + ' TURNED';""",
"""      elZone.textContent = (player.team === 1 ? 'INFECTED \\u00b7 ' : 'SURVIVE \\u00b7 ')
        + fmtTime(zombClock) + ' \\u00b7 ' + alive1 + ' ON THEIR FEET';""")

sub("""    zomb: 'One of them turns at the start.""",
    """    zomb: 'A few turn at the start and more keep coming, faster as the clock runs down.""")

# ==================================================== objective markers ======
sub("""  // ---- minimap: only ground you have actually seen ------------------------""",
"""  // Objectives are map knowledge, so they are marked wherever they are -
  // pinned to the screen edge with a bearing and range when they are off it.
  function marker(wx, wy, label, tint, hollow) {
    var sx = (wx - cam.x) * zoom + cw / 2;
    var sy = (wy - cam.y) * zoom + ch / 2;
    var pad = 30;
    var off = sx < pad || sx > cw - pad || sy < pad || sy > ch - pad;
    sx = clamp(sx, pad, cw - pad);
    sy = clamp(sy, pad, ch - pad);
    ctx.save();
    ctx.globalAlpha = off ? 0.92 : 0.6;
    ctx.strokeStyle = 'rgba(' + tint + ',.9)';
    ctx.fillStyle = 'rgba(' + tint + ',' + (hollow ? '.18' : '.75') + ')';
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(sx, sy - 9); ctx.lineTo(sx + 9, sy); ctx.lineTo(sx, sy + 9); ctx.lineTo(sx - 9, sy);
    ctx.closePath();
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = hollow ? 'rgba(' + tint + ',.95)' : '#04060a';
    ctx.font = '700 9px "Chakra Petch", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, sx, sy + 1);
    if (off) {
      ctx.fillStyle = 'rgba(' + tint + ',.8)';
      ctx.font = '600 8.5px "IBM Plex Mono", monospace';
      var d = Math.round(Math.sqrt((wx - player.x) * (wx - player.x) + (wy - player.y) * (wy - player.y)));
      ctx.fillText(d + 'u', sx, sy + 19);
    }
    ctx.textAlign = 'left';
    ctx.globalAlpha = 1;
    ctx.restore();
  }

  function renderObjectives() {
    if (!player.alive) return;
    var i;
    for (i = 0; i < sectors.length; i++) {
      var sc = sectors[i];
      var tint = sc.owner < 0 ? '198,212,227' : TEAM_TINT[sc.owner === player.team ? 0 : 1];
      marker(sc.x, sc.y, sc.name, tint, sc.owner < 0);
    }
    for (i = 0; i < flags.length; i++) {
      var f = flags[i];
      var ft = TEAM_TINT[f.team === player.team ? 0 : 1];
      marker(f.hx, f.hy, 'H', ft, true);                       // the stand
      var known = f.home || (f.carrier && f.carrier.team === player.team) || visibleToPlayer(f.x, f.y);
      if (known && !f.home) marker(f.x, f.y, 'F', ft, false);  // and the flag itself
    }
  }

  // ---- minimap: only ground you have actually seen ------------------------""")

sub("""    renderAllies();
    if (SET.minimap) drawMinimap();""",
"""    renderAllies();
    renderObjectives();
    if (SET.minimap) drawMinimap();""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p33 applied')
