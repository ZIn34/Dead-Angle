# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b, n=1):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, n)

# Everyone carries a team index. On their own, each fighter is their own team,
# so the same comparisons cover solo, duos and 5v5 without special cases.
sub("""  function foes(a, b) { return MODE.teams ? a.team !== b.team : true; }""",
    """  function foes(a, b) { return a.team !== b.team; }""")

sub("""  var difficulty = 1, mode = 'br', mapKind = 'cqb', blackout = false;""",
    """  var difficulty = 1, mode = 'br', mapKind = 'cqb', blackout = false, squad = 1;
  var fieldN = 10;                 // how many fighters this match actually has""")

# --- squad-aware field size and team assignment ---------------------------
sub("""    var sp = MODE.teams ? teamSpawns(MODE.field) : pickSpawns(MODE.field);
    player = makeEnt(sp[0], true, 'YOU');
    ents.push(player);
    for (var i = 1; i < MODE.field; i++) ents.push(makeEnt(sp[i % sp.length], false, NAMES[i - 1]));""",
"""    var per = MODE.teams ? (MODE.field >> 1) : squad;
    fieldN = MODE.field;
    if (squad > 1 && !MODE.teams && mode === 'duel') fieldN = 4;   // 1v1 becomes 2v2
    var sp = MODE.teams ? teamSpawns(fieldN)
           : (squad > 1 ? squadSpawns(Math.ceil(fieldN / squad), squad) : pickSpawns(fieldN));
    player = makeEnt(sp[0], true, 'YOU');
    ents.push(player);
    for (var i = 1; i < fieldN; i++) ents.push(makeEnt(sp[i % sp.length], false, NAMES[i - 1]));""")

sub("""    if (MODE.teams) {
      var half = MODE.field >> 1;
      ents.forEach(function (e, idx) {
        e.team = idx < half ? 0 : 1;
        var set = TEAM_SKINS[e.team];
        e.skin = set[(idx % half) % set.length];
      });
    } else {""",
"""    if (MODE.teams) {
      var half = fieldN >> 1;
      ents.forEach(function (e, idx) {
        e.team = idx < half ? 0 : 1;
        var set = TEAM_SKINS[e.team];
        e.skin = set[(idx % half) % set.length];
      });
    } else if (squad > 1) {
      var pool2 = [];
      for (var k2 = 0; k2 < 16; k2++) pool2.push(k2);
      shuffle(pool2);
      ents.forEach(function (e, idx) {
        e.team = Math.floor(idx / squad);         // partners share a team
        e.skin = pool2[idx % pool2.length];
      });
    } else {""")

sub("""      shuffle(pool);
      ents.forEach(function (e, idx) { e.skin = pool[idx % pool.length]; });
    }""",
"""      shuffle(pool);
      ents.forEach(function (e, idx) { e.skin = pool[idx % pool.length]; e.team = idx; });
    }""")

# --- partners drop together ------------------------------------------------
sub("""  // Two anchors as far apart as the map allows, one per side.""",
"""  // Squads land together: one anchor per squad, members a step apart.
  function squadSpawns(nTeams, per) {
    var anchors = pickSpawns(nTeams), out = [];
    for (var i = 0; i < nTeams; i++) {
      var a = anchors[i % anchors.length];
      for (var k = 0; k < per; k++) {
        var t = a;
        for (var tries = 0; tries < 30; tries++) {
          var cx2 = a.x + rnd(5) - 2, cy2 = a.y + rnd(5) - 2;
          if (!isWall(cx2, cy2)) { t = { x: cx2, y: cy2 }; break; }
        }
        out.push(t);
      }
    }
    return out;
  }

  // Two anchors as far apart as the map allows, one per side.""")

# --- friendly fire / senses / respawn now read the team index directly -----
sub("""          if (MODE.teams && ents[b.owner] && e.team === ents[b.owner].team) continue;""",
    """          if (ents[b.owner] && e.team === ents[b.owner].team) continue;""")
sub("""        if (MODE.teams && ents[s.owner] && ents[s.owner].team === e.team) { s.heard[e.id] = 1; continue; }""",
    """        if (ents[s.owner] && ents[s.owner].team === e.team) { s.heard[e.id] = 1; continue; }""")
sub("""      var sc = minD - (MODE.teams && friend < 1e8 ? friend * 0.25 : 0);""",
    """      var sc = minD - (friend < 1e8 ? friend * 0.25 : 0);""")
sub("""      var tint = MODE.teams
        ? TEAM_TINT[e.team === player.team ? 0 : 1]
        : (e === player ? '124,231,216' : '255,122,77');""",
"""      var tint = TEAM_TINT[e.team === player.team ? 0 : 1];""")
sub("""      drawUnit(en, (MODE.teams && en.team === player.team) ? '#8ff0e4' : '#ff7a4d');""",
    """      drawUnit(en, en.team === player.team ? '#8ff0e4' : '#ff7a4d');""")
sub("""    else feed('<b>' + kn + '</b> &rsaquo; ' + e.name, MODE.teams && killer && killer.team === player.team);""",
    """    else feed('<b>' + kn + '</b> &rsaquo; ' + e.name, !!(killer && killer.team === player.team));""")

# --- battle royale ends when one squad is left -----------------------------
sub("""    } else if (alive === 1 && player.alive) {
      finish(true, 'Last one standing. Nothing left to hear.', 1);
    }""",
"""    } else if (player.alive) {
      var live = {}, nTeams = 0;
      for (var q = 0; q < ents.length; q++) {
        if (ents[q].alive && !live[ents[q].team]) { live[ents[q].team] = 1; nTeams++; }
      }
      if (nTeams === 1) {
        finish(true, squad > 1 ? 'Your squad is the last one moving.'
                               : 'Last one standing. Nothing left to hear.', 1);
      }
    }""")

sub("""    if (mode === 'br') { big = '#' + place; small = 'OF ' + MODE.field; }""",
    """    if (mode === 'br') { big = '#' + place; small = 'OF ' + fieldN; }""")
sub("""      $('placeL').textContent = result.small;""",
    """      $('placeL').textContent = result.small;""")

# --- menu ------------------------------------------------------------------
sub("""  function syncMenu() {
    $('mapPick').hidden = mode !== 'br';""",
"""  function syncMenu() {
    $('mapPick').hidden = mode !== 'br';
    $('squadPick').hidden = (mode === 'team');""")

sub("""    if (blackout) t += '  \\u2014  BLACKOUT:""",
"""    if (squad > 1 && mode !== 'team') t += '  \\u2014  DUOS: you drop with a partner, you cannot hurt each other, and neither of you reacts to the other\\'s noise.';
    if (blackout) t += '  \\u2014  BLACKOUT:""")

sub("""  $('lightRow').addEventListener('click', function (ev) {""",
"""  $('squadRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    squad = parseInt(b.getAttribute('data-s'), 10);
    pressRow(this, 'data-s', String(squad));
    syncMenu();
  });
  $('lightRow').addEventListener('click', function (ev) {""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p12 applied')
