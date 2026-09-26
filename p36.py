# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ==================================================== grenade discipline =====
# Per-bot cooldowns still let fifteen of them throw at once. One side gets one
# grenade in the air at a time, and only at something they can actually see.
sub("""  var zombClock = 0, zombSpawnT = 0;""",
    """  var zombClock = 0, zombSpawnT = 0;
  var teamNadeT = [0, 0];            // a whole side shares one throwing window""")

sub("""    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = []; secTick = 0;""",
    """    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = []; secTick = 0;
    teamNadeT = [0, 0];""")

sub("""    updateNades(dt);
    updateSmoke(dt);""",
"""    updateNades(dt);
    updateSmoke(dt);
    if (teamNadeT[0] > 0) teamNadeT[0] -= dt;
    if (teamNadeT[1] > 0) teamNadeT[1] -= dt;""")

sub("""    if (e.nades > 0 && e.nadeT <= 0 && !e.down) {
      var gt = e.target || (e.alertT > 3.5 ? { x: e.alertX, y: e.alertY } : null);
      if (gt) {
        var gd = Math.sqrt((gt.x - e.x) * (gt.x - e.x) + (gt.y - e.y) * (gt.y - e.y));
        if (gd > 105 && gd < 340 && lineClear(e.x, e.y, gt.x, gt.y)) {""",
"""    if (e.nades > 0 && e.nadeT <= 0 && teamNadeT[e.team] <= 0 && !e.down) {
      var gt = e.target;                      // something they can see, not a rumour
      if (gt) {
        var gd = dist(e, gt);
        if (gd > 140 && gd < 330 && lineClear(e.x, e.y, gt.x, gt.y)) {""")

sub("""            throwNade(e, 'frag', ga3, throwPower(gd));
            e.nadeT = rr(D.smart ? 6 : 13, D.smart ? 15 : 26);
            e.fireT = Math.max(e.fireT, 0.45);""",
"""            throwNade(e, 'frag', ga3, throwPower(gd));
            e.nadeT = rr(D.smart ? 16 : 30, D.smart ? 34 : 55);
            teamNadeT[e.team] = rr(5, 9);
            e.fireT = Math.max(e.fireT, 0.45);""")

# smoke gets the same treatment, less severely
sub("""        throwNade(e, 'smoke', sa3, throwPower(sd2 * 0.55));
        e.smokeT = rr(16, 30);""",
"""        throwNade(e, 'smoke', sa3, throwPower(sd2 * 0.55));
        e.smokeT = rr(26, 48);""")

# ==================================================== hold the whole map =====
# They were all walking to the same nearest sector. Give each of them a post,
# rotate the posts so it does not go stale, and let them redeploy to whatever
# their side does not already hold.
sub("""          if (MODE.sectors && sectors.length) {
            var pick = null, pickD = 1e9;
            for (var si = 0; si < sectors.length; si++) {
              var sq = sectors[si];
              var sd = dist(e, sq) * (sq.owner === e.team ? 2.2 : 1);   // prefer what is not yours
              if (sd < pickD) { pickD = sd; pick = sq; }
            }
            if (pick) { want = { x: pick.x, y: pick.y }; following = true; }
          }""",
"""          if (MODE.sectors && sectors.length) {
            var post = (e.id + Math.floor(matchTime / 28)) % sectors.length;
            var pick = sectors[post];
            if (pick.owner === e.team) {
              // ours already - go help somewhere it is not
              for (var si = 1; si < sectors.length; si++) {
                var alt = sectors[(post + si) % sectors.length];
                if (alt.owner !== e.team) { pick = alt; break; }
              }
            }
            want = { x: pick.x + rr(-70, 70), y: pick.y + rr(-70, 70) };
            following = true;
          }""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p36 applied')
