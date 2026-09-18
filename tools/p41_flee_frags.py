# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:220])
    s = s.replace(a, b, 1)

# ==================================================== running when empty =====
# Remember whether an alert was gunfire - that is what an empty-handed bot
# should be running from even before it sees anyone.
sub("""            e.alertT = s.kind === 'shot' ? 7 : 4;""",
    """            e.alertT = s.kind === 'shot' ? 7 : 4;
            e.alertShot = s.kind === 'shot';""")

sub("""    var reloadRetreat = D.smart && e.reloadT > 0 && e.target && dist(e, e.target) < 420;""",
"""    // Nothing to fight with: run from anyone who does, and from gunfire.
    // An empty-handed stranger is no threat - keep looting past them.
    var threat = null;
    if (dry && !isZombie(e)) {
      if (e.target && curW(e.target)) threat = e.target;
      else if (e.alertT > 0 && e.alertShot) threat = { x: e.alertX, y: e.alertY };
    }
    var reloadRetreat = D.smart && e.reloadT > 0 && e.target && dist(e, e.target) < 420;""")

sub("""    } else if ((dry || reloadRetreat || hurtRetreat) && e.target) {
      // back off - empty, reloading, or patching up
      var fspeed = dry ? 254 : 200;""",
"""    } else if (threat) {
      // Pick somewhere well away from the danger and sprint for it. Running in
      // a straight line away just pins them against the nearest wall.
      if (!e.path || e.pathI >= e.path.length || e.repathT <= 0) {
        var here = dist(e, threat), bestT = null, bestS = -1e9;
        for (var ft = 0; ft < 18; ft++) {
          var cand = floorTiles[rnd(floorTiles.length)];
          var cx5 = cand.x * TILE, cy5 = cand.y * TILE;
          var dT = Math.sqrt((cx5 - threat.x) * (cx5 - threat.x) + (cy5 - threat.y) * (cy5 - threat.y));
          var dM = Math.sqrt((cx5 - e.x) * (cx5 - e.x) + (cy5 - e.y) * (cy5 - e.y));
          if (dT < here + 120 || dM > 900) continue;
          var sc5 = dT - dM * 0.35;
          if (sc5 > bestS) { bestS = sc5; bestT = cand; }
        }
        if (bestT) pathTo(e, bestT.x * TILE, bestT.y * TILE, 1.1);
        else e.repathT = 0.3;
      }
      if (!followPath(e, dt, 254)) {
        // no route yet: at least get out of the line of fire
        var tdx = e.x - threat.x, tdy = e.y - threat.y, tl = Math.sqrt(tdx * tdx + tdy * tdy) || 1;
        moveEnt(e, tdx / tl * 254 * dt, tdy / tl * 254 * dt);
      }
      footstep(e, dt, true);
    } else if ((reloadRetreat || hurtRetreat) && e.target) {
      // back off - reloading, or patching up
      var fspeed = 200;""")

sub("""      footstep(e, dt, dry);
      if (hurtRetreat && !lineClear(e.x, e.y, e.target.x, e.target.y)) useMed(e);""",
"""      footstep(e, dt, false);
      if (hurtRetreat && !lineClear(e.x, e.y, e.target.x, e.target.y)) useMed(e);""")

# a gun with nothing left in it is a club
sub("""        if (slot.ammo <= 0) startReload(e);""",
"""        if (slot.ammo <= 0 && e.reserve <= 0) { if (dd < 38) melee(e); }
        else if (slot.ammo <= 0) startReload(e);""")

# ==================================================== frags, not a barrage ===
# They should still throw them - just not three in a row at the same person.
sub("""  var teamNadeT = [0, 0];            // a whole side shares one throwing window""",
    """  var teamNadeT = [0, 0];            // a whole side shares one throwing window
  var botFrags = 0;                  // thrown by bots this match, for tuning""")
sub("""    teamNadeT = [0, 0];""", """    teamNadeT = [0, 0]; botFrags = 0;""")

sub("""        if (gd > 140 && gd < 330 && lineClear(e.x, e.y, gt.x, gt.y)) {""",
    """        var recently = gt.fragAt !== undefined && matchTime - gt.fragAt < 10;
        if (!recently && gd > 140 && gd < 330 && lineClear(e.x, e.y, gt.x, gt.y)) {""")

sub("""            throwNade(e, 'frag', ga3, throwPower(gd));
            e.nadeT = rr(D.smart ? 16 : 30, D.smart ? 34 : 55);
            teamNadeT[e.team] = rr(5, 9);""",
"""            throwNade(e, 'frag', ga3, throwPower(gd));
            gt.fragAt = matchTime;             // nobody else frags them for a while
            botFrags++;
            e.nadeT = rr(D.smart ? 12 : 22, D.smart ? 24 : 40);
            teamNadeT[e.team] = rr(4, 7);""")

sub("""        mode: mode, live: live, armed: armed, withTarget: withTarget,""",
    """        mode: mode, live: live, armed: armed, withTarget: withTarget, botFrags: botFrags,""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p41 applied')
