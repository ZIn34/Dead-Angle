# -*- coding: utf-8 -*-
"""TAB opens your kit, and anything in it can go on the floor."""
import io, sys
G = sys.argv[1]
H = sys.argv[2]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- putting things down --------------------------------------------------------
sub("""  function swapSlot(n, e) {""",
"""  // Anything that is not a gun: stims, frags, smoke, spare rounds.
  function dropItem(e, kind) {
    if (!e || !e.alive || e.down || e.air) return false;
    var type = null, n = 1;
    if (kind === 'ammo') {
      if (!(e.reserve > 0) || e.reserve >= 9000) return false;
      n = Math.min(30, e.reserve); e.reserve -= n; type = 'ammo';
    } else if (kind === 'med' && e.meds > 0) { e.meds--; type = 'med'; }
    else if (kind === 'nade' && e.nades > 0) { e.nades--; type = 'nade'; }
    else if (kind === 'smoke' && e.smokes > 0) { e.smokes--; type = 'smoke'; }
    if (!type) return false;
    loot.push({
      x: e.x + Math.cos(e.ang) * 20, y: e.y + Math.sin(e.ang) * 20, type: type, key: null,
      spin: rr(0, 6.2832), ammo: 0, n: n, seen: true
    });
    audioEmit(e.x, e.y, PICK_SND, e.id);
    return true;
  }
  // One place both a gun and a pocket item go through, so a guest can ask the
  // host for the same thing a local player just does.
  function dropKind(e, kind) {
    if (!e) return;
    if (netGuest && e === player) { netSend({ t: 'dr', k: kind }); return; }
    if (kind === 'w0' || kind === 'w1') {
      var want = kind === 'w1' ? 1 : 0;
      if (!e.slots[want]) return;
      if (e.slot !== want) swapSlot(want, e);
      dropWeapon(e);
      return;
    }
    dropItem(e, kind);
  }

  function swapSlot(n, e) {""")

# ---- the panel -------------------------------------------------------------------
sub("""  var mapRect = null;""",
"""  // ---- your kit, laid out, with anything droppable ---------------------------
  function invRows(e) {
    var s0 = e.slots[0], s1 = e.slots[1];
    return [
      { kind: 'w0', label: 'PRIMARY', val: s0 ? WEAPONS[s0.key].name + '  ' + s0.ammo : '\\u2014', has: !!s0 },
      { kind: 'w1', label: 'SECONDARY', val: s1 ? WEAPONS[s1.key].name + '  ' + s1.ammo : '\\u2014', has: !!s1 },
      { kind: 'ammo', label: 'ROUNDS', val: e.reserve >= 9000 ? 'PLENTY' : String(e.reserve | 0), has: e.reserve > 0 && e.reserve < 9000 },
      { kind: 'med', label: 'STIMS', val: String(e.meds | 0), has: e.meds > 0 },
      { kind: 'nade', label: 'FRAGS', val: String(e.nades | 0), has: e.nades > 0 },
      { kind: 'smoke', label: 'SMOKE', val: String(e.smokes | 0), has: e.smokes > 0 }
    ];
  }
  function invMove(e, d) {
    var rows = invRows(e);
    e.invSel = ((e.invSel || 0) + d + rows.length) % rows.length;
  }
  function invDrop(e) {
    var rows = invRows(e), r = rows[e.invSel || 0];
    if (r && r.has) dropKind(e, r.kind);
  }
  var invRect = null;
  function drawInventory() {
    var e = player, rows = invRows(e);
    var W = Math.min(340, cw - 48), RH = 34, H = RH * rows.length + 74;
    var bx = Math.round((cw - W) / 2), by = Math.round((ch - H) / 2);
    ctx.save();
    ctx.fillStyle = 'rgba(4,6,10,.72)'; ctx.fillRect(0, 0, cw, ch);
    ctx.fillStyle = 'rgba(8,12,18,.94)'; ctx.fillRect(bx, by, W, H);
    ctx.strokeStyle = 'rgba(242,189,29,.5)'; ctx.lineWidth = 1.5;
    ctx.strokeRect(bx + .75, by + .75, W - 1.5, H - 1.5);
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';
    ctx.font = '400 15px "Russo One", "Chakra Petch", sans-serif';
    ctx.fillStyle = '#f1e7d0';
    ctx.fillText('KIT', bx + W / 2, by + 24);
    var sel = e.invSel || 0;
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i], ry = by + 44 + i * RH;
      if (i === sel) {
        ctx.fillStyle = 'rgba(242,189,29,.14)';
        ctx.fillRect(bx + 8, ry, W - 16, RH - 4);
        ctx.strokeStyle = 'rgba(242,189,29,.75)'; ctx.lineWidth = 1;
        ctx.strokeRect(bx + 8.5, ry + .5, W - 17, RH - 5);
      }
      ctx.font = '600 11px "IBM Plex Mono", monospace';
      ctx.textAlign = 'left';
      ctx.fillStyle = r.has ? 'rgba(241,231,208,.8)' : 'rgba(146,170,196,.45)';
      ctx.fillText(r.label, bx + 20, ry + (RH - 4) / 2);
      ctx.textAlign = 'right';
      ctx.fillStyle = r.has ? '#f1e7d0' : 'rgba(146,170,196,.45)';
      ctx.fillText(r.val, bx + W - 20, ry + (RH - 4) / 2);
    }
    ctx.textAlign = 'center';
    ctx.font = '600 10px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(241,231,208,.7)';
    ctx.fillText(usingPad(e)
      ? 'LEFT STICK PICKS  \\u00b7  B DROPS  \\u00b7  L3 CLOSES'
      : 'ARROWS PICK  \\u00b7  Z DROPS  \\u00b7  TAB CLOSES', bx + W / 2, by + H - 18);
    ctx.restore();
    if (e === kbPlayer()) invRect = { x: VX + bx, y: VY + by + 44, w: W, rh: RH, n: rows.length };
  }
  // a click straight on a row picks it and puts it down
  function invClick(sx, sy) {
    var r = invRect, kp = kbPlayer();
    if (!r || !kp.invOpen || state !== 'play') return false;
    if (sx >= r.x && sx <= r.x + r.w && sy >= r.y && sy <= r.y + r.rh * r.n) {
      kp.invSel = Math.floor((sy - r.y) / r.rh);
      invDrop(kp);
    }
    return true;                       // the panel swallows the click either way
  }

  var mapRect = null;""")

# ---- keys -------------------------------------------------------------------------
sub("""      else if (k === 'm') { kp.mapOpen = !kp.mapOpen; kp.mapCur = null; }""",
"""      else if (k === 'm') { kp.mapOpen = !kp.mapOpen; kp.mapCur = null; }
      else if (k === 'tab') { kp.invOpen = !kp.invOpen; kp.invSel = 0; }
      else if (kp.invOpen && (k === 'arrowup' || k === 'arrowdown')) invMove(kp, k === 'arrowup' ? -1 : 1);""")
sub("""      else if (k === 'z') dropWeapon(kp);""",
    """      else if (k === 'z') { if (kp.invOpen) invDrop(kp); else dropWeapon(kp); }""")
sub("""      else if (k === 'escape') { if (kp.mapOpen) kp.mapOpen = false; else pause(); }""",
"""      else if (k === 'escape') { if (kp.mapOpen || kp.invOpen) { kp.mapOpen = false; kp.invOpen = false; } else pause(); }""")
sub("""    if (['w', 'a', 's', 'd', ' '].indexOf(k) >= 0) e.preventDefault();
  });
  window.addEventListener('keyup'""",
"""    if (['w', 'a', 's', 'd', ' ', 'tab', 'arrowup', 'arrowdown'].indexOf(k) >= 0) e.preventDefault();
  });
  window.addEventListener('keyup'""")
# the same keys for someone playing on someone else's host
sub("""      if (k === 'escape') { if (settingsOpenFromPause()) $('setBack').click(); else if (netGuestPaused) resume(); else pause(); }
      else if (GB[k] !== undefined && !netGuestPaused && !e.repeat) guestHits |= 1 << GB[k];
      if (['w', 'a', 's', 'd', ' '].indexOf(k) >= 0) e.preventDefault();""",
"""      if (k === 'escape') {
        if (settingsOpenFromPause()) $('setBack').click();
        else if (player && (player.mapOpen || player.invOpen)) { player.mapOpen = false; player.invOpen = false; }
        else if (netGuestPaused) resume(); else pause();
      }
      else if (k === 'm' && player) { player.mapOpen = !player.mapOpen; player.mapCur = null; }
      else if (k === 'tab' && player) { player.invOpen = !player.invOpen; player.invSel = 0; }
      else if (k === 'c' && player) pingAt(player, mouse.wx, mouse.wy);
      else if (player && player.invOpen && (k === 'arrowup' || k === 'arrowdown')) invMove(player, k === 'arrowup' ? -1 : 1);
      else if (player && player.invOpen && k === 'z') invDrop(player);
      else if (GB[k] !== undefined && !netGuestPaused && !e.repeat) guestHits |= 1 << GB[k];
      if (['w', 'a', 's', 'd', ' ', 'tab', 'arrowup', 'arrowdown'].indexOf(k) >= 0) e.preventDefault();""")
# ENTER belongs to the chat, but not while the kit is open
sub("""    if (netRole && (state === 'play') && (k === 't' || k === 'enter') && $('igChat').hidden)""",
    """    if (netRole && (state === 'play') && (k === 't' || k === 'enter') && $('igChat').hidden && !(player && player.invOpen))""")

# ---- pad --------------------------------------------------------------------------
sub("""      if (I.hit(PAD.map)) { e.mapOpen = !e.mapOpen; e.mapCur = null; }""",
"""      if (I.hit(PAD.map)) { e.mapOpen = !e.mapOpen; e.mapCur = null; }
      if (I.hit(PAD.inv)) { e.invOpen = !e.invOpen; e.invSel = 0; }""")
sub("""    if (e.mapOpen && I.pad && I.padOn) {""",
"""    if (e.invOpen && I.pad && I.padOn) {
      // the stick walks the list, so you are not also walking into a wall
      var iy = I.ax(1);
      e.invT = Math.max(0, (e.invT || 0) - dt);
      if (Math.abs(iy) > 0.55 && e.invT <= 0) { invMove(e, iy > 0 ? 1 : -1); e.invT = 0.18; }
      if (I.hit(PAD.drop)) invDrop(e);
      e._spd = 0; e.moving = false; e.prompt = null;
      if (e === player) promptItem = null;
      return;
    }
    if (e.mapOpen && I.pad && I.padOn) {""")
# a guest asks the host to put it down
sub("""    } else if (m.t === 'pg') {""",
"""    } else if (m.t === 'dr') {
      dropKind(g.ent, String(m.k || ''));
    } else if (m.t === 'pg') {""")

# ---- draw ---------------------------------------------------------------------------
sub("""    if (player.mapOpen && !noOverlay) drawBigMap();
    else if (SET.minimap && !splitVs()) drawMinimap();""",
"""    if (player.mapOpen && !noOverlay) drawBigMap();
    else if (SET.minimap && !splitVs()) drawMinimap();
    if (player.invOpen && !noOverlay) drawInventory();""")
sub("""      if (!mapClick(ev.clientX - r2.left, ev.clientY - r2.top)) mouse.down = true;""",
"""      var cx3 = ev.clientX - r2.left, cy3 = ev.clientY - r2.top;
      if (!invClick(cx3, cy3) && !mapClick(cx3, cy3)) mouse.down = true;""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)

h = io.open(H, encoding='utf-8').read(); ho = h
a = """<span><kbd>Z</kbd> drop weapon</span>"""
if a not in h:
    raise SystemExit('HTML PATTERN NOT FOUND')
h = h.replace(a, a + """<span><kbd>TAB</kbd> kit</span><span><kbd>M</kbd> map</span><span><kbd>C</kbd> mark</span>""", 1)
assert h != ho
io.open(H, 'w', encoding='utf-8', newline='').write(h)
print('p65 applied')
