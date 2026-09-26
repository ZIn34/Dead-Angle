# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ==================================================== capture the flag =======
sub("""    war:  { field: 20, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 75, teams: true }
  };""",
"""    war:  { field: 20, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 75, teams: true },
    ctf:  { field: 10, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 3, teams: true, ctf: true }
  };

  // A carried flag announces itself - the only way anyone finds the runner.
  var FLAG_SND = { maxR: 760, speed: 700, color: '242,189,29', w: 2.2,
                   aud: { rate: 0.9, cut: 2400, hp: 300, decay: 0.16, body: 120, vol: 0.30 } };""")

sub("""    war: 'Twenty fighters,""",
"""    ctf: 'Two flags, five a side, first to three captures. Your own flag has to be home for a capture to count. Carrying the enemy flag makes you ring out across the map every second - taking it is the easy part.',
    war: 'Twenty fighters,""")

sub("""    else if (mode === 'war') genRooms(86, 86, 8, 16, 34, 2, true);""",
    """    else if (mode === 'war') genRooms(86, 86, 8, 16, 34, 2, true);
    else if (mode === 'ctf') genRooms(76, 76, 7, 14, 30, 2, true);""")

sub("""  var MODE_LABEL = { br: 'Battle royale', duel: '1v1', gun: 'Gun game', team: 'Teams 5v5', war: 'War 10v10' };""",
    """  var MODE_LABEL = { br: 'Battle royale', duel: '1v1', gun: 'Gun game', team: 'Teams 5v5', war: 'War 10v10', ctf: 'Capture the flag' };""")

sub("""      : (mode === 'duel' ? 'FIGHT' : (mode === 'team' || mode === 'war' ? 'DEPLOY' : 'START LADDER'));""",
    """      : (mode === 'duel' ? 'FIGHT' : (mode === 'team' || mode === 'war' || mode === 'ctf' ? 'DEPLOY' : 'START LADDER'));""")

sub("""    } else if (mode === 'team' || mode === 'war') {
      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];""",
"""    } else if (mode === 'team' || mode === 'war' || mode === 'ctf') {
      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];""")

sub("""    $('squadPick').hidden = (mode === 'team' || mode === 'war');""",
    """    $('squadPick').hidden = (mode === 'team' || mode === 'war' || mode === 'ctf');""")

# --- state ---------------------------------------------------------------
sub("""  var decals = [], impacts = [], deaths = [], nades = [];""",
    """  var decals = [], impacts = [], deaths = [], nades = [], flags = [];""")

sub("""    decals = []; impacts = []; deaths = []; nades = [];""",
    """    decals = []; impacts = []; deaths = []; nades = []; flags = [];""")

# bases sit at each side's drop point
sub("""    spawnLoot(sp);
    elFeed.innerHTML = '';""",
"""    if (MODE.ctf) {
      var acc = [{ x: 0, y: 0, n: 0 }, { x: 0, y: 0, n: 0 }];
      ents.forEach(function (e) {
        var a = acc[e.team];
        a.x += e.x; a.y += e.y; a.n++;
      });
      flags = [0, 1].map(function (t) {
        var a = acc[t], hx = a.n ? a.x / a.n : WORLD_W / 2, hy = a.n ? a.y / a.n : WORLD_H / 2;
        return { team: t, hx: hx, hy: hy, x: hx, y: hy, home: true, carrier: null, ping: 0 };
      });
    }

    spawnLoot(sp);
    elFeed.innerHTML = '';""")

# --- the flag game -------------------------------------------------------
sub("""  function updateNades(dt) {""",
"""  function flagState(f) { return f.carrier ? 'TAKEN' : (f.home ? 'HOME' : 'DROPPED'); }

  function updateFlags(dt) {
    for (var i = 0; i < flags.length; i++) {
      var f = flags[i];

      // a carrier who is dead or down loses it where they fell
      if (f.carrier && (!f.carrier.alive || f.carrier.down)) {
        f.x = f.carrier.x; f.y = f.carrier.y;
        f.carrier = null; f.home = false;
        feed('<b>' + (f.team === player.team ? 'YOUR' : 'THEIR') + '</b> flag dropped', f.team !== player.team);
      }

      if (f.carrier) {
        f.x = f.carrier.x; f.y = f.carrier.y;
        f.ping -= dt;
        if (f.ping <= 0) { f.ping = 1.0; emit(f.x, f.y, FLAG_SND, -1, 'flag'); }
        // home with it? only counts if your own flag is on its stand
        var own = flags[f.carrier.team];
        var d = Math.sqrt((f.carrier.x - own.hx) * (f.carrier.x - own.hx) + (f.carrier.y - own.hy) * (f.carrier.y - own.hy));
        if (d < 34 && own.home && !own.carrier) {
          score[f.carrier.team]++;
          var mine = f.carrier.team === player.team;
          feed('<b>' + (f.carrier === player ? 'YOU' : f.carrier.name) + '</b> captured', mine);
          f.carrier = null; f.home = true; f.x = f.hx; f.y = f.hy;
          if (score[mine ? player.team : 1 - player.team] >= MODE.target) {
            finish(mine, mine ? 'Three flags home. That is the match.'
                              : 'They ran the third one home.');
            return;
          }
        }
        continue;
      }

      // on the ground: enemies take it, teammates send it back
      for (var j = 0; j < ents.length; j++) {
        var e = ents[j];
        if (!e.alive || e.down) continue;
        var dd = Math.sqrt((e.x - f.x) * (e.x - f.x) + (e.y - f.y) * (e.y - f.y));
        if (dd > 24) continue;
        if (e.team !== f.team) {
          f.carrier = e; f.home = false; f.ping = 0.5;
          feed('<b>' + (e === player ? 'YOU' : e.name) + '</b> took ' + (f.team === player.team ? 'your' : 'their') + ' flag',
               e.team === player.team);
          break;
        } else if (!f.home) {
          f.home = true; f.x = f.hx; f.y = f.hy;
          feed('<b>' + (f.team === player.team ? 'YOUR' : 'THEIR') + '</b> flag returned', f.team === player.team);
          break;
        }
      }
    }
  }

  function updateNades(dt) {""")

sub("""    updateBullets(dt);
    updateNades(dt);""",
"""    updateBullets(dt);
    updateNades(dt);
    if (MODE.ctf && state === 'play') updateFlags(dt);""")

# --- bots play the objective ---------------------------------------------
sub("""          // a downed squadmate outranks anything else lying around""",
"""          if (MODE.ctf && flags.length === 2) {
            var ours = flags[e.team], theirs = flags[1 - e.team];
            if (theirs.carrier === e) want = { x: ours.hx, y: ours.hy };          // run it home
            else if (!ours.home && !ours.carrier) want = { x: ours.x, y: ours.y }; // recover ours
            else if (!theirs.carrier) want = { x: theirs.x, y: theirs.y };         // go get theirs
            else if (theirs.carrier.team === e.team) want = { x: theirs.carrier.x, y: theirs.carrier.y };
            else want = { x: ours.hx, y: ours.hy };                                // hold home
            if (want) following = true;
          }
          // a downed squadmate outranks anything else lying around""")

# --- drawn on the field ---------------------------------------------------
sub("""    for (i = 0; i < nades.length; i++) {""",
"""    for (i = 0; i < flags.length; i++) {
      var fl2 = flags[i];
      var ft = TEAM_TINT[fl2.team === player.team ? 0 : 1];
      ctx.strokeStyle = 'rgba(' + ft + ',.30)';       // the stand is a known landmark
      ctx.lineWidth = 2 / zoom;
      ctx.beginPath(); ctx.arc(fl2.hx, fl2.hy, 30, 0, 6.2832); ctx.stroke();
      if (fl2.carrier) continue;                      // drawn on the carrier instead
      ctx.strokeStyle = 'rgba(' + ft + ',.95)';
      ctx.lineWidth = 2.2 / zoom;
      ctx.beginPath(); ctx.moveTo(fl2.x, fl2.y + 9); ctx.lineTo(fl2.x, fl2.y - 13); ctx.stroke();
      ctx.fillStyle = 'rgba(' + ft + ',.9)';
      ctx.beginPath();
      ctx.moveTo(fl2.x, fl2.y - 13); ctx.lineTo(fl2.x + 14, fl2.y - 8); ctx.lineTo(fl2.x, fl2.y - 3);
      ctx.closePath(); ctx.fill();
    }

    for (i = 0; i < nades.length; i++) {""")

# a carrier flies it
sub("""      if (e !== player) {
        var hw = 22, hp0 = clamp(e.hp / 100, 0, 1);""",
"""      for (var cf = 0; cf < flags.length; cf++) {
        if (flags[cf].carrier !== e) continue;
        var cft = TEAM_TINT[flags[cf].team === player.team ? 0 : 1];
        ctx.strokeStyle = 'rgba(' + cft + ',.95)';
        ctx.lineWidth = 2 / zoom;
        ctx.beginPath(); ctx.moveTo(e.x, e.y - 6); ctx.lineTo(e.x, e.y - 24); ctx.stroke();
        ctx.fillStyle = 'rgba(' + cft + ',.9)';
        ctx.beginPath();
        ctx.moveTo(e.x, e.y - 24); ctx.lineTo(e.x + 13, e.y - 19); ctx.lineTo(e.x, e.y - 14);
        ctx.closePath(); ctx.fill();
      }
      if (e !== player) {
        var hw = 22, hp0 = clamp(e.hp / 100, 0, 1);""")

# --- minimap: bases always, flags only when you could know ---------------
sub("""    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (!a.alive || a === player || a.team !== player.team) continue;
      ctx.fillStyle = '#7ce7d8';""",
"""    for (var fi = 0; fi < flags.length; fi++) {
      var mf = flags[fi];
      var mt = mf.team === player.team ? '124,231,216' : '255,122,77';
      ctx.strokeStyle = 'rgba(' + mt + ',.6)';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(mx(mf.hx), my(mf.hy), 4, 0, 6.2832); ctx.stroke();
      var known = mf.home || (mf.carrier && mf.carrier.team === player.team) || visibleToPlayer(mf.x, mf.y);
      if (known) {
        ctx.fillStyle = 'rgba(' + mt + ',.95)';
        ctx.fillRect(mx(mf.x) - 2, my(mf.y) - 3, 4, 6);
      }
    }
    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (!a.alive || a === player || a.team !== player.team) continue;
      ctx.fillStyle = '#7ce7d8';""")

# --- HUD ------------------------------------------------------------------
sub("""    } else if (mode === 'team' || mode === 'war') {
      elAlive.textContent = score[player.team] + ' \\u2013 ' + score[1 - player.team];""",
"""    } else if (mode === 'ctf') {
      elAlive.textContent = score[player.team] + ' \\u2013 ' + score[1 - player.team];
      elZone.className = 'zone-line';
      if (flags.length === 2) {
        elZone.textContent = 'YOURS ' + flagState(flags[player.team]) +
                             ' \\u00b7 THEIRS ' + flagState(flags[1 - player.team]) +
                             ' \\u00b7 FIRST TO ' + MODE.target;
      } else elZone.textContent = 'FIRST TO ' + MODE.target;
    } else if (mode === 'team' || mode === 'war') {
      elAlive.textContent = score[player.team] + ' \\u2013 ' + score[1 - player.team];""")

sub("""    else if (mode === 'team' || mode === 'war') {
      big = won ? 'WIN' : 'LOSS';
      small = score[player.team] + ' \\u2014 ' + score[1 - player.team];
    }""",
"""    else if (mode === 'team' || mode === 'war' || mode === 'ctf') {
      big = won ? 'WIN' : 'LOSS';
      small = score[player.team] + ' \\u2014 ' + score[1 - player.team];
    }""")

# kills in CTF just feed the respawn loop
sub("""    if (mode === 'team' || mode === 'war') {
      if (killer && killer !== e && foes(killer, e)) {""",
"""    if (mode === 'ctf') {
      e.respawnT = 2.4;
      return;
    }
    if (mode === 'team' || mode === 'war') {
      if (killer && killer !== e && foes(killer, e)) {""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p21 applied')
