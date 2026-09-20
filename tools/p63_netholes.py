# -*- coding: utf-8 -*-
"""A guest is only told about people nearby, so the roster has gaps. Fill them
with a quiet stand-in, or every loop that walks the roster trips over a hole."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s
a = """    for (i = 0; i < ents.length; i++) if (ents[i]) ents[i].hidden = !seen[i];"""
b = """    for (i = 0; i < ents.length; i++) {
      if (!ents[i]) { var st = makeEnt({ x: 0, y: 0 }, true, ''); st.id = i; st.alive = false; ents[i] = st; }
      ents[i].hidden = !seen[i];
    }"""
if a not in s:
    raise SystemExit('PATTERN NOT FOUND')
s = s.replace(a, b, 1)
assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p63 applied')
