# -*- coding: utf-8 -*-
"""Controller everywhere: direction-true menu navigation on every screen, an
on-screen keyboard for text boxes, pad-answerable invites. No mute key."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- no mute key --------------------------------------------------------------
sub("""      else if (k === 'm') { muted = !muted; feed(muted ? 'sound <b>off</b>' : 'sound <b>on</b>', true); }
      else if (GB[k] !== undefined""", """      else if (GB[k] !== undefined""")
sub("""      if (kp.air) { if (k === 'escape') pause(); if (k === 'm') { muted = !muted; } return; }""",
    """      if (kp.air) { if (k === 'escape') pause(); return; }""")
sub("""      else if (k === 'm') { muted = !muted; feed(muted ? 'sound <b>off</b>' : 'sound <b>on</b>', true); }
      else if (k === 'escape') pause();""", """      else if (k === 'escape') pause();""")

# ---- menu navigation ------------------------------------------------------------
a = s.index("  var uiScr = null, uiIdx = 0, uiRepeat = 0;")
b = s.index("  function screenToWorld(sx, sy) {")
s = s[:a] + r"""  // ---- driving every screen with a pad ---------------------------------
  // Up/down/left/right move to whatever is actually in that direction on
  // screen - down goes to the next row, not the next button along.
  var uiScr = null, uiRepeat = 0;
  function uiScreen() {
    var ids = ['osk', 'account', 'online', 'paused', 'over', 'settings', 'shop', 'menu'];
    for (var i = 0; i < ids.length; i++) {
      var el = $(ids[i]);
      if (el && !el.hidden) return el;
    }
    return null;
  }
  function uiItems(scr) {
    var list = Array.prototype.slice.call(scr.querySelectorAll('button, input, .skincard'));
    // an invite pop-up joins whatever screen is showing
    if (scr.id !== 'osk' && !$('inviteToast').hidden) list = list.concat(Array.prototype.slice.call($('inviteToast').querySelectorAll('button')));
    return list.filter(function (el) { return el.offsetParent !== null && !el.disabled; });
  }
  function uiMove(items, cur, dx, dy) {
    var r = cur.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    var best = null, bestS = 1e9;
    for (var i = 0; i < items.length; i++) {
      var el = items[i];
      if (el === cur) continue;
      var q = el.getBoundingClientRect(), qx = q.left + q.width / 2, qy = q.top + q.height / 2;
      var along, across;
      if (dy) {
        // must sit clearly in the next row, above or below
        if (dy > 0 ? q.top < r.bottom - 4 : q.bottom > r.top + 4) continue;
        along = Math.abs(qy - cy); across = Math.abs(qx - cx);
      } else {
        if (dx > 0 ? qx <= cx + 2 : qx >= cx - 2) continue;
        if (Math.abs(qy - cy) > Math.max(r.height, q.height)) continue;    // same row only
        along = Math.abs(qx - cx); across = Math.abs(qy - cy);
      }
      var sc = along + across * 2.2;
      if (sc < bestS) { bestS = sc; best = el; }
    }
    return best;
  }
  function uiFocus(el) {
    if (!el) return;
    el.focus({ preventScroll: true });
    if (el.scrollIntoView) el.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }
  function uiBack() {
    if (!$('osk').hidden) { oskKey('BACK'); return; }
    if (!$('inviteToast').hidden && document.activeElement && $('inviteToast').contains(document.activeElement)) { answerInvite(false); return; }
    if (!$('account').hidden) $('acctBack').click();
    else if (!$('online').hidden) $('netBack').click();
    else if (!$('paused').hidden) resume();
    else if (!$('shop').hidden) $('shopBack').click();
    else if (!$('settings').hidden) $('setBack').click();
    else if (!elOver.hidden) $('homeBtn').click();
  }
  function uiPad(dt) {
    pollPad();
    if (!pad) return;
    var scr = uiScreen();
    if (!scr) { uiScr = null; return; }
    var items = uiItems(scr);
    if (!items.length) return;
    var cur = document.activeElement;
    if (scr !== uiScr || items.indexOf(cur) < 0) {
      if (scr !== uiScr) { uiScr = scr; cur = items[0]; uiFocus(cur); }
      else { cur = items[0]; }
    }

    if (uiRepeat > 0) uiRepeat -= dt;
    var ay = padAxis(1), ax = padAxis(0);
    var dy = (padHit(13) ? 1 : 0) - (padHit(12) ? 1 : 0);
    var dx = (padHit(15) ? 1 : 0) - (padHit(14) ? 1 : 0);
    if (!dy && !dx && uiRepeat <= 0) {                 // stick, with a repeat delay
      if (ay > 0.6) dy = 1; else if (ay < -0.6) dy = -1;
      else if (ax > 0.6) dx = 1; else if (ax < -0.6) dx = -1;
      if (dy || dx) uiRepeat = 0.2;
    }

    if (dx && cur && cur.type === 'range') {
      var stepv = parseInt(cur.step || 1, 10) * 3 * dx;
      cur.value = clamp(parseInt(cur.value, 10) + stepv, parseInt(cur.min, 10), parseInt(cur.max, 10));
      cur.dispatchEvent(new Event('input'));
      dx = 0;
    }
    if (dy || dx) uiFocus(uiMove(items, cur, dx, dy) || cur);
    if (padHit(0)) {
      var it = document.activeElement && items.indexOf(document.activeElement) >= 0 ? document.activeElement : cur;
      if (it && it.tagName === 'INPUT' && it.type !== 'range') openOsk(it);
      else if (it && it.click) it.click();
    }
    if (padHit(1)) uiBack();
    if (padHit(2) && !$('osk').hidden) oskKey('BACK');       // X deletes a letter
    if (padHit(3) && !$('osk').hidden) oskKey('DONE');       // Y finishes typing
    if (padHit(9)) {
      if (!$('osk').hidden) oskKey('DONE');
      else if (!$('paused').hidden) resume();
    }
  }

  // ---- on-screen keyboard, for typing names and codes with a pad --------
  var oskTarget = null, oskUpper = true;
  var OSK_ROWS = ['1234567890', 'QWERTYUIOP', 'ASDFGHJKL_', 'ZXCVBNM'];
  function buildOsk() {
    var keysEl = $('oskKeys');
    keysEl.innerHTML = '';
    OSK_ROWS.forEach(function (row) {
      var r = document.createElement('div');
      r.className = 'oskrow';
      row.split('').forEach(function (ch) {
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'oskk';
        b.setAttribute('data-k', ch);
        b.textContent = ch;
        b.addEventListener('click', function () { oskKey(this.getAttribute('data-k')); });
        r.appendChild(b);
      });
      keysEl.appendChild(r);
    });
    var r2 = document.createElement('div');
    r2.className = 'oskrow';
    [['SHIFT', 'abc'], ['BACK', '⌫ DELETE'], ['DONE', 'DONE']].forEach(function (p) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'oskk wide' + (p[0] === 'DONE' ? ' done' : '');
      b.setAttribute('data-k', p[0]);
      b.textContent = p[1];
      b.addEventListener('click', function () { oskKey(this.getAttribute('data-k')); });
      r2.appendChild(b);
    });
    keysEl.appendChild(r2);
  }
  function oskShow() {
    var t = oskTarget;
    var v = t ? t.value : '';
    $('oskText').textContent = (t && t.type === 'password' ? v.replace(/./g, '•') : v) || ' ';
    $('oskLabel').textContent = t ? (t.getAttribute('aria-label') || t.placeholder || '') : '';
    Array.prototype.forEach.call($('oskKeys').querySelectorAll('.oskk'), function (b) {
      var k = b.getAttribute('data-k');
      if (k.length === 1 && /[A-Z]/.test(k)) b.textContent = oskUpper ? k : k.toLowerCase();
      if (k === 'SHIFT') b.textContent = oskUpper ? 'abc' : 'ABC';
    });
  }
  function openOsk(input) {
    oskTarget = input;
    // codes and names read naturally in capitals; passwords start lower case
    oskUpper = input.type !== 'password';
    if (!$('oskKeys').children.length) buildOsk();
    $('osk').hidden = false;
    oskShow();
    uiScr = null;
  }
  function oskKey(k) {
    var t = oskTarget;
    if (!t) { $('osk').hidden = true; return; }
    if (k === 'DONE') {
      $('osk').hidden = true;
      uiScr = null;
      uiFocus(t);
      oskTarget = null;
      return;
    }
    if (k === 'SHIFT') { oskUpper = !oskUpper; oskShow(); return; }
    if (k === 'BACK') {
      if (!t.value.length) { oskKey('DONE'); return; }
      t.value = t.value.slice(0, -1);
    } else {
      var max = parseInt(t.getAttribute('maxlength') || '64', 10);
      if (t.value.length < max) t.value += /[A-Z]/.test(k) && !oskUpper ? k.toLowerCase() : k;
    }
    oskShow();
  }

""" + s[b:]

# the guest's pause menu is driven while its match keeps running
sub("""    if (state === 'play') {
      if (netGuest) guestTick(Math.max(dt, 0.0001));
      else update(Math.max(dt, 0.0001));
    }
    else uiPad(dt);""",
"""    if (state === 'play') {
      if (netGuest) guestTick(Math.max(dt, 0.0001));
      else update(Math.max(dt, 0.0001));
      if (netGuest && netGuestPaused) uiPad(dt);
    }
    else uiPad(dt);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

# ================================================================ html ======
h = io.open(H, encoding='utf-8').read()
a = """  <div class="toast" id="inviteToast" hidden>"""
if a not in h:
    raise SystemExit('HTML PATTERN NOT FOUND')
h = h.replace(a, """  <div class="screen osk" id="osk" hidden>
    <div class="panel">
      <div class="osklabel" id="oskLabel"></div>
      <div class="osktext" id="oskText"> </div>
      <div class="oskkeys" id="oskKeys"></div>
      <p class="modedesc">A types · X deletes · Y or START finishes · B deletes, then closes</p>
    </div>
  </div>

""" + a, 1)
a = """.ptitle{"""
h = h.replace(a, """.osk{z-index:30;background:rgba(10,9,7,.94)}
.osklabel{font-family:var(--font-x);font-size:12px;letter-spacing:.24em;color:var(--gold);text-transform:uppercase}
.osktext{min-width:260px;padding:12px 16px;font-family:var(--font-m);font-size:18px;font-weight:600;letter-spacing:.16em;background:var(--paper);color:var(--out);border:3px solid var(--out);border-radius:4px;min-height:1.6em}
.oskkeys{display:flex;flex-direction:column;align-items:center;gap:6px}
.oskrow{display:flex;gap:6px;justify-content:center}
.oskk{appearance:none;min-width:38px;height:40px;padding:0 8px;font-family:var(--font-m);font-size:14px;font-weight:600;background:var(--navy);color:var(--paper);border:2px solid var(--out);border-radius:4px;cursor:pointer}
.oskk.wide{min-width:96px;font-size:12px;letter-spacing:.12em}
.oskk.done{background:var(--gold);color:var(--out)}
.oskk:focus{outline:3px solid var(--gold);outline-offset:1px}
@media (max-width:480px){.oskk{min-width:28px;height:36px;padding:0 4px;font-size:12px}.oskrow{gap:4px}}
""" + a, 1)
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p52 applied')
