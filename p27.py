# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ==================================================== sector capture =========
sub("""    ctf:  { field: 14, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 3, teams: true, ctf: true }
  };""",
"""    ctf:  { field: 14, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 3, teams: true, ctf: true },
    sect: { field: 16, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 150, teams: true, sectors: 3 }
  };""")

sub("""    ctf: 'Two flags,""",
"""    sect: 'Three sectors, eight a side. Outnumber the other team inside one and it flips to you; every sector you hold pays a point a second, first to a hundred and fifty. Holding all three is loud, obvious work - they will hear exactly where you are.',
    ctf: 'Two flags,""")

sub("""    else if (mode === 'ctf') genRooms(126, 126, 7, 15, 74, 2, true);""",
    """    else if (mode === 'ctf') genRooms(126, 126, 7, 15, 74, 2, true);
    else if (mode === 'sect') genRooms(122, 122, 7, 15, 70, 2, true);""")

sub("""  var MODE_LABEL = { br: 'Battle royale', duel: '1v1', gun: 'Gun game', team: 'Teams 5v5', war: 'War 10v10', ctf: 'Capture the flag' };""",
    """  var MODE_LABEL = { br: 'Battle royale', duel: '1v1', gun: 'Gun game', team: 'Teams 5v5', war: 'War 10v10', ctf: 'Capture the flag', sect: 'Sector capture' };""")

sub("""      : (mode === 'duel' ? 'FIGHT' : (mode === 'team' || mode === 'war' || mode === 'ctf' ? 'DEPLOY' : 'START LADDER'));""",
    """      : (mode === 'duel' ? 'FIGHT' : (mode === 'gun' ? 'START LADDER' : 'DEPLOY'));""")

sub("""    } else if (mode === 'team' || mode === 'war' || mode === 'ctf') {
      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];""",
"""    } else if (MODE.teams) {
      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];""")

sub("""    $('squadPick').hidden = (mode === 'team' || mode === 'war' || mode === 'ctf');""",
    """    $('squadPick').hidden = !!MODES[mode].teams;""")

sub("""  var decals = [], impacts = [], deaths = [], nades = [], flags = [], smokes = [];""",
    """  var decals = [], impacts = [], deaths = [], nades = [], flags = [], smokes = [], sectors = [], secTick = 0;""")
sub("""    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = [];""",
    """    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = []; secTick = 0;""")

# three well-spaced holds
sub("""    spawnLoot(sp);
    elFeed.innerHTML = '';""",
"""    if (MODE.sectors) {
      var st = pickSpawns(MODE.sectors);
      sectors = st.map(function (t, i) {
        return {
          x: t.x * TILE + TILE / 2, y: t.y * TILE + TILE / 2, r: 108,
          name: 'ABC'.charAt(i), owner: -1, cap: -1, prog: 0
        };
      });
    }

    spawnLoot(sp);
    elFeed.innerHTML = '';""")

sub("""  function flagState(f) { return f.carrier ? 'TAKEN' : (f.home ? 'HOME' : 'DROPPED'); }""",
"""  function flagState(f) { return f.carrier ? 'TAKEN' : (f.home ? 'HOME' : 'DROPPED'); }

  function updateSectors(dt) {
    var i, j;
    for (i = 0; i < sectors.length; i++) {
      var sc = sectors[i];
      var head = [0, 0];
      for (j = 0; j < ents.length; j++) {
        var e = ents[j];
        if (!e.alive || e.down) continue;
        var dx = e.x - sc.x, dy = e.y - sc.y;
        if (dx * dx + dy * dy < sc.r * sc.r) head[e.team]++;
      }
      var lead = head[0] > head[1] ? 0 : (head[1] > head[0] ? 1 : -1);
      if (lead >= 0 && lead !== sc.owner) {
        if (sc.cap !== lead) { sc.cap = lead; sc.prog = 0; }
        sc.prog += dt * 0.16 * Math.min(3, Math.abs(head[0] - head[1]));
        if (sc.prog >= 1) {
          sc.owner = lead; sc.prog = 0; sc.cap = -1;
          var mine = lead === player.team;
          feed('sector <b>' + sc.name + '</b> ' + (mine ? 'taken' : 'lost'), mine);
        }
      } else {
        sc.prog = Math.max(0, sc.prog - dt * 0.22);
        if (sc.prog === 0) sc.cap = -1;
      }
    }

    secTick += dt;
    while (secTick >= 1) {
      secTick -= 1;
      for (i = 0; i < sectors.length; i++) {
        if (sectors[i].owner >= 0) score[sectors[i].owner]++;
      }
      for (var t = 0; t < 2; t++) {
        if (score[t] >= MODE.target) {
          var won = t === player.team;
          finish(won, won ? 'Held the ground long enough. That is the match.'
                          : 'They held more of it for longer.');
          return;
        }
      }
    }
  }""")

sub("""    if (MODE.ctf && state === 'play') updateFlags(dt);""",
"""    if (MODE.ctf && state === 'play') updateFlags(dt);
    if (MODE.sectors && state === 'play') updateSectors(dt);""")

# bots go where the ground is
sub("""          if (MODE.ctf && flags.length === 2) {""",
"""          if (MODE.sectors && sectors.length) {
            var pick = null, pickD = 1e9;
            for (var si = 0; si < sectors.length; si++) {
              var sq = sectors[si];
              var sd = dist(e, sq) * (sq.owner === e.team ? 2.2 : 1);   // prefer what is not yours
              if (sd < pickD) { pickD = sd; pick = sq; }
            }
            if (pick) { want = { x: pick.x, y: pick.y }; following = true; }
          }
          if (MODE.ctf && flags.length === 2) {""")

# --- drawn on the ground, always: these are landmarks ---------------------
sub("""    for (i = 0; i < flags.length; i++) {""",
"""    for (i = 0; i < sectors.length; i++) {
      var sc2 = sectors[i];
      var tint2 = sc2.owner < 0 ? '198,212,227' : TEAM_TINT[sc2.owner === player.team ? 0 : 1];
      ctx.fillStyle = 'rgba(' + tint2 + ',.055)';
      ctx.beginPath(); ctx.arc(sc2.x, sc2.y, sc2.r, 0, 6.2832); ctx.fill();
      ctx.strokeStyle = 'rgba(' + tint2 + ',.5)';
      ctx.lineWidth = 2.2 / zoom;
      ctx.beginPath(); ctx.arc(sc2.x, sc2.y, sc2.r, 0, 6.2832); ctx.stroke();
      if (sc2.prog > 0 && sc2.cap >= 0) {
        ctx.strokeStyle = 'rgba(' + TEAM_TINT[sc2.cap === player.team ? 0 : 1] + ',.95)';
        ctx.lineWidth = 4 / zoom;
        ctx.beginPath();
        ctx.arc(sc2.x, sc2.y, sc2.r, -Math.PI / 2, -Math.PI / 2 + 6.2832 * sc2.prog);
        ctx.stroke();
      }
      ctx.fillStyle = 'rgba(' + tint2 + ',.75)';
      ctx.font = 'bold ' + (34 / zoom).toFixed(1) + 'px "Chakra Petch", sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(sc2.name, sc2.x, sc2.y);
      ctx.textAlign = 'left';
    }

    for (i = 0; i < flags.length; i++) {""")

# --- minimap -------------------------------------------------------------
sub("""    for (var fi = 0; fi < flags.length; fi++) {""",
"""    for (var sq2 = 0; sq2 < sectors.length; sq2++) {
      var ms = sectors[sq2];
      var mst = ms.owner < 0 ? '198,212,227' : (ms.owner === player.team ? '124,231,216' : '255,122,77');
      ctx.strokeStyle = 'rgba(' + mst + ',.85)';
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(mx(ms.x), my(ms.y), 4.5, 0, 6.2832); ctx.stroke();
    }
    for (var fi = 0; fi < flags.length; fi++) {""")

# --- HUD -----------------------------------------------------------------
sub("""    } else if (mode === 'ctf') {""",
"""    } else if (mode === 'sect') {
      elAlive.textContent = score[player.team] + ' \\u2013 ' + score[1 - player.team];
      elZone.className = 'zone-line';
      var bits = [];
      for (var sh = 0; sh < sectors.length; sh++) {
        var so = sectors[sh].owner;
        bits.push(sectors[sh].name + ' ' + (so < 0 ? '\\u2013' : (so === player.team ? 'YOU' : 'THEM')));
      }
      elZone.textContent = bits.join(' \\u00b7 ') + ' \\u00b7 TO ' + MODE.target;
    } else if (mode === 'ctf') {""")

sub("""    else if (mode === 'team' || mode === 'war' || mode === 'ctf') {
      big = won ? 'WIN' : 'LOSS';""",
"""    else if (MODE.teams) {
      big = won ? 'WIN' : 'LOSS';""")

sub("""    if (mode === 'ctf') {
      e.respawnT = 2.4;
      return;
    }""",
"""    if (mode === 'ctf' || mode === 'sect') {
      e.respawnT = 2.4;
      return;
    }""")

# ---- everyone drops what they were carrying, in every mode ---------------
sub("""    var killer = ents[fromId];
    var kn = killer ? killer.name : 'THE ZONE';""",
"""    dropKit(e);
    var killer = ents[fromId];
    var kn = killer ? killer.name : 'THE ZONE';""")

sub("""  function dist(a, b) { var dx = a.x - b.x, dy = a.y - b.y; return Math.sqrt(dx * dx + dy * dy); }""",
"""  // Whatever they were carrying hits the floor, whatever the mode.
  function dropKit(e) {
    function put(type, key, ammo, n) {
      loot.push({
        x: e.x + rr(-16, 16), y: e.y + rr(-16, 16), type: type, key: key || null,
        spin: rr(0, 6.2832), ammo: ammo || 0, n: n || 0, seen: false
      });
    }
    for (var sx2 = 0; sx2 < 2; sx2++) {
      if (e.slots[sx2]) put('gun', e.slots[sx2].key, e.slots[sx2].ammo, 0);
    }
    if (e.reserve > 10 && e.reserve < 9000) put('ammo', null, 0, Math.min(60, e.reserve));
    while (e.meds > 0) { put('med', null, 0, 1); e.meds--; }
    while (e.nades > 0) { put('nade', null, 0, 1); e.nades--; }
    while (e.smokes > 0) { put('smoke', null, 0, 1); e.smokes--; }
    if (loot.length > 900) loot.splice(0, loot.length - 900);
  }

  function dist(a, b) { var dx = a.x - b.x, dy = a.y - b.y; return Math.sqrt(dx * dx + dy * dy); }""")

# the old battle-royale-only drop is now redundant
sub("""    alive--;
    for (var s = 0; s < 2; s++) {
      if (e.slots[s]) loot.push({ x: e.x + rr(-12, 12), y: e.y + rr(-12, 12), type: 'gun', key: e.slots[s].key, ammo: e.slots[s].ammo, n: 0, seen: false });
    }
    if (e.reserve > 10 && e.reserve < 9000) loot.push({ x: e.x + rr(-12, 12), y: e.y + rr(-12, 12), type: 'ammo', key: null, ammo: 0, n: Math.min(60, e.reserve), seen: false });
""",
"""    alive--;
""")

# and picking things up has to work everywhere now, not just in looting modes
sub("""    if (MODE.loot) autoPickup(e);

    promptItem = null;
    if (MODE.loot) {""",
"""    autoPickup(e);

    promptItem = null;
    if (true) {""")

sub("""    if (MODE.loot) autoPickup(e);
    var w = curW(e), slot = curSlot(e);""",
"""    autoPickup(e);
    var w = curW(e), slot = curSlot(e);""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p27 applied')
