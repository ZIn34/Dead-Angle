# -*- coding: utf-8 -*-
"""CrazyGames quality pass: keys by their place on the board (AZERTY, QWERTZ),
a real document head so phones lay the page out properly, and P for pause so
nobody has to fight Escape in fullscreen."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- read the key's position, not the letter printed on it ---------------------
sub("""  window.addEventListener('keydown', function (e) {
    kbmLast = performance.now();
    var k = e.key.toLowerCase();
    keys[k] = true;
    // number keys by position, so Shift (sprint) held down does not turn
    // 1 and 2 into ! and @
    if (e.code === 'Digit1' || e.code === 'Numpad1') k = '1';
    else if (e.code === 'Digit2' || e.code === 'Numpad2') k = '2';""",
"""  // Which key it is by where it sits on the board. A French AZERTY player
  // presses the same square of four keys everyone else does, and Shift no
  // longer turns 1 and 2 into ! and @.
  var CODEKEY = {
    KeyW: 'w', KeyA: 'a', KeyS: 's', KeyD: 'd', KeyQ: 'q', KeyE: 'e', KeyR: 'r', KeyF: 'f',
    KeyG: 'g', KeyH: 'h', KeyV: 'v', KeyZ: 'z', KeyX: 'x', KeyC: 'c', KeyM: 'm', KeyT: 't',
    KeyP: 'p', Digit1: '1', Digit2: '2', Numpad1: '1', Numpad2: '2', Space: ' ',
    Escape: 'escape', Enter: 'enter', NumpadEnter: 'enter', Tab: 'tab',
    ArrowUp: 'arrowup', ArrowDown: 'arrowdown', ArrowLeft: 'arrowleft', ArrowRight: 'arrowright',
    ShiftLeft: 'shift', ShiftRight: 'shift'
  };
  function keyOf(e) { return CODEKEY[e.code] || (e.key || '').toLowerCase(); }
  window.addEventListener('keydown', function (e) {
    kbmLast = performance.now();
    var k = keyOf(e);
    keys[k] = true;""")
sub("""  window.addEventListener('keyup', function (e) { keys[e.key.toLowerCase()] = false; });""",
    """  window.addEventListener('keyup', function (e) { keys[keyOf(e)] = false; });""")

# ---- P pauses as well, so Escape can stay the browser's -------------------------
sub("""      else if (k === 'escape') { if (kp.mapOpen || kp.invOpen) { kp.mapOpen = false; kp.invOpen = false; } else pause(); }
    } else if (k === 'escape' && state === 'paused')""",
"""      else if (k === 'escape' || k === 'p') { if (kp.mapOpen || kp.invOpen) { kp.mapOpen = false; kp.invOpen = false; } else pause(); }
    } else if ((k === 'escape' || k === 'p') && state === 'paused')""")
sub("""      if (k === 'escape') {
        if (settingsOpenFromPause()) $('setBack').click();
        else if (player && (player.mapOpen || player.invOpen)) { player.mapOpen = false; player.invOpen = false; }
        else if (netGuestPaused) resume(); else pause();
      }""",
"""      if (k === 'escape' || k === 'p') {
        if (settingsOpenFromPause()) $('setBack').click();
        else if (player && (player.mapOpen || player.invOpen)) { player.mapOpen = false; player.invOpen = false; }
        else if (netGuestPaused) resume(); else pause();
      }""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

# ---- a proper document, and phone-friendly surfaces -------------------------------
h = io.open(H, encoding='utf-8').read(); ho = h
head = """<title>Dead Angle</title>"""
if head not in h:
    raise SystemExit('HTML TITLE NOT FOUND')
h = h.replace(head, """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="description" content="Dead Angle - a top-down shooter where sound gives you away.">
<title>Dead Angle</title>""", 1)
a = """*{box-sizing:border-box}"""
h = h.replace(a, """*{box-sizing:border-box}
/* phones: no text selection, no double-tap zoom, no rubber-band scroll */
html,body{-webkit-user-select:none;-moz-user-select:none;user-select:none;-webkit-touch-callout:none;-webkit-tap-highlight-color:transparent;overscroll-behavior:none;touch-action:manipulation}""", 1)
# the pane the menus live in keeps clear of a notch on either side
b = """.screen{position:absolute;inset:0;display:flex;align-items:flex-start;justify-content:center;padding:24px 16px;"""
if b not in h:
    raise SystemExit('HTML SCREEN RULE NOT FOUND')
h = h.replace(b, """.screen{position:absolute;inset:0;display:flex;align-items:flex-start;justify-content:center;padding:calc(24px + env(safe-area-inset-top,0px)) calc(16px + env(safe-area-inset-right,0px)) calc(24px + env(safe-area-inset-bottom,0px)) calc(16px + env(safe-area-inset-left,0px));""", 1)
c = """.hud-bot{position:absolute;left:16px;right:16px;"""
h = h.replace(c, """.hud-bot{position:absolute;left:calc(16px + env(safe-area-inset-left,0px));right:calc(16px + env(safe-area-inset-right,0px));""", 1)
assert h != ho
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p72 applied')
