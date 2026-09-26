# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ================================================================ downing ====
# With a squad behind you a killing shot puts you down rather than out. You
# bleed while a teammate has time to reach you; alone, it just kills you.
sub("""      _spd: 0, kills: 0, skin: 0, team: 0""",
    """      _spd: 0, kills: 0, skin: 0, team: 0, down: false, downT: 0, revT: 0""")

sub("""    e.fireT = 0; e.reloadT = 0; e.useT = 0; e.stepT = 0;""",
    """    e.fireT = 0; e.reloadT = 0; e.useT = 0; e.stepT = 0;
    e.down = false; e.downT = 0; e.revT = 0;""")

sub("""  function kill(e, fromId) {
    e.alive = false; e.hp = 0;""",
"""  function kill(e, fromId) {
    // someone still standing on your side? then you go down, not out
    if (!e.down) {
      var helper = false;
      for (var h = 0; h < ents.length; h++) {
        var m = ents[h];
        if (m !== e && m.alive && !m.down && m.team === e.team) { helper = true; break; }
      }
      if (helper) {
        e.down = true; e.downT = 22; e.revT = 0;
        e.hp = 24;
        e.target = null; e.path = null; e.reloadT = 0; e.useT = 0;
        spark(e.x, e.y, 10, '255,77,141', 150);
        emit(e.x, e.y, MOVE_SND.hit, e.id, 'hit');
        var dn = ents[fromId];
        if (e === player) feed('<b>DOWNED</b> - hold on for a teammate', true);
        else if (e.team === player.team) feed('<b>' + e.name + '</b> is down', true);
        else if (dn === player) feed('<b>YOU</b> downed ' + e.name, true);
        return;
      }
    }
    e.alive = false; e.hp = 0; e.down = false;""")

# a downed fighter bleeds, and a teammate standing over them brings them back
sub("""    if (MODE.respawn) {""",
"""    for (i = 0; i < ents.length; i++) {
      e = ents[i];
      if (!e.alive || !e.down) continue;
      var medic = null;
      for (var j2 = 0; j2 < ents.length; j2++) {
        var m2 = ents[j2];
        if (m2 === e || !m2.alive || m2.down || m2.team !== e.team) continue;
        if (dist(m2, e) < 30) { medic = m2; break; }
      }
      if (medic) {
        e.revT += dt;
        if (e.revT >= 2.6) {
          e.down = false; e.revT = 0; e.downT = 0;
          e.hp = 50;
          if (e === player) feed('<b>BACK UP</b> - ' + medic.name + ' got you', true);
          else if (e.team === player.team) feed('<b>' + e.name + '</b> is back up', true);
          audioEmit(e.x, e.y, PICK_SND, e.id);
        }
      } else {
        e.revT = Math.max(0, e.revT - dt * 0.6);
        e.downT -= dt;
        e.hp -= dt * 0.9;
        if (e.downT <= 0 || e.hp <= 0) { e.hp = 0; kill(e, -1); }
      }
    }

    if (MODE.respawn) {""")

# downed fighters do not act
sub("""      if (e.bot && e.alive) botThink(e, dt);""",
    """      if (e.bot && e.alive && !e.down) botThink(e, dt);""")

sub("""  function updatePlayer(dt) {
    var e = player;
    if (!e.alive) return;""",
"""  function updatePlayer(dt) {
    var e = player;
    if (!e.alive) return;
    if (e.down) { e._spd = 0; promptItem = null; lean.on = false; return; }""")

# allied bots break off to pick you up
sub("""          if (!want && player.alive && e.team === player.team && dist(e, player) > 230) {
            want = { x: player.x, y: player.y };
            following = true;
          }""",
"""          // a downed squadmate outranks anything else lying around
          var hurt = null, hurtD = 900;
          for (var dq = 0; dq < ents.length; dq++) {
            var cand = ents[dq];
            if (!cand.alive || !cand.down || cand.team !== e.team) continue;
            var cd = dist(e, cand);
            if (cd < hurtD) { hurtD = cd; hurt = cand; }
          }
          if (hurt) { want = { x: hurt.x, y: hurt.y }; following = true; }
          if (!want && player.alive && e.team === player.team && dist(e, player) > 230) {
            want = { x: player.x, y: player.y };
            following = true;
          }""")

# ---- how a downed fighter looks ------------------------------------------
sub("""    if (PACK_READY) {
      var tint = TEAM_TINT[e.team === player.team ? 0 : 1];""",
"""    if (PACK_READY && e.down) {
      var dt2 = TEAM_TINT[e.team === player.team ? 0 : 1];
      ctx.fillStyle = 'rgba(' + dt2 + ',.22)';
      ctx.beginPath(); ctx.ellipse(e.x, e.y, e.r * 1.5, e.r * 0.95, 0, 0, 6.2832); ctx.fill();
      ctx.globalAlpha = 0.55;
      drawPacked(e);
      ctx.globalAlpha = 1;
      if (e.revT > 0) {
        ctx.strokeStyle = '#7ce7d8';
        ctx.lineWidth = 2.4 / zoom;
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.r + 8, -Math.PI / 2, -Math.PI / 2 + 6.2832 * (e.revT / 2.6));
        ctx.stroke();
      } else {
        ctx.strokeStyle = 'rgba(255,77,141,.8)';
        ctx.lineWidth = 1.8 / zoom;
        ctx.beginPath(); ctx.arc(e.x, e.y, e.r + 8, 0, 6.2832); ctx.stroke();
      }
      return;
    }
    if (PACK_READY) {
      var tint = TEAM_TINT[e.team === player.team ? 0 : 1];""")

# ---- your own downed state on the HUD ------------------------------------
sub("""  function renderLean() {""",
"""  function renderDowned() {
    if (!player.alive || !player.down) return;
    var label = player.revT > 0
      ? 'BEING PICKED UP  ' + Math.ceil(2.6 - player.revT) + 's'
      : 'DOWNED  \\u00b7  ' + Math.ceil(player.downT) + 's';
    ctx.font = '700 13px "Chakra Petch", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    var tw = ctx.measureText(label).width;
    var bw = tw + 40, bh = 30, bx = cw / 2 - bw / 2, by = ch * 0.62;
    ctx.fillStyle = 'rgba(10,15,22,.86)';
    ctx.fillRect(bx, by, bw, bh);
    ctx.strokeStyle = player.revT > 0 ? 'rgba(124,231,216,.8)' : 'rgba(255,77,141,.8)';
    ctx.lineWidth = 1;
    ctx.strokeRect(bx + .5, by + .5, bw - 1, bh - 1);
    ctx.fillStyle = player.revT > 0 ? '#7ce7d8' : '#ff4d8d';
    ctx.fillText(label, cw / 2, by + bh / 2 + 1);
    ctx.textAlign = 'left';
  }

  function renderLean() {""")

sub("""    renderLean();
    renderPrompt();""",
"""    renderLean();
    renderDowned();
    renderPrompt();""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p20 applied')
