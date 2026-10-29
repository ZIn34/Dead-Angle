# -*- coding: utf-8 -*-
"""Quick play loses its leave button (BACK already does it), and the match
settings stop hiding behind MATCH OPTIONS."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
h = io.open(H, encoding='utf-8').read(); ho = h
s = io.open(G, encoding='utf-8').read(); so = s

def subh(a, b):
    global h
    if a not in h:
        raise SystemExit('HTML PATTERN NOT FOUND:\n' + a[:200])
    h = h.replace(a, b, 1)

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('JS PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ---- DA-16: no STOP LOOKING; BACK is the way out ---------------------------------
sub("""    showIf('netLeave', !!netRole);""",
    """    showIf('netLeave', !!netRole && !quick);     // BACK is the way out of waiting""")
sub("""    $('netLeave').textContent = quick ? 'STOP LOOKING' : 'LEAVE ROOM';
""", "")
# backing out of the waiting room stops the search rather than leaving it running
sub("""  $('netBack').addEventListener('click', function () {
    quickStand();""",
"""  $('netBack').addEventListener('click', function () {
    quickStand();
    if (netView === 'quick' && netRole) netClose('');""")

# ---- DA-17: the settings are just there ------------------------------------------
subh("""        <button class="go ghost" id="optBtn" type="button" aria-expanded="false">MATCH OPTIONS</button>
""", "")
subh("""      <div class="opts" id="opts" hidden>""", """      <div class="opts" id="opts">""")
sub("""  $('optBtn').addEventListener('click', function () {
    var box = $('opts'), open = box.hidden;
    box.hidden = !open;
    this.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
""", "")
# the big PLAY at the bottom of the settings was there to close them; keep it, it
# saves scrolling back up
subh("""#optBtn[aria-expanded="true"]{background:var(--gold);color:var(--out)}
""", "")

io.open(H, 'w', encoding='utf-8', newline='').write(h)
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p85 applied')
