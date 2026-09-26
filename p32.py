# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ==================================================== controller presence ====
sub("""  var pad = null, padPrev = {}, padSeen = false;
  function pollPad() {
    var list = navigator.getGamepads ? navigator.getGamepads() : null;
    pad = null;
    if (!list) return;
    for (var i = 0; i < list.length; i++) {
      if (list[i] && list[i].connected) { pad = list[i]; padSeen = true; break; }
    }
  }""",
"""  var pad = null, padPrev = {}, padSeen = false, padLast = -1e9;
  function pollPad() {
    var list = navigator.getGamepads ? navigator.getGamepads() : null;
    pad = null;
    if (!list) return;
    for (var i = 0; i < list.length; i++) {
      if (list[i] && list[i].connected) { pad = list[i]; padSeen = true; break; }
    }
    if (!pad) return;
    // note when the stick or a button was last touched, so the prompts can
    // switch between keyboard and controller on their own
    var busy = false, j;
    for (j = 0; j < pad.buttons.length; j++) if (pad.buttons[j] && pad.buttons[j].pressed) { busy = true; break; }
    if (!busy) for (j = 0; j < pad.axes.length; j++) if (Math.abs(pad.axes[j]) > 0.45) { busy = true; break; }
    if (busy) padLast = performance.now();
  }
  function padActive() { return !!pad && (performance.now() - padLast) < 10000; }
  // Prompts read as whatever you are actually holding.
  function promptKey(keyLabel, padLabel) { return padActive() ? padLabel : keyLabel; }""")

# ==================================================== menus on a controller ==
sub("""  function screenToWorld(sx, sy) {""",
"""  // ---- driving the screens with a pad ------------------------------------
  var uiScr = null, uiIdx = 0, uiRepeat = 0;
  function uiScreen() {
    var ids = ['paused', 'over', 'settings', 'shop', 'menu'];
    for (var i = 0; i < ids.length; i++) {
      var el = $(ids[i]);
      if (el && !el.hidden) return el;
    }
    return null;
  }
  function uiPad(dt) {
    pollPad();
    if (!pad) return;
    var scr = uiScreen();
    if (!scr) { uiScr = null; return; }
    var items = Array.prototype.slice.call(scr.querySelectorAll('button, input[type=range]'));
    if (!items.length) return;
    if (scr !== uiScr) { uiScr = scr; uiIdx = 0; items[0].focus(); }
    if (uiIdx >= items.length) uiIdx = 0;

    if (uiRepeat > 0) uiRepeat -= dt;
    var ay = padAxis(1), ax = padAxis(0);
    var dy = (padHit(13) ? 1 : 0) - (padHit(12) ? 1 : 0);
    var dx = (padHit(15) ? 1 : 0) - (padHit(14) ? 1 : 0);
    if (!dy && !dx && uiRepeat <= 0) {                 // stick, with a repeat delay
      if (ay > 0.6) dy = 1; else if (ay < -0.6) dy = -1;
      else if (ax > 0.6) dx = 1; else if (ax < -0.6) dx = -1;
      if (dy || dx) uiRepeat = 0.22;
    }

    var cur = items[uiIdx];
    if (dx && cur && cur.type === 'range') {
      var stepv = parseInt(cur.step || 1, 10) * 3 * dx;
      cur.value = clamp(parseInt(cur.value, 10) + stepv, parseInt(cur.min, 10), parseInt(cur.max, 10));
      cur.dispatchEvent(new Event('input'));
      dx = 0;
    }
    if (dy || dx) {
      uiIdx = (uiIdx + dy + dx + items.length) % items.length;
      items[uiIdx].focus();
    }
    if (padHit(0)) { var it = items[uiIdx]; if (it && it.click) it.click(); }
    if (padHit(1)) {
      if (!$('paused').hidden) resume();
      else if (!$('shop').hidden) $('shopBack').click();
      else if (!$('settings').hidden) $('setBack').click();
      else if (!elOver.hidden) $('homeBtn').click();
    }
    if (padHit(9) && !$('paused').hidden) resume();
  }

  function screenToWorld(sx, sy) {""")

sub("""    var dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (state === 'play') update(Math.max(dt, 0.0001));""",
"""    var dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (state === 'play') update(Math.max(dt, 0.0001));
    else uiPad(dt);""")

# ==================================================== downed on a pad ========
sub("""    var e = player;
    if (!e.alive) return;
    if (e.down) { e._spd = 0; promptItem = null; return; }""",
"""    var e = player;
    if (!e.alive) return;
    if (e.down) {
      e._spd = 0; promptItem = null;
      pollPad();
      if (padHit(1)) { e.hp = 0; kill(e, -1); }        // B gives up
      return;
    }""")

sub("""    pollPad();
    var ix = 0, iy = 0;""",
"""    var ix = 0, iy = 0;""")

sub("""  function updatePlayer(dt) {
    var e = player;""",
"""  function updatePlayer(dt) {
    pollPad();
    var e = player;""")

# ==================================================== prompts ================
sub("""    ctx.fillStyle = '#7ce7d8';
    ctx.textBaseline = 'middle';
    ctx.fillText('E', bx + 14, by + boxH / 2 + 1);""",
"""    ctx.fillStyle = '#7ce7d8';
    ctx.textBaseline = 'middle';
    ctx.fillText(promptKey('E', 'A'), bx + 14, by + boxH / 2 + 1);""")

sub("""      : 'DOWNED  \\u00b7  ' + Math.ceil(player.downT) + 's  \\u00b7  X TO GIVE UP';""",
    """      : 'DOWNED  \\u00b7  ' + Math.ceil(player.downT) + 's  \\u00b7  ' + promptKey('X', 'B') + ' TO GIVE UP';""")

# ==================================================== the punch =============
sub("""    var reach = 0;
    if (e.throwT > 0) {""",
"""    // a jab: quick out and back, translation only
    var jab = e.swingT > 0 ? Math.sin((1 - e.swingT / 0.18) * Math.PI) * 32 : 0;
    var reach = 0;
    if (e.throwT > 0) {""")

sub("""    limb(4, -CHAR.armX + stride * 2 - reach * 0.12, CHAR.armY - stride * 4 + kick + reach * 0.18, CHAR.armRot + stride * 0.09);
    limb(0, stride * 2 + reach * 0.10, CHAR.torsoY, stride * 0.03);                  // torso leans into it""",
"""    limb(4, -CHAR.armX + stride * 2 - reach * 0.12, CHAR.armY - stride * 4 + kick + reach * 0.18 + jab * 0.25, CHAR.armRot + stride * 0.09);
    limb(0, stride * 2 + reach * 0.10, CHAR.torsoY - jab * 0.12, stride * 0.03);     // torso leans into it""")

sub("""    limb(3, CHAR.armX + stride * 2 + reach * 0.16, CHAR.armY + stride * 4 + kick - reach, CHAR.armRot - stride * 0.09);""",
    """    limb(3, CHAR.armX + stride * 2 + reach * 0.16 - jab * 0.30, CHAR.armY + stride * 4 + kick - reach - jab, CHAR.armRot - stride * 0.09);""")

# ==================================================== controller reticle =====
sub("""  function renderPrompt() {""",
"""  // On a pad there is no mouse to show where you are pointing, so put a dot
  // out in front - at half a screen, or on the first wall in the way.
  var cursorHidden = null;
  function renderReticle() {
    var on = padActive();
    if (cursorHidden !== on) {
      cursorHidden = on;
      canvas.style.cursor = on ? 'none' : 'crosshair';
    }
    if (!on || !player.alive || player.down) return;
    var maxD = Math.min(cw, ch) * 0.5 / zoom;
    var cx3 = Math.cos(player.ang), cy3 = Math.sin(player.ang);
    var d = maxD, step = TILE * 0.35;
    for (var t = step; t < maxD; t += step) {
      if (wallAt(player.x + cx3 * t, player.y + cy3 * t)) { d = t; break; }
    }
    var sx3 = (player.x + cx3 * d - cam.x) * zoom + cw / 2;
    var sy3 = (player.y + cy3 * d - cam.y) * zoom + ch / 2;
    ctx.fillStyle = 'rgba(124,231,216,.9)';
    ctx.beginPath(); ctx.arc(sx3, sy3, 2.6, 0, 6.2832); ctx.fill();
    ctx.strokeStyle = 'rgba(124,231,216,.32)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(sx3, sy3, 7.5, 0, 6.2832); ctx.stroke();
  }

  function renderPrompt() {""")

sub("""    renderDowned();
    renderPrompt();""",
"""    renderReticle();
    renderDowned();
    renderPrompt();""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p32 applied')
