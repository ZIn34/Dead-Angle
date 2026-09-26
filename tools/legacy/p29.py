# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ==================================================== infection ==============
# Team 0 are the living, team 1 are not. Everything the team system already
# does - friendly fire, colours, sound filtering - carries straight over.
sub("""    sect: { field: 16, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 150, teams: true, sectors: 3 }
  };""",
"""    sect: { field: 16, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 150, teams: true, sectors: 3 },
    zomb: { field: 20, zone: false, loot: false, respawn: true,  label: 'ALIVE', teams: true, zombies: true, clock: 190 }
  };
  var ZOMBIE_SKIN = 8;""")

sub("""    sect: 'Three sectors,""",
"""    zomb: 'One of them turns at the start. The infected carry nothing and cannot shoot - they are faster than you, they find you without needing to see you, and a hit puts you on their side. Survive the clock and the living win; lose the last human and it is over.',
    sect: 'Three sectors,""")

sub("""    else if (mode === 'sect') genRooms(122, 122, 7, 15, 70, 2, true);""",
    """    else if (mode === 'sect') genRooms(122, 122, 7, 15, 70, 2, true);
    else if (mode === 'zomb') genRooms(112, 112, 7, 15, 62, 2, true);""")

sub("""  var MODE_LABEL = { br: 'Battle royale', duel: '1v1', gun: 'Gun game', team: 'Teams 5v5', war: 'War 10v10', ctf: 'Capture the flag', sect: 'Sector capture' };""",
    """  var MODE_LABEL = { br: 'Battle royale', duel: '1v1', gun: 'Gun game', team: 'Teams 5v5', war: 'War 10v10', ctf: 'Capture the flag', sect: 'Sector capture', zomb: 'Infection' };""")

sub("""  function foes(a, b) { return a.team !== b.team; }""",
"""  function foes(a, b) { return a.team !== b.team; }
  function isZombie(e) { return !!(MODE.zombies && e.team === 1); }""")

# --- loadouts -------------------------------------------------------------
sub("""    } else if (MODE.teams) {
      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];""",
"""    } else if (MODE.zombies && e.team === 1) {
      e.slots = [null, null]; e.slot = 0; e.reserve = 0;
      e.meds = 0; e.nades = 0; e.smokes = 0;
      e.skin = ZOMBIE_SKIN;
    } else if (MODE.teams) {
      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];""")

# --- one of them turns at the start --------------------------------------
sub("""    if (MODE.teams) {
      var half = fieldN >> 1;""",
"""    if (MODE.zombies) {
      ents.forEach(function (e, idx) { e.team = 0; e.skin = idx % 16; });
      var patient = 1 + rnd(Math.max(1, fieldN - 1));     // never the player
      ents[patient].team = 1;
      ents[patient].skin = ZOMBIE_SKIN;
      zombClock = MODE.clock;
    } else if (MODE.teams) {
      var half = fieldN >> 1;""")

sub("""  var decals = [], impacts = [], deaths = [], nades = [], flags = [], smokes = [], sectors = [], secTick = 0;""",
    """  var decals = [], impacts = [], deaths = [], nades = [], flags = [], smokes = [], sectors = [], secTick = 0;
  var zombClock = 0;""")

# the infected never arm themselves, even off a body
sub("""      } else if (it.type === 'gun' && e.bot) {""",
    """      } else if (it.type === 'gun' && e.bot && !isZombie(e)) {""")

# --- turning --------------------------------------------------------------
sub("""    if (mode === 'ctf' || mode === 'sect') {
      e.respawnT = 2.4;
      return;
    }""",
"""    if (MODE.zombies) {
      if (e.team === 0) {
        e.team = 1;
        e.skin = ZOMBIE_SKIN;
        charCache = {};
        if (e === player) feed('<b>YOU TURNED</b>', true);
        else feed('<b>' + e.name + '</b> turned', false);
      }
      e.respawnT = 3.2;
      return;
    }
    if (mode === 'ctf' || mode === 'sect') {
      e.respawnT = 2.4;
      return;
    }""")

# --- the clock and the two ways it ends ----------------------------------
sub("""    if (MODE.sectors && state === 'play') updateSectors(dt);""",
"""    if (MODE.sectors && state === 'play') updateSectors(dt);
    if (MODE.zombies && state === 'play') {
      zombClock -= dt;
      var living = 0;
      for (i = 0; i < ents.length; i++) if (ents[i].alive && ents[i].team === 0) living++;
      if (living === 0) {
        finish(player.team === 1, player.team === 1
          ? 'Nothing left breathing. The infected take it.'
          : 'The last of the living went down.');
      } else if (zombClock <= 0) {
        finish(player.team === 0, player.team === 0
          ? 'You held out. The living take it.'
          : 'They lasted the clock out.');
      }
    }""")

# --- the infected hunt ----------------------------------------------------
sub("""      if (best) {
        if (e.target !== best) e.reactT = D.react;""",
"""      // the infected do not need to see you
      if (!best && isZombie(e)) {
        var near2 = null, nd2 = 820;
        for (var zi = 0; zi < ents.length; zi++) {
          var zo = ents[zi];
          if (!zo.alive || zo.team === e.team) continue;
          var zd = dist(e, zo);
          if (zd < nd2) { nd2 = zd; near2 = zo; }
        }
        best = near2;
      }
      if (best) {
        if (e.target !== best) e.reactT = D.react;""")

sub("""    } else if (carrying) {""",
"""    } else if (isZombie(e) && e.target) {
      // straight at them, no cover, no hesitation
      var zt = e.target;
      var zdx = zt.x - e.x, zdy = zt.y - e.y;
      var zl = Math.sqrt(zdx * zdx + zdy * zdy) || 1;
      var zspeed = 244;
      var zbx = e.x, zby = e.y;
      moveEnt(e, zdx / zl * zspeed * dt, zdy / zl * zspeed * dt);
      if (Math.abs(e.x - zbx) + Math.abs(e.y - zby) < zspeed * dt * 0.4) {
        if (!e.path || e.repathT <= 0) pathTo(e, zt.x, zt.y, 0.7);
        followPath(e, dt, zspeed);
      }
      footstep(e, dt, true);
    } else if (carrying) {""")

# the living are quicker on their feet than usual; the infected quicker still
sub("""    var speed = w ? 165 : 186;""",
    """    var speed = isZombie(e) ? 244 : (w ? 165 : 186);""")

sub("""    var base = curW(e) ? 168 : 190;""",
    """    var base = curW(e) ? 168 : (MODE.zombies && e.team === 1 ? 236 : 190);""")

# --- HUD ------------------------------------------------------------------
sub("""    } else if (mode === 'sect') {""",
"""    } else if (mode === 'zomb') {
      var alive0 = 0, alive1 = 0;
      for (var zq = 0; zq < ents.length; zq++) {
        if (!ents[zq].alive) continue;
        if (ents[zq].team === 0) alive0++; else alive1++;
      }
      elAliveL.textContent = 'LIVING';
      elAlive.textContent = ('0' + alive0).slice(-2);
      elZone.className = 'zone-line' + (zombClock < 30 ? ' hot' : '');
      elZone.textContent = (player.team === 1 ? 'INFECTED \\u00b7 ' : 'SURVIVE \\u00b7 ')
        + fmtTime(zombClock) + ' \\u00b7 ' + alive1 + ' TURNED';
    } else if (mode === 'sect') {""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p29 applied')
