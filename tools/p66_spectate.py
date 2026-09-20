# -*- coding: utf-8 -*-
"""Once you are out, you watch whoever is left on your side."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- who you are watching ---------------------------------------------------------
sub("""  function renderKillcam(kc) {""",
"""  // ---- watching the rest of your side ---------------------------------------
  function specMates(e) {
    var out = [];
    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (!a || a === e || !a.alive || a.hidden || a.team !== e.team) continue;
      out.push(a);
    }
    return out;
  }
  function specCycle(e, d) {
    var m = specMates(e);
    if (!m.length) { e.spec = null; return; }
    var at = m.indexOf(e.spec);
    e.spec = m[((at < 0 ? 0 : at + d) + m.length) % m.length];
    if (netGuest && e === player) netSend({ t: 'sp', id: e.spec.id });
  }
  // keep the view on someone who is still standing
  function specTick() {
    for (var i = 0; i < locals.length; i++) {
      var L = locals[i];
      if (L.alive || state !== 'play' || L.kc) { if (L.alive) L.spec = null; continue; }
      if (!L.spec || !L.spec.alive || L.spec.team !== L.team) {
        var m = specMates(L);
        L.spec = m.length ? m[0] : null;
        if (netGuest && L === player) netSend({ t: 'sp', id: L.spec ? L.spec.id : -1 });
      }
    }
  }
  function renderSpectate(t) {
    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
    ctx.save();
    var bar = Math.round(ch * 0.07);
    ctx.fillStyle = '#05070b';
    ctx.fillRect(0, 0, cw, bar); ctx.fillRect(0, ch - bar, cw, bar);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '500 11px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(241,231,208,.75)';
    ctx.fillText('SPECTATING', cw / 2, bar + 20);
    ctx.font = '400 24px "Russo One", "Chakra Petch", sans-serif';
    ctx.lineJoin = 'round'; ctx.lineWidth = 6; ctx.strokeStyle = '#0d0f12';
    ctx.strokeText(t.name, cw / 2, bar + 46);
    ctx.fillStyle = '#7ce7d8';
    ctx.fillText(t.name, cw / 2, bar + 46);
    ctx.font = '600 12px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#f1e7d0';
    ctx.fillText(Math.max(0, Math.round(t.hp)) + ' HP  \\u00b7  ' + (t.kills || 0) + ' KILLS', cw / 2, bar + 70);
    ctx.font = '500 11px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(241,231,208,.7)';
    ctx.fillText(usingPad(t) || usingPad(player) ? 'LB / RB SWITCHES' : 'A / D SWITCHES', cw / 2, ch - bar - 20);
    ctx.restore();
  }

  function renderKillcam(kc) {""")

# ---- the camera stays with them ----------------------------------------------------
sub("""      if (L.kc) {
        var kl = 1 - Math.pow(0.015, dt);
        lc.x += (L.kc.k.x - lc.x) * kl; lc.y += (L.kc.k.y - lc.y) * kl;
        continue;
      }""",
"""      if (L.kc) {
        var kl = 1 - Math.pow(0.015, dt);
        lc.x += (L.kc.k.x - lc.x) * kl; lc.y += (L.kc.k.y - lc.y) * kl;
        continue;
      }
      if (!L.alive && L.spec && L.spec.alive) {
        var sl = 1 - Math.pow(0.02, dt);
        lc.x += (L.spec.x - lc.x) * sl; lc.y += (L.spec.y - lc.y) * sl;
        continue;
      }""")
sub("""    pingTick(dt);
    if (mode === 'tut') tutTick(dt);""",
"""    pingTick(dt);
    specTick();
    if (mode === 'tut') tutTick(dt);""")

# ---- switching ----------------------------------------------------------------------
sub("""    if (!e.alive) { if (I.pad && I.hit(9)) pause(); return; }""",
"""    if (!e.alive) {
      if (I.pad && I.hit(PAD.pause)) pause();
      if (e.spec && I.pad) {
        if (I.hit(PAD.swapL)) specCycle(e, -1);
        if (I.hit(PAD.swapR)) specCycle(e, 1);
      }
      return;
    }""")
sub("""    if (state === 'play') {
      var kp = kbPlayer();
      if (kp.air === 'plane' && (k === 'e' || k === ' ')) kp.jumpReq = true;""",
"""    if (state === 'play') {
      var kp = kbPlayer();
      if (!kp.alive && kp.spec && (k === 'a' || k === 'd')) { specCycle(kp, k === 'a' ? -1 : 1); return; }
      if (kp.air === 'plane' && (k === 'e' || k === ' ')) kp.jumpReq = true;""")

# ---- draw from their eyes -------------------------------------------------------------
sub("""      renderScene();
      return;
    }""",
"""      if (!player.alive && player.spec && player.spec.alive) {
        var meS = player, spS = player.spec;
        player = spS; noOverlay = true;
        try { renderScene(); } finally { player = meS; noOverlay = false; }
        renderSpectate(spS);
        return;
      }
      renderScene();
      return;
    }""")
sub("""      if (L.kc) {
        // this player's own kill cam, in their half
        var kcS = L.kc;
        player = kcS.k; noOverlay = true;
        try { renderScene(); } finally { player = L; noOverlay = false; }
        renderKillcam(kcS);
      } else renderScene();""",
"""      if (L.kc) {
        // this player's own kill cam, in their half
        var kcS = L.kc;
        player = kcS.k; noOverlay = true;
        try { renderScene(); } finally { player = L; noOverlay = false; }
        renderKillcam(kcS);
      } else if (!L.alive && L.spec && L.spec.alive) {
        player = L.spec; noOverlay = true;
        try { renderScene(); } finally { player = L; noOverlay = false; }
        renderSpectate(L.spec);
      } else renderScene();""")

# ---- online: the host sends the world around whoever you are watching ---------------
sub("""  function nearGuest(g, x, y) {
    var ge = g.ent;""",
"""  // A dead guest watches a teammate, so their slice of the world follows that
  // teammate instead of their own body.
  function guestEye(g) {
    var e = g.ent;
    if (e && !e.alive && g.spec >= 0) {
      var t = ents[g.spec];
      if (t && t.alive && t.team === e.team) return t;
    }
    return e;
  }
  function nearGuest(g, x, y) {
    var ge = guestEye(g);""")
sub("""    } else if (m.t === 'dr') {""",
"""    } else if (m.t === 'sp') {
      g.spec = m.id | 0;
    } else if (m.t === 'dr') {""")
# the guest keeps its own watch going
sub("""    killcamTick(dt);
    if (player.kc) {
      var gk = 1 - Math.pow(0.015, dt);
      cam.x += (player.kc.k.x - cam.x) * gk; cam.y += (player.kc.k.y - cam.y) * gk;
    } else {""",
"""    killcamTick(dt);
    specTick();
    if (player.kc) {
      var gk = 1 - Math.pow(0.015, dt);
      cam.x += (player.kc.k.x - cam.x) * gk; cam.y += (player.kc.k.y - cam.y) * gk;
    } else if (!player.alive && player.spec && player.spec.alive) {
      var gs = 1 - Math.pow(0.02, dt);
      cam.x += (player.spec.x - cam.x) * gs; cam.y += (player.spec.y - cam.y) * gs;
    } else {""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p66 applied')
