# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ------------------------------------------------------- war: 10 v 10 -------
sub("""  var NAMES = ['VESPER', 'MAGPIE', 'KESTREL', 'SABLE', 'JUNIPER', 'HOLLOW', 'CINDER', 'WREN', 'OTTER'];""",
"""  var NAMES = ['VESPER', 'MAGPIE', 'KESTREL', 'SABLE', 'JUNIPER', 'HOLLOW', 'CINDER', 'WREN', 'OTTER',
               'RAVEN', 'LARK', 'FINCH', 'HERON', 'SWIFT', 'PLOVER', 'MARTIN', 'ROOK', 'CRANE', 'TEAL'];""")

sub("""    team: { field: 10, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 30, teams: true }
  };""",
"""    team: { field: 10, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 30, teams: true },
    war:  { field: 20, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 75, teams: true }
  };""")

sub("""    team: 'Five against five,""",
"""    war: 'Twenty fighters, ten a side, first to seventy-five. A big map and constant contact - you will rarely be more than a few seconds from a firefight, and the ring of a shot is the only warning you get.',
    team: 'Five against five,""")

sub("""    else if (mode === 'team') genRooms(72, 72, 7, 14, 28, 2, true);""",
    """    else if (mode === 'team') genRooms(72, 72, 7, 14, 28, 2, true);
    else if (mode === 'war') genRooms(86, 86, 8, 16, 34, 2, true);""")

sub("""  var MODE_LABEL = { br: 'Battle royale', duel: '1v1', gun: 'Gun game', team: 'Teams 5v5' };""",
    """  var MODE_LABEL = { br: 'Battle royale', duel: '1v1', gun: 'Gun game', team: 'Teams 5v5', war: 'War 10v10' };""")

sub("""      : (mode === 'duel' ? 'FIGHT' : (mode === 'team' ? 'DEPLOY' : 'START LADDER'));""",
    """      : (mode === 'duel' ? 'FIGHT' : (mode === 'team' || mode === 'war' ? 'DEPLOY' : 'START LADDER'));""")

# every teams-style mode shares the same loadout and HUD path
sub("""    } else if (mode === 'team') {
      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];""",
"""    } else if (mode === 'team' || mode === 'war') {
      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];""")

sub("""    if (mode === 'team') {
      if (killer && killer !== e && foes(killer, e)) {""",
"""    if (mode === 'team' || mode === 'war') {
      if (killer && killer !== e && foes(killer, e)) {""")

sub("""    } else if (mode === 'team') {
      elAlive.textContent = score[player.team] + ' \\u2013 ' + score[1 - player.team];""",
"""    } else if (mode === 'team' || mode === 'war') {
      elAlive.textContent = score[player.team] + ' \\u2013 ' + score[1 - player.team];""")

sub("""    else if (mode === 'team') {
      big = won ? 'WIN' : 'LOSS';
      small = score[player.team] + ' \\u2014 ' + score[1 - player.team];
    }""",
"""    else if (mode === 'team' || mode === 'war') {
      big = won ? 'WIN' : 'LOSS';
      small = score[player.team] + ' \\u2014 ' + score[1 - player.team];
    }""")

sub("""    $('squadPick').hidden = (mode === 'team');""",
    """    $('squadPick').hidden = (mode === 'team' || mode === 'war');""")

# ------------------------------------------------------- skins and credits --
sub("""  var difficulty = 1, mode = 'br', mapKind = 'cqb', blackout = false, squad = 1;""",
"""  var difficulty = 1, mode = 'br', mapKind = 'cqb', blackout = false, squad = 1;
  // Everyone starts in plain grey; credits come from playing and buy the rest.
  var BASE_SKIN = 9;
  var WALLET = { coins: 0, owned: [BASE_SKIN], skin: BASE_SKIN };
  function loadWallet() {
    try {
      var raw = localStorage.getItem('earshot.wallet');
      if (raw) {
        var w = JSON.parse(raw);
        if (w && w.owned && w.owned.length) {
          WALLET = { coins: w.coins | 0, owned: w.owned, skin: w.skin | 0 };
          if (WALLET.owned.indexOf(WALLET.skin) < 0) WALLET.skin = BASE_SKIN;
        }
      }
    } catch (err) { /* private window or blocked storage - stay on the default */ }
  }
  function saveWallet() {
    try { localStorage.setItem('earshot.wallet', JSON.stringify(WALLET)); } catch (err) {}
  }
  function skinPrice(i) { return i === BASE_SKIN ? 0 : (i >= 12 ? 500 : 200); }
  function skinOwned(i) { return WALLET.owned.indexOf(i) >= 0; }""")

# the player wears what they chose
sub("""      ents.forEach(function (e, idx) { e.skin = pool[idx % pool.length]; e.team = idx; });
    }""",
"""      ents.forEach(function (e, idx) { e.skin = pool[idx % pool.length]; e.team = idx; });
    }
    player.skin = WALLET.skin;""")

# credits on the results screen
sub("""    result = { big: big, small: small, won: won };
    overCause = msg;""",
"""    var earned = kills * 12 + Math.round(matchTime / 6) + (won ? 80 : 0);
    WALLET.coins += earned;
    saveWallet();
    result = { big: big, small: small, won: won, earned: earned };
    overCause = msg + '  +' + earned + ' credits.';""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p15 applied')
