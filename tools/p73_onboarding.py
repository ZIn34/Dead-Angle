# -*- coding: utf-8 -*-
"""Onboarding the way CrazyGames asks for it: show the key instead of
describing it, keep the words short, and put a plain SKIP button on screen."""
import io, re, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- shorter words, and a picture of the control for every step ------------------
STEPS = [
  ("""    { title: 'MOVE', k: 'W A S D to walk', p: 'LEFT STICK to walk',
      done: function () { return tut.moved > 260; } },""",
   """    { title: 'MOVE', k: 'Walk around', p: 'Walk around', g: { wasd: 1 }, gp: { caps: ['LEFT STICK'] },
      done: function () { return tut.moved > 260; } },"""),
  ("""    { title: 'AIM', k: 'Point with the MOUSE - you always face it', p: 'Point with the RIGHT STICK',
      done: function () { return tut.t > 2.5; } },""",
   """    { title: 'AIM', k: 'You always face the cursor', p: 'You face where the stick points',
      g: { mouse: 'move' }, gp: { caps: ['RIGHT STICK'] },
      done: function () { return tut.t > 2.5; } },"""),
  ("""    { title: 'SHOOT', k: 'Follow the gold marker to the targets. CLICK to shoot one', p: 'Follow the gold marker to the targets. RT to shoot one', mark: 'targets',
      done: function () { return tut.hits >= 1; } },""",
   """    { title: 'SHOOT', k: 'Shoot a target', p: 'Shoot a target', mark: 'targets',
      g: { mouse: 'left' }, gp: { caps: ['RT'] },
      done: function () { return tut.hits >= 1; } },"""),
  ("""    { title: 'RELOAD', k: 'R to reload', p: 'A to reload',""",
   """    { title: 'RELOAD', k: 'Reload', p: 'Reload', g: { caps: ['R'] }, gp: { caps: ['A'] },"""),
  ("""    { title: 'PICK UP', k: 'Walk to the rifle (gold marker) and press E', p: 'Walk to the rifle (gold marker) and press X', mark: 'item',""",
   """    { title: 'PICK UP', k: 'Take the rifle', p: 'Take the rifle', mark: 'item',
      g: { caps: ['E'] }, gp: { caps: ['X'] },"""),
  ("""    { title: 'SWAP', k: 'Q (or 1 / 2) swaps weapons', p: 'LB or RB swaps weapons',""",
   """    { title: 'SWAP', k: 'Swap weapons', p: 'Swap weapons',
      g: { caps: ['Q', '1', '2'] }, gp: { caps: ['LB', 'RB'] },"""),
  ("""    { title: 'SPRINT', k: 'Hold SHIFT while walking - fast, but loud', p: 'Hold LT while walking - fast, but loud',""",
   """    { title: 'SPRINT', k: 'Hold it while walking - fast, but loud', p: 'Hold it while walking - fast, but loud',
      g: { caps: ['SHIFT'] }, gp: { caps: ['LT'] },"""),
  ("""    { title: 'FRAG', k: 'G throws a frag - hit the group', p: 'D-PAD LEFT throws a frag - hit the group', mark: 'targets',""",
   """    { title: 'FRAG', k: 'Throw a frag at the group', p: 'Throw a frag at the group', mark: 'targets',
      g: { caps: ['G'] }, gp: { caps: ['D-PAD LEFT'] },"""),
  ("""    { title: 'SMOKE', k: 'H throws smoke - nobody sees through it', p: 'D-PAD RIGHT throws smoke - nobody sees through it',""",
   """    { title: 'SMOKE', k: 'Throw smoke - nobody sees through it', p: 'Throw smoke - nobody sees through it',
      g: { caps: ['H'] }, gp: { caps: ['D-PAD RIGHT'] },"""),
  ("""    { title: 'HEAL', k: 'You are hurt. F uses a stim', p: 'You are hurt. Y uses a stim',""",
   """    { title: 'HEAL', k: 'You are hurt - use a stim', p: 'You are hurt - use a stim',
      g: { caps: ['F'] }, gp: { caps: ['Y'] },"""),
  ("""    { title: 'MELEE', k: 'V swings the gun butt - works with no ammo', p: 'D-PAD UP (or click the right stick) swings the gun butt',""",
   """    { title: 'MELEE', k: 'Swing the gun butt - works with no ammo', p: 'Swing the gun butt - works with no ammo',
      g: { caps: ['V'] }, gp: { caps: ['D-PAD UP'] },"""),
  ("""    { title: 'READY', k: 'That is everything. Press ENTER for the menu.', p: 'That is everything. Press A for the menu.',""",
   """    { title: 'READY', k: 'That is everything.', p: 'That is everything.',
      g: { caps: ['ENTER'] }, gp: { caps: ['A'] },"""),
]
for a, b in STEPS:
    sub(a, b)

# ---- drawing the keys ---------------------------------------------------------------
sub("""  function renderTutorial() {""",
"""  // A key cap, drawn the way it looks under a finger. Showing the control
  // beats another sentence about it.
  function capW(label) {
    ctx.font = '700 12px "IBM Plex Mono", monospace';
    return Math.max(32, ctx.measureText(label).width + 20);
  }
  function capBox(label, cx, y) {
    var w = capW(label), h = 30, x = cx - w / 2;
    ctx.fillStyle = '#f2bd1d'; ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 3;
    ctx.fillRect(x, y, w, h); ctx.strokeRect(x, y, w, h);
    ctx.fillStyle = '#0d0f12';
    ctx.fillRect(x + 2, y + h - 5, w - 4, 3);
    ctx.font = '700 12px "IBM Plex Mono", monospace';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(label, cx, y + h / 2 - 1);
    return w;
  }
  function capRow(list, cx, y) {
    var i, total = 0, ws = [];
    for (i = 0; i < list.length; i++) { ws.push(capW(list[i])); total += ws[i] + 8; }
    var x = cx - (total - 8) / 2;
    for (i = 0; i < list.length; i++) { capBox(list[i], x + ws[i] / 2, y); x += ws[i] + 8; }
  }
  function capWasd(cx, y) {
    capBox('W', cx, y);
    capBox('A', cx - 40, y + 34); capBox('S', cx, y + 34); capBox('D', cx + 40, y + 34);
  }
  function mouseGlyph(cx, y, kind) {
    var w = 30, h = 42, x = cx - w / 2;
    ctx.fillStyle = '#1d2d3b'; ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 3;
    ctx.fillRect(x, y, w, h); ctx.strokeRect(x, y, w, h);
    if (kind === 'left') {                       // the button you press, lit
      ctx.fillStyle = '#f2bd1d';
      ctx.fillRect(x + 2, y + 2, w / 2 - 3, h / 3);
    }
    ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, y + h / 3); ctx.lineTo(x + w, y + h / 3);
    ctx.moveTo(cx, y); ctx.lineTo(cx, y + h / 3);
    ctx.stroke();
    if (kind === 'move') {                       // a nudge either way
      ctx.strokeStyle = '#f2bd1d'; ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(x - 10, y + h * 0.62); ctx.lineTo(x - 22, y + h * 0.62);
      ctx.moveTo(x + w + 10, y + h * 0.62); ctx.lineTo(x + w + 22, y + h * 0.62);
      ctx.stroke();
      ctx.fillStyle = '#f2bd1d';
      ctx.beginPath(); ctx.moveTo(x - 26, y + h * 0.62); ctx.lineTo(x - 18, y + h * 0.62 - 5); ctx.lineTo(x - 18, y + h * 0.62 + 5); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(x + w + 26, y + h * 0.62); ctx.lineTo(x + w + 18, y + h * 0.62 - 5); ctx.lineTo(x + w + 18, y + h * 0.62 + 5); ctx.closePath(); ctx.fill();
    }
  }
  function drawStepGlyph(st, cx, y) {
    var g = (usingPad(player) && st.gp) ? st.gp : st.g;
    if (!g) return;
    ctx.save();
    if (g.wasd) capWasd(cx, y);
    else if (g.mouse) mouseGlyph(cx, y, g.mouse);
    else if (g.caps) capRow(g.caps, cx, y);
    ctx.restore();
  }

  function renderTutorial() {""")
sub("""    for (var li = 0; li < lines.length; li++) ctx.fillText(lines[li], cw / 2, by + 46 + li * 19);""",
"""    for (var li = 0; li < lines.length; li++) ctx.fillText(lines[li], cw / 2, by + 46 + li * 19);
    drawStepGlyph(st, cw / 2, by + bh + 14);""")

# ---- a plain button to leave, no key needed -------------------------------------------
sub("""  function tutDone() {""",
"""  function tutLeave() {
    if (mode !== 'tut' || tut.leaving) return;
    tut.leaving = true;
    setTimeout(tutDone, 0);
  }
  if ($('tutSkip')) $('tutSkip').addEventListener('click', tutLeave);
  function tutDone() {""")
sub("""  function syncHud() {""",
"""  function syncHud() {
    var sk = $('tutSkip');
    if (sk) sk.hidden = !(mode === 'tut' && state === 'play');""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

h = io.open(H, encoding='utf-8').read(); ho = h
a = """  <div class="hud" id="hud" hidden>"""
if a not in h:
    raise SystemExit('HUD NOT FOUND')
h = h.replace(a, a + """
    <button class="tutskip" id="tutSkip" type="button" hidden>SKIP TUTORIAL</button>""", 1)
b = """.hud{position:absolute;inset:0;pointer-events:none;font-family:var(--font-m)}"""
h = h.replace(b, b + """
.tutskip{position:absolute;top:calc(14px + env(safe-area-inset-top,0px));left:calc(16px + env(safe-area-inset-left,0px));pointer-events:auto;appearance:none;border:3px solid var(--out);background:var(--navy);color:var(--paper);font-family:var(--font-m);font-size:10.5px;font-weight:600;letter-spacing:.14em;padding:8px 14px;cursor:pointer;box-shadow:3px 3px 0 rgba(0,0,0,.45)}
.tutskip:hover{background:var(--gold);color:var(--out)}""", 1)
assert h != ho
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p73 applied')
