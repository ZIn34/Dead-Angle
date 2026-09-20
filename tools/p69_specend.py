# -*- coding: utf-8 -*-
"""In a battle royale your match is not over while a squadmate is still up:
you watch them, and the results wait until your side is gone."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

sub("""    if (e.local && !anyLocalAlive()) {
      finishAfterCam(e, false, killer && killer !== e
        ? kn + ' put ' + ((locals.length > 1) ? e.name : 'you') + ' down at ' + Math.round(dist(e, killer)) + ' units.'
        : 'The zone closed over ' + ((locals.length > 1) ? e.name : 'you') + '.', alive + 1);
    } else if (anyLocalAlive()) {""",
"""    if (e.local && !anyLocalAlive()) {
      var endMsg = killer && killer !== e
        ? kn + ' put ' + ((locals.length > 1) ? e.name : 'you') + ' down at ' + Math.round(dist(e, killer)) + ' units.'
        : 'The zone closed over ' + ((locals.length > 1) ? e.name : 'you') + '.';
      // squadmates still up: stay in the match and watch them instead
      if (specMates(e).length) e.pendEnd = [false, endMsg, alive + 1];
      else finishAfterCam(e, false, endMsg, alive + 1);
    } else if (anyLocalAlive()) {""")

sub("""  // keep the view on someone who is still standing
  function specTick() {""",
"""  // the results wait for the last of your side, win or lose
  function specEndCheck() {
    for (var i = 0; i < locals.length; i++) {
      var L = locals[i];
      if (L.alive || !L.pendEnd || L.kc || state !== 'play') continue;
      if (specMates(L).length) {
        var live = {}, n = 0;
        for (var q = 0; q < ents.length; q++) {
          if (ents[q] && ents[q].alive && !live[ents[q].team]) { live[ents[q].team] = 1; n++; }
        }
        // they took the whole thing while you watched
        if (n === 1 && live[L.team]) { L.pendEnd = null; finish(true, 'Your squad is the last one moving.', 1); }
        continue;
      }
      var pe = L.pendEnd; L.pendEnd = null;
      finishAfterCam(L, pe[0], pe[1], pe[2]);
    }
  }
  // keep the view on someone who is still standing
  function specTick() {""")
sub("""    pingTick(dt);
    specTick();""", """    pingTick(dt);
    specTick();
    specEndCheck();""")
# a fresh life or a new match carries nothing over
sub("""    e.alive = true; e.respawnT = 0; e.bleeding = false;""",
    """    e.alive = true; e.respawnT = 0; e.bleeding = false; e.pendEnd = null; e.spec = null;""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p69 applied')
