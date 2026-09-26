# -*- coding: utf-8 -*-
"""Remove the tactical wall lock entirely."""
import io, sys, re
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def cut(a, b=''):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# state + helpers
start = s.index('  var lean = { on: false')
end = s.index('  function updateLean(e, dt, ix, iy) {')
end2 = s.index('\n', s.index('    lean.peek = clamp(t, 0.10, 0.55);\n    return true;\n  }'))
block = s[start:s.index('    lean.peek = clamp(t, 0.10, 0.55);\n    return true;\n  }') + len('    lean.peek = clamp(t, 0.10, 0.55);\n    return true;\n  }') + 1]
s = s.replace(block, '', 1)

# the branch inside updatePlayer
cut("""    if (updateLean(e, dt, ix, iy)) {
      // locked to the corner: aim and fire still work, feet do not
      if (sticks.aim) {
        var ladx = sticks.aim.x - sticks.aim.ox, lady = sticks.aim.y - sticks.aim.oy;
        if (Math.sqrt(ladx * ladx + lady * lady) > 10) e.ang = Math.atan2(lady, ladx);
      } else e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);
      e.fireT -= dt;
      if (e.reloadT > 0) {
        e.reloadT -= dt;
        if (e.reloadT <= 0) finishReload(e);
      }
      var lfire = mouse.down || (sticks.aim && Math.abs(sticks.aim.x - sticks.aim.ox) + Math.abs(sticks.aim.y - sticks.aim.oy) > 26);
      if (lfire && curW(e)) {
        if (curSlot(e).ammo <= 0) startReload(e);
        else fire(e);
      }
      return;
    }
""")

cut("""
    if (!e.bot && lean.on) spread *= 0.5;      // braced on the corner""")

cut("""
    lean.on = false; lean.cool = 0;""")

cut(""" lean.on = false;""")

# the overlay
lstart = s.index('  function renderLean() {')
lend = s.index('  function renderPrompt() {')
s = s[:lstart] + s[lend:]

cut("""    renderLean();
""")

assert 'lean' not in s.replace('cleanly', ''), 'leftover lean reference'
assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p22 applied - tactical wall removed')
