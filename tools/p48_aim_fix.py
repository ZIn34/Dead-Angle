# -*- coding: utf-8 -*-
"""Keyboard+mouse aim no longer hijacked by a resting controller; pad aim line."""
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:220])
    s = s.replace(a, b, 1)

# Some pads report triggers (and worn sticks) far off zero while nobody is
# touching them, which read as "the pad is in use" forever - so walking with
# WASD turned you to face the walk instead of the mouse. Judge movement
# against where each axis rests, and let whichever device moved last win.
sub("""  function pollPad() {""",
"""  var padRest = {}, kbmLast = -1e9;
  function padBusy(g) {
    var rest = padRest[g.index];
    if (!rest) { rest = padRest[g.index] = g.axes.slice(); return false; }
    for (var j = 0; j < g.buttons.length; j++) if (g.buttons[j] && g.buttons[j].pressed) return true;
    for (j = 0; j < g.axes.length; j++) if (Math.abs(g.axes[j] - (rest[j] || 0)) > 0.45) return true;
    return false;
  }
  function pollPad() {""")
sub("""    var busy = false, j;
    for (j = 0; j < pad.buttons.length; j++) if (pad.buttons[j] && pad.buttons[j].pressed) { busy = true; break; }
    if (!busy) for (j = 0; j < pad.axes.length; j++) if (Math.abs(pad.axes[j]) > 0.45) { busy = true; break; }
    if (busy) padLast = performance.now();
  }
  function padActive() { return !!pad && (performance.now() - padLast) < 10000; }""",
"""    if (padBusy(pad)) padLast = performance.now();
  }
  function padActive() {
    return !!pad && padLast > kbmLast && (performance.now() - padLast) < 10000;
  }""")
sub("""    if (g) {
      var busy = false, j;
      for (j = 0; j < g.buttons.length; j++) if (g.buttons[j] && g.buttons[j].pressed) { busy = true; break; }
      if (!busy) for (j = 0; j < g.axes.length; j++) if (Math.abs(g.axes[j]) > 0.45) { busy = true; break; }
      if (busy) e.padLast = performance.now();
    }""",
"""    if (g && padBusy(g)) e.padLast = performance.now();""")
sub("""    return (performance.now() - (e.padLast || -1e9)) < 10000;
  }""",
"""    return (e.padLast || -1e9) > kbmLast && (performance.now() - (e.padLast || -1e9)) < 10000;
  }""")

# the mouse and keyboard mark themselves as the device in use
sub("""  canvas.addEventListener('pointerdown', function (ev) {""",
    """  canvas.addEventListener('pointerdown', function (ev) {
    if (ev.pointerType !== 'touch') kbmLast = performance.now();""")
sub("""  canvas.addEventListener('pointermove', function (ev) {""",
    """  canvas.addEventListener('pointermove', function (ev) {
    if (ev.pointerType !== 'touch' && (Math.abs(ev.movementX || 0) + Math.abs(ev.movementY || 0)) > 2) kbmLast = performance.now();""")
sub("""  window.addEventListener('keydown', function (e) {""",
    """  window.addEventListener('keydown', function (e) {
    kbmLast = performance.now();""")

# a dotted line out to the pad's aim dot
sub("""    var sx3 = (player.x + cx3 * d - cam.x) * zoom + cw / 2;
    var sy3 = (player.y + cy3 * d - cam.y) * zoom + ch / 2;""",
"""    var sx3 = (player.x + cx3 * d - cam.x) * zoom + cw / 2;
    var sy3 = (player.y + cy3 * d - cam.y) * zoom + ch / 2;
    var ox3 = (player.x + cx3 * (player.r + 10) - cam.x) * zoom + cw / 2;
    var oy3 = (player.y + cy3 * (player.r + 10) - cam.y) * zoom + ch / 2;
    ctx.save();
    ctx.strokeStyle = 'rgba(124,231,216,.45)';
    ctx.lineWidth = 1.6;
    ctx.setLineDash([2, 7]);
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(ox3, oy3); ctx.lineTo(sx3, sy3); ctx.stroke();
    ctx.restore();""")

assert s != o
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('p48 applied')
