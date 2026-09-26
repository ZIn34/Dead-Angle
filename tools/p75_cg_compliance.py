# -*- coding: utf-8 -*-
"""What the CrazyGames build needs and the standalone one does not: no gore
(their site is PEGI 12), a brighter frame, no chat, and an online button that
always ends in a match."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- one place that says how the CrazyGames build differs -------------------------
sub("""  var CG_MODE = window.DEAD_ANGLE_PLATFORM === 'crazygames';""",
"""  var CG_MODE = window.DEAD_ANGLE_PLATFORM === 'crazygames';
  // CrazyGames is a PEGI 12 site with a lot of daylight games on it. Their
  // build keeps the same fight but loses the blood and opens the view up.
  var GORE = !CG_MODE;""")

# ---- 1. no blood on their build -----------------------------------------------------
sub("""  function addSplat(x, y, r, pal, kind) {
    if (!SET.blood) return;""",
"""  function addSplat(x, y, r, pal, kind) {
    if (!SET.blood || !GORE) return;""")
sub("""    if (!SET.blood) { spark(x, y, big ? 10 : 4, '170,150,150', 120); return; }""",
    """    if (!SET.blood || !GORE) { spark(x, y, big ? 10 : 4, '196,204,214', 120); return; }""")
sub("""    if (FX.blood && SET.blood && amount >= 30) {""",
    """    if (FX.blood && SET.blood && GORE && amount >= 30) {""")
sub("""    if (FX.death && SET.blood) {""",
    """    if (FX.death && SET.blood && GORE) {""")

# ---- 2. a frame you can actually see -------------------------------------------------
sub("""  var FOV_HALF = 0.96, NEAR_SEE = 60;""",
"""  var FOV_HALF = CG_MODE ? 1.28 : 0.96, NEAR_SEE = CG_MODE ? 120 : 60;""")
sub("""    g.addColorStop(1, 'rgba(4,6,10,.93)');""",
    """    g.addColorStop(1, CG_MODE ? 'rgba(4,6,10,.74)' : 'rgba(4,6,10,.93)');""")
# ground you have already walked keeps a little more light on their build
sub("""    if (packed) {
      tilePass(r0, r1, t0, t1, true, false, 0, '#0b1016');
      tilePass(r0, r1, t0, t1, true, true, 0, '#141d27');""",
"""    if (packed) {
      tilePass(r0, r1, t0, t1, true, false, 0, CG_MODE ? '#131c26' : '#0b1016');
      tilePass(r0, r1, t0, t1, true, true, 0, CG_MODE ? '#202d3c' : '#141d27');""")

# ---- 3. no chat of ours on their build ------------------------------------------------
sub("""  function cgNoChat() { return !!cgSet.disableChat; }""",
    """  function cgNoChat() { return CG_MODE || !!cgSet.disableChat; }""")
sub("""    if (netRole && (state === 'play') && (k === 't' || k === 'enter') && $('igChat').hidden && !(player && player.invOpen)) { e.preventDefault(); openIgChat(); return; }""",
    """    if (netRole && !cgNoChat() && (state === 'play') && (k === 't' || k === 'enter') && $('igChat').hidden && !(player && player.invOpen)) { e.preventDefault(); openIgChat(); return; }""")
sub("""    $('acctBtn').hidden = true;
    $('friendsBtn').hidden = true;""",
"""    $('acctBtn').hidden = true;
    $('friendsBtn').hidden = true;
    if ($('chatHint')) $('chatHint').hidden = true;
    if ($('bloodRow')) $('bloodRow').hidden = true;""")

# ---- 4. online always ends in a match --------------------------------------------------
sub("""  function quickPlay() {""",
"""  // Whatever goes wrong out there - their SDK blocked, the broker down, an
  // empty site - the button has to end in a match, not a spinner.
  var quickGuard = 0;
  function quickWatch() {
    clearTimeout(quickGuard);
    quickGuard = setTimeout(function () {
      if (state === 'play' || state === 'paused') return;   // already playing
      if (queueOn || netRole === 'guest') return;           // in a lobby, leave it alone
      quickStatus('No match to join - starting one with bots.');
      if (netRole) netClose('');
      setTimeout(function () { if (state !== 'play') startMatch(); }, 700);
    }, 10000);
  }
  function quickPlay() {
    quickWatch();""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

h = io.open(H, encoding='utf-8').read(); ho = h
a = """        <span><kbd>T</kbd> party chat</span>"""
if a not in h:
    raise SystemExit('CHAT HINT NOT FOUND')
h = h.replace(a, """        <span id="chatHint"><kbd>T</kbd> party chat</span>""", 1)
assert h != ho
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p75 applied')
