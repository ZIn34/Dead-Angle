# -*- coding: utf-8 -*-
import io, sys, re
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ==================================================== the SMG is gone ========
s = re.sub(r"\n    smg:      \{ name: 'SMG',.*?\n", "\n", s, count=1)

sub("""  var WEAPON_KEYS = ['pistol', 'smg', 'shotgun', 'rifle', 'silenced'];
  var WEAPON_WEIGHT = [30, 26, 18, 14, 12];
  var LADDER = ['pistol', 'smg', 'shotgun', 'rifle', 'silenced'];""",
"""  var WEAPON_KEYS = ['pistol', 'shotgun', 'rifle', 'silenced'];
  var WEAPON_WEIGHT = [32, 22, 20, 26];
  var LADDER = ['pistol', 'shotgun', 'rifle', 'silenced'];""")

sub("""  var WEAP_IDX = { pistol: 2, smg: 3, silenced: 3, shotgun: 4, rifle: 4 };
  var WEAP_MUL = { pistol: 1.0, smg: 0.92, silenced: 1.05, shotgun: 1.0, rifle: 1.18 };""",
"""  var WEAP_IDX = { pistol: 2, silenced: 3, shotgun: 4, rifle: 4 };
  var WEAP_MUL = { pistol: 1.0, silenced: 1.05, shotgun: 1.0, rifle: 1.18 };""")

sub("""      var prim = ['smg', 'shotgun', 'rifle', 'silenced'][rnd(4)];""",
    """      var prim = ['shotgun', 'rifle', 'silenced'][rnd(3)];""")

sub("""        var src = buildChar(idx, 'smg');""", """        var src = buildChar(idx, 'rifle');""")

sub("""pistol, SMG, shotgun, sniper, rifle. Get a kill with the rifle to win.""",
    """pistol, shotgun, sniper, rifle. Get a kill with the rifle to win.""")

# ==================================================== always face the aim ====
sub("""    var rx = pad ? padAxis(2) : 0, ry = pad ? padAxis(3) : 0;
    if (rx || ry) {
      e.ang = aimAssist(e, Math.atan2(ry, rx));
    } else if (sticks.aim) {
      var adx = sticks.aim.x - sticks.aim.ox, ady = sticks.aim.y - sticks.aim.oy;
      if (Math.sqrt(adx * adx + ady * ady) > 10) e.ang = Math.atan2(ady, adx);
    } else if (!pad) e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);""",
"""    // Face the right stick if it is pushed; otherwise where you are walking on
    // a pad; otherwise the cursor. Never left pointing at nothing.
    var rx = pad ? padAxis(2) : 0, ry = pad ? padAxis(3) : 0;
    if (rx || ry) {
      e.ang = aimAssist(e, Math.atan2(ry, rx));
    } else if (sticks.aim) {
      var adx = sticks.aim.x - sticks.aim.ox, ady = sticks.aim.y - sticks.aim.oy;
      if (Math.sqrt(adx * adx + ady * ady) > 10) e.ang = Math.atan2(ady, adx);
    } else if (padActive() && (ix || iy)) {
      e.ang = Math.atan2(iy, ix);
    } else {
      e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);
    }""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p39 applied')
