# -*- coding: utf-8 -*-
"""Bleeding: 1 HP a second, at most 20 HP per wound."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

sub("""      e.bleeding = true; e.bleedBy = fromId;""",
    """      e.bleeding = true; e.bleedBy = fromId;
      e.bleedLeft = 20;                         // a wound costs at most 20 HP""")
sub("""      bl.hp -= 5 * dt;
      if (bl.hp <= 0) {""",
"""      var bd = Math.min(1 * dt, bl.bleedLeft || 0);    // 1 HP a second
      bl.hp -= bd; bl.bleedLeft = (bl.bleedLeft || 0) - bd;
      if (bl.bleedLeft <= 0 && bl.hp > 0) { bl.bleeding = false; continue; }
      if (bl.hp <= 0) {""")
sub("""      var bt = 'BLEEDING  \\u00b7  ' + promptKey('F', 'Y')""",
    """      var bt = 'BLEEDING ' + Math.ceil(player.bleedLeft || 0) + ' HP  \\u00b7  ' + promptKey('F', 'Y')""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p60 applied')
