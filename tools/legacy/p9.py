# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ---------------------------------------------------------------- mode ------
sub("""    gun:  { field: 6,  zone: false, loot: false, respawn: true,  label: 'LEVEL' }
  };""",
"""    gun:  { field: 6,  zone: false, loot: false, respawn: true,  label: 'LEVEL' },
    team: { field: 10, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 30, teams: true }
  };

  // Cool skins for your side, warm for theirs, so a glimpse is enough.
  var TEAM_SKINS = [[1, 4, 15, 13, 9], [2, 0, 11, 10, 7]];
  var TEAM_TINT = ['124,231,216', '255,122,77'];""")

sub("""    gun: 'Every elimination hands you the next weapon up the ladder: pistol, SMG, shotgun, sniper, rifle. Get a kill with the rifle to win. Everyone respawns.'""",
"""    gun: 'Every elimination hands you the next weapon up the ladder: pistol, SMG, shotgun, sniper, rifle. Get a kill with the rifle to win. Everyone respawns.',
    team: 'Five against five, everyone respawns, first side to thirty eliminations. Your squad wears cool colours and theirs wears warm - but in the dark you will hear them long before you can tell.'""")

# ---------------------------------------------------------------- entity ----
sub("""      _spd: 0, kills: 0, skin: 0""",
    """      _spd: 0, kills: 0, skin: 0, team: 0""")

sub("""  function curSlot(e) { return e.slots[e.slot]; }""",
"""  function curSlot(e) { return e.slots[e.slot]; }
  function foes(a, b) { return MODE.teams ? a.team !== b.team : true; }""")

# ---------------------------------------------------------------- loadout ---
sub("""    } else if (mode === 'duel') {""",
"""    } else if (mode === 'team') {
      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];
      e.slots = [{ key: prim, ammo: WEAPONS[prim].mag }, { key: 'pistol', ammo: WEAPONS.pistol.mag }];
      e.slot = 0; e.reserve = 140; e.meds = 1;
    } else if (mode === 'duel') {""")

# ---------------------------------------------------------------- spawning --
sub("""  function pickRespawnTile(e) {
    var best = null, bestScore = -1;
    for (var i = 0; i < 48; i++) {
      var t = floorTiles[rnd(floorTiles.length)];
      var wx = t.x * TILE, wy = t.y * TILE, minD = 1e9;
      for (var j = 0; j < ents.length; j++) {
        var o = ents[j];
        if (o === e || !o.alive) continue;
        var dx = o.x - wx, dy = o.y - wy;
        minD = Math.min(minD, Math.sqrt(dx * dx + dy * dy));
      }
      if (minD > bestScore) { bestScore = minD; best = t; }
    }
    return best || floorTiles[0];
  }""",
"""  function pickRespawnTile(e) {
    var best = null, bestScore = -1e9;
    for (var i = 0; i < 48; i++) {
      var t = floorTiles[rnd(floorTiles.length)];
      var wx = t.x * TILE, wy = t.y * TILE, minD = 1e9, friend = 1e9;
      for (var j = 0; j < ents.length; j++) {
        var o = ents[j];
        if (o === e || !o.alive) continue;
        var dx = o.x - wx, dy = o.y - wy;
        var d = Math.sqrt(dx * dx + dy * dy);
        if (foes(e, o)) minD = Math.min(minD, d);
        else friend = Math.min(friend, d);
      }
      // far from the other side, but not stranded from your own
      var sc = minD - (MODE.teams && friend < 1e8 ? friend * 0.25 : 0);
      if (sc > bestScore) { bestScore = sc; best = t; }
    }
    return best || floorTiles[0];
  }

  // Two anchors as far apart as the map allows, one per side.
  function teamSpawns(n) {
    var a = floorTiles[rnd(floorTiles.length)], b = a, far = -1, i, t, d;
    for (i = 0; i < floorTiles.length; i += 3) {
      t = floorTiles[i];
      d = (t.x - a.x) * (t.x - a.x) + (t.y - a.y) * (t.y - a.y);
      if (d > far) { far = d; b = t; }
    }
    far = -1;
    for (i = 0; i < floorTiles.length; i += 3) {
      t = floorTiles[i];
      d = (t.x - b.x) * (t.x - b.x) + (t.y - b.y) * (t.y - b.y);
      if (d > far) { far = d; a = t; }
    }
    function near(anchor, count) {
      var pool = floorTiles.slice().sort(function (p, q) {
        return ((p.x - anchor.x) * (p.x - anchor.x) + (p.y - anchor.y) * (p.y - anchor.y)) -
               ((q.x - anchor.x) * (q.x - anchor.x) + (q.y - anchor.y) * (q.y - anchor.y));
      });
      var out = [];
      for (var k = 0; k < pool.length && out.length < count; k++) {
        var ok = true;
        for (var m = 0; m < out.length; m++) {
          var ddx = out[m].x - pool[k].x, ddy = out[m].y - pool[k].y;
          if (ddx * ddx + ddy * ddy < 16) { ok = false; break; }
        }
        if (ok) out.push(pool[k]);
      }
      return out;
    }
    var half = n >> 1;
    return near(a, half).concat(near(b, n - half));
  }""")

sub("""    var sp = pickSpawns(MODE.field);
    player = makeEnt(sp[0], true, 'YOU');""",
"""    var sp = MODE.teams ? teamSpawns(MODE.field) : pickSpawns(MODE.field);
    player = makeEnt(sp[0], true, 'YOU');""")

sub("""    // a different skin each, so people are told apart by more than a colour
    var pool = [];
    for (var k = 0; k < 16; k++) pool.push(k);
    shuffle(pool);
    ents.forEach(function (e, idx) { e.skin = pool[idx % pool.length]; });
    charCache = {};""",
"""    if (MODE.teams) {
      var half = MODE.field >> 1;
      ents.forEach(function (e, idx) {
        e.team = idx < half ? 0 : 1;
        var set = TEAM_SKINS[e.team];
        e.skin = set[(idx % half) % set.length];
      });
    } else {
      // a different skin each, so people are told apart by more than a colour
      var pool = [];
      for (var k = 0; k < 16; k++) pool.push(k);
      shuffle(pool);
      ents.forEach(function (e, idx) { e.skin = pool[idx % pool.length]; });
    }
    charCache = {};""")

# ---------------------------------------------------------------- combat ----
sub("""          if (!e.alive || e.id === b.owner) continue;""",
    """          if (!e.alive || e.id === b.owner) continue;
          if (MODE.teams && ents[b.owner] && e.team === ents[b.owner].team) continue;""")

sub("""        if (o === e || !o.alive) continue;
        var d = dist(e, o);
        if (d >= sightR || !lineClear(e.x, e.y, o.x, o.y)) continue;""",
"""        if (o === e || !o.alive || !foes(e, o)) continue;
        var d = dist(e, o);
        if (d >= sightR || !lineClear(e.x, e.y, o.x, o.y)) continue;""")

sub("""        if (!e.bot || !e.alive || e.id === s.owner || s.heard[e.id]) continue;""",
"""        if (!e.bot || !e.alive || e.id === s.owner || s.heard[e.id]) continue;
        if (MODE.teams && ents[s.owner] && ents[s.owner].team === e.team) { s.heard[e.id] = 1; continue; }""")

# ---------------------------------------------------------------- scoring ---
sub("""    if (mode === 'duel') {""",
"""    if (mode === 'team') {
      if (killer && killer !== e && foes(killer, e)) {
        score[killer.team]++;
        if (score[killer.team] >= MODE.target) {
          var won = killer.team === player.team;
          finish(won, won ? 'Your side took it ' + score[player.team] + '-' + score[1 - player.team] + '.'
                          : 'They closed it out ' + score[1 - player.team] + '-' + score[player.team] + '.');
          return;
        }
      }
      e.respawnT = 2.2;
      return;
    }
    if (mode === 'duel') {""")

sub("""    else if (mode === 'duel') { big = won ? 'WIN' : 'LOSS'; small = score[0] + ' \\u2014 ' + score[1]; }""",
"""    else if (mode === 'duel') { big = won ? 'WIN' : 'LOSS'; small = score[0] + ' \\u2014 ' + score[1]; }
    else if (mode === 'team') {
      big = won ? 'WIN' : 'LOSS';
      small = score[player.team] + ' \\u2014 ' + score[1 - player.team];
    }""")

sub("""    } else if (mode === 'duel') {
      elAlive.textContent = score[0] + ' \\u2013 ' + score[1];""",
"""    } else if (mode === 'team') {
      elAlive.textContent = score[player.team] + ' \\u2013 ' + score[1 - player.team];
      elZone.className = 'zone-line';
      var mates = 0, opp = 0;
      for (var q = 0; q < ents.length; q++) {
        if (!ents[q].alive) continue;
        if (ents[q].team === player.team) mates++; else opp++;
      }
      elZone.textContent = player.alive
        ? 'FIRST TO ' + MODE.target + ' \\u00b7 ' + mates + ' v ' + opp + ' UP'
        : 'RESPAWNING \\u00b7 ' + Math.ceil(player.respawnT);
    } else if (mode === 'duel') {
      elAlive.textContent = score[0] + ' \\u2013 ' + score[1];""")

# ---------------------------------------------------------------- colours ---
sub("""    if (PACK_READY) {
      ctx.fillStyle = e === player ? 'rgba(124,231,216,.34)' : 'rgba(255,122,77,.36)';""",
"""    if (PACK_READY) {
      var tint = MODE.teams
        ? TEAM_TINT[e.team === player.team ? 0 : 1]
        : (e === player ? '124,231,216' : '255,122,77');
      ctx.fillStyle = 'rgba(' + tint + ',' + (e === player ? '.40' : '.36') + ')';""")

sub("""      if (e !== player) {
        var hw = 22, hp0 = clamp(e.hp / 100, 0, 1);
        ctx.fillStyle = 'rgba(10,15,22,.8)';
        ctx.fillRect(e.x - hw / 2, e.y - e.r - 13, hw, 2.6);
        ctx.fillStyle = 'rgba(255,122,77,.9)';
        ctx.fillRect(e.x - hw / 2, e.y - e.r - 13, hw * hp0, 2.6);
      }""",
"""      if (e !== player) {
        var hw = 22, hp0 = clamp(e.hp / 100, 0, 1);
        ctx.fillStyle = 'rgba(10,15,22,.8)';
        ctx.fillRect(e.x - hw / 2, e.y - e.r - 13, hw, 2.6);
        ctx.fillStyle = 'rgba(' + tint + ',.9)';
        ctx.fillRect(e.x - hw / 2, e.y - e.r - 13, hw * hp0, 2.6);
      }""")

sub("""    for (i = 0; i < ents.length; i++) {
      var en = ents[i];
      if (!en.alive || en === player) continue;
      if (!visibleToPlayer(en.x, en.y)) continue;
      drawUnit(en, '#ff7a4d');
    }""",
"""    for (i = 0; i < ents.length; i++) {
      var en = ents[i];
      if (!en.alive || en === player) continue;
      if (!visibleToPlayer(en.x, en.y)) continue;
      drawUnit(en, (MODE.teams && en.team === player.team) ? '#8ff0e4' : '#ff7a4d');
    }""")

# kill feed shows which side took the hit
sub("""    else feed('<b>' + kn + '</b> &rsaquo; ' + e.name, false);""",
"""    else feed('<b>' + kn + '</b> &rsaquo; ' + e.name, MODE.teams && killer && killer.team === player.team);""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p9 applied')
