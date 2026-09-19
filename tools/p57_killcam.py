# -*- coding: utf-8 -*-
"""Kill cam: when you die, see who got you, through their eyes."""
import io, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- start it when you are killed by someone -------------------------------
sub("""    var kn = killer ? killer.name : 'THE ZONE';""",
"""    var kn = killer ? killer.name : 'THE ZONE';
    // you were killed by someone: the camera goes to them for a moment
    if (e === player && killer && killer !== e && !splitOn && !netGuest && mode !== 'tut') {
      var kw = curW(killer);
      killcam = { k: killer, victim: e, t: 0, dur: 3.2, after: null,
                  gun: kw ? kw.name : 'BARE HANDS', hp: Math.max(0, Math.round(killer.hp)), d: Math.round(dist(e, killer)) };
    }""")
# battle royale: the results wait until the kill cam has played
sub("""    if (e.local && !anyLocalAlive()) {
      finish(false, killer && killer !== e""", """    if (e.local && !anyLocalAlive()) {
      finishAfterCam(e, false, killer && killer !== e""")
sub("""  function finish(won, msg, place) {""",
"""  var killcam = null;
  function finishAfterCam(e, won, msg, place) {
    if (killcam && killcam.victim === e) { killcam.after = [won, msg, place]; return; }
    finish(won, msg, place);
  }
  function killcamTick(dt) {
    if (!killcam) return;
    killcam.t += dt;
    // over when it has run, or the moment you are back on your feet
    var done = killcam.t >= killcam.dur || (player.alive && killcam.t > 0.4);
    if (!killcam.k.alive && killcam.t > 1.4) done = true;              // they died too
    if (!done) return;
    var aft = killcam.after;
    killcam = null;
    if (aft && state === 'play') finish(aft[0], aft[1], aft[2]);
  }
  function finish(won, msg, place) {""")
# a new match or going home clears it
sub("""    result = null; overCause = ''; lastWinner = null;""", """    result = null; overCause = ''; lastWinner = null; killcam = null;""")
sub("""  function goHome() {
    cgGame('gameplayStop');""", """  function goHome() {
    cgGame('gameplayStop');
    killcam = null;""")
# tick it with the match
sub("""    if (mode === 'tut') tutTick(dt);""", """    if (mode === 'tut') tutTick(dt);
    killcamTick(dt);""")

# ---- camera: glide over to the killer --------------------------------------------
sub("""      var L = locals[li], lc = L.cam || cam;""",
"""      var L = locals[li], lc = L.cam || cam;
      if (killcam && L === player) {
        var kl = 1 - Math.pow(0.015, dt);
        lc.x += (killcam.k.x - lc.x) * kl; lc.y += (killcam.k.y - lc.y) * kl;
        continue;
      }""")

# ---- drawing: their view, a marker on them, the banner ----------------------------
sub("""    if (!splitOn) {
      VX = 0; VY = 0; VW = cw; VH = ch;
      player.viewX = 0; player.viewY = 0; player.viewW = cw; player.viewH = ch; player.zoom = zoom;
      renderScene();
      return;
    }""",
"""    if (!splitOn) {
      VX = 0; VY = 0; VW = cw; VH = ch;
      player.viewX = 0; player.viewY = 0; player.viewW = cw; player.viewH = ch; player.zoom = zoom;
      if (killcam) {
        // see the world as the one who got you saw it
        var me = player;
        player = killcam.k; noOverlay = true;
        try { renderScene(); } finally { player = me; noOverlay = false; }
        renderKillcam();
        return;
      }
      renderScene();
      return;
    }""")
sub("""  function renderDropHint() {""", r"""  function renderKillcam() {
    var kc = killcam, k = kc.k;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.save();
    var ease = Math.min(1, kc.t / 0.35);
    // letterbox bars and a red edge
    var bar = Math.round(ch * 0.09 * ease);
    ctx.fillStyle = '#05070b';
    ctx.fillRect(0, 0, cw, bar); ctx.fillRect(0, ch - bar, cw, bar);
    var vg = ctx.createRadialGradient(cw / 2, ch / 2, Math.min(cw, ch) * 0.3, cw / 2, ch / 2, Math.max(cw, ch) * 0.7);
    vg.addColorStop(0, 'rgba(120,0,20,0)'); vg.addColorStop(1, 'rgba(120,0,20,' + (0.35 * ease).toFixed(3) + ')');
    ctx.fillStyle = vg; ctx.fillRect(0, 0, cw, ch);
    // a ring around them
    var sx = (k.x - cam.x) * zoom + cw / 2, sy = (k.y - cam.y) * zoom + ch / 2;
    var pulse = 1 + Math.sin(kc.t * 7) * 0.08;
    ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.arc(sx, sy, 26 * zoom * pulse + 6, 0, 6.2832); ctx.stroke();
    ctx.strokeStyle = '#ff4d5e'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(sx, sy, 26 * zoom * pulse + 6, 0, 6.2832); ctx.stroke();
    // who, with what
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    var ty = bar + 44;
    ctx.font = '500 11px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(241,231,208,.75)';
    ctx.fillText('KILLED BY', cw / 2, ty - 22);
    ctx.font = '400 30px "Russo One", "Chakra Petch", sans-serif';
    ctx.lineJoin = 'round'; ctx.lineWidth = 6; ctx.strokeStyle = '#0d0f12';
    ctx.strokeText(k.name, cw / 2, ty + 6);
    ctx.fillStyle = '#ff5a68';
    ctx.fillText(k.name, cw / 2, ty + 6);
    ctx.font = '600 12px "IBM Plex Mono", monospace';
    var line = kc.gun + '  ·  ' + kc.d + 'u AWAY  ·  ' + kc.hp + ' HP LEFT';
    ctx.lineWidth = 4; ctx.strokeText(line, cw / 2, ty + 36);
    ctx.fillStyle = '#f1e7d0'; ctx.fillText(line, cw / 2, ty + 36);
    // what happens next
    var nxt = kc.after ? 'RESULTS IN ' + Math.max(1, Math.ceil(kc.dur - kc.t))
            : (player.respawnT > 0 ? 'RESPAWN IN ' + Math.ceil(player.respawnT) : '');
    if (nxt) {
      ctx.font = '500 11px "IBM Plex Mono", monospace';
      ctx.fillStyle = 'rgba(241,231,208,.7)';
      ctx.fillText(nxt, cw / 2, ch - bar - 22);
    }
    ctx.restore();
  }

  function renderDropHint() {""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p57 applied')
