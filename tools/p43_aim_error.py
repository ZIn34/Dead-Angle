# -*- coding: utf-8 -*-
"""Bots aim like people: a first-shot miss they walk in, and a hand that wobbles."""
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:220])
    s = s.replace(a, b, 1)

# miss: opening error (rad) on a fresh target; settle: how fast it closes (1/s);
# wob: the steady sway that never goes away
sub("""dmg: 0.42, turn: 5.0,  lead: 0.25, smart: false, aimTol: 0.20 },""",
    """dmg: 0.42, turn: 5.0,  lead: 0.25, smart: false, aimTol: 0.20, miss: 0.34, settle: 1.1, wob: 0.075 },""")
sub("""dmg: 0.55, turn: 8.5,  lead: 0.75, smart: true,  aimTol: 0.15 },""",
    """dmg: 0.55, turn: 8.5,  lead: 0.75, smart: true,  aimTol: 0.15, miss: 0.26, settle: 1.6, wob: 0.055 },""")
sub("""dmg: 0.70, turn: 12.0, lead: 1.00, smart: true,  aimTol: 0.10 }""",
    """dmg: 0.70, turn: 12.0, lead: 1.00, smart: true,  aimTol: 0.10, miss: 0.18, settle: 2.3, wob: 0.038 }""")

sub("""  var botShots = 0, targetSwaps = 0; // diagnostics""",
    """  var botShots = 0, targetSwaps = 0; // diagnostics
  var botHits = 0, aimErrOn = true;""")
sub("""botShots = 0; targetSwaps = 0; killCauses = {};""",
    """botShots = 0; targetSwaps = 0; killCauses = {}; botHits = 0;""")
sub("""        botShots: botShots, targetSwaps: targetSwaps, killCauses: killCauses,""",
    """        botShots: botShots, botHits: botHits, targetSwaps: targetSwaps, killCauses: killCauses,""")

sub("""    if (godMode && e === player) return;""",
    """    var hitBy = ents[fromId];
    if (hitBy && hitBy.bot && hitBy !== e) botHits++;
    if (godMode && e === player) return;""")

# the aim itself
sub("""      var want2 = Math.atan2(aimY - e.y, aimX - e.x);
      var diff = ((want2 - e.ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;""",
"""      var want2 = Math.atan2(aimY - e.y, aimX - e.x);
      if (aimErrOn) want2 += aimError(e, tt, dd, dt, D);
      var diff = ((want2 - e.ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;""")

sub("""  // ---------------------------------------------------------------- player
  function updatePlayer(dt) {""",
"""  // Where a bot's hand actually is, relative to a perfect line on the target.
  // A fresh target starts well off to one side and the shots walk in; after
  // that a slow sway stays, bigger when the target is strafing, the bot is
  // moving, or it has just been hit.
  function aimError(e, tt, dd, dt, D) {
    if (e.aimTgt !== tt) {
      e.aimTgt = tt;
      e.aimOff = (Math.random() < 0.5 ? -1 : 1) * rr(0.55, 1) * D.miss;
      e.aimPh = rr(0, 6.28); e.aimPh2 = rr(0, 6.28);
    }
    e.aimOff *= Math.exp(-D.settle * dt);
    // sideways speed of the target as seen from here, in radians per second
    var ux = (tt.x - e.x) / (dd || 1), uy = (tt.y - e.y) / (dd || 1);
    var lat = Math.abs((tt.vx || 0) * -uy + (tt.vy || 0) * ux) / Math.max(dd, 60);
    var sway = D.wob * (1 + Math.min(lat * 2.2, 1.6) + ((e._spd || 0) > 40 ? 0.6 : 0) + (e.flinch > 0 ? 1.2 : 0));
    var t = matchTime;
    return e.aimOff + sway * (Math.sin(t * 2.1 + e.aimPh) * 0.65 + Math.sin(t * 5.3 + e.aimPh2) * 0.35);
  }

  // ---------------------------------------------------------------- player
  function updatePlayer(dt) {""")

# getting shot throws your aim
sub("""    e.hp -= amount;
    e.useT = 0;""",
"""    e.hp -= amount;
    e.useT = 0;
    if (e.bot) { e.flinch = 0.35; if (e.aimOff !== undefined) e.aimOff += rr(-0.06, 0.06); }""")
sub("""    e.fireT -= dt;
    if (e.reloadT > 0) {
      e.reloadT -= dt;""",
"""    e.fireT -= dt;
    if (e.flinch > 0) e.flinch -= dt;
    if (e.reloadT > 0) {
      e.reloadT -= dt;""")

sub("""    god: function (on) { godMode = !!on; return godMode; },""",
    """    god: function (on) { godMode = !!on; return godMode; },
    aimErr: function (on) { aimErrOn = !!on; return aimErrOn; },""")

assert s != o
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('p43 applied')
