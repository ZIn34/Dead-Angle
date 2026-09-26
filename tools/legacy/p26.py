# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# ==================================================== melee ==================
sub("""  var PIN_SND   = { maxR: 300,  speed: 760,  color: '200,200,180', w: 1.2,""",
"""  var MELEE_SND = { maxR: 420,  speed: 780,  color: '198,212,227', w: 1.8,
                    aud: { rate: 0.85, cut: 2000, hp: 140, decay: 0.16, body: 88, vol: 0.45 } };
  var PIN_SND   = { maxR: 300,  speed: 760,  color: '200,200,180', w: 1.2,""")

sub("""      fireT: 0, reloadT: 0, stepT: 0, useT: 0, respawnT: 0,""",
    """      fireT: 0, reloadT: 0, stepT: 0, useT: 0, respawnT: 0, meleeT: 0, swingT: 0,""")

sub("""  function useMed(e) {""",
"""  // Out of ammo is not out of the fight - swing the gun.
  function melee(e) {
    if (!e.alive || e.down || e.meleeT > 0 || e.useT > 0) return;
    e.meleeT = 0.55;
    e.swingT = 0.18;
    e.reloadT = 0;
    emit(e.x, e.y, MELEE_SND, e.id, 'melee');
    var hitAny = false;
    for (var i = 0; i < ents.length; i++) {
      var o = ents[i];
      if (o === e || !o.alive || !foes(e, o)) continue;
      var dx = o.x - e.x, dy = o.y - e.y;
      var d = Math.sqrt(dx * dx + dy * dy);
      if (d > 40) continue;
      var diff = ((Math.atan2(dy, dx) - e.ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
      if (Math.abs(diff) > 1.0) continue;
      if (!lineClear(e.x, e.y, o.x, o.y)) continue;
      damage(o, 48, e.id, Math.atan2(dy, dx));
      hitAny = true;
    }
    if (hitAny && e === player) shake = Math.min(shake + 3, 8);
  }

  function useMed(e) {""")

sub("""      if (e.animFire > 0) e.animFire -= dt;
    }""",
"""      if (e.animFire > 0) e.animFire -= dt;
      if (e.meleeT > 0) e.meleeT -= dt;
      if (e.swingT > 0) e.swingT -= dt;
    }""")

# clicking with nothing left swings instead
sub("""    var firing = mouse.down || (sticks.aim && Math.abs(sticks.aim.x - sticks.aim.ox) + Math.abs(sticks.aim.y - sticks.aim.oy) > 26);
    if (firing && curW(e)) {
      if (curSlot(e).ammo <= 0) startReload(e);
      else fire(e);
    }""",
"""    var firing = mouse.down || (sticks.aim && Math.abs(sticks.aim.x - sticks.aim.ox) + Math.abs(sticks.aim.y - sticks.aim.oy) > 26);
    if (firing) {
      var cw2 = curW(e), cs2 = curSlot(e);
      if (!cw2 || (cs2.ammo <= 0 && e.reserve <= 0)) melee(e);   // nothing to shoot with
      else if (cs2.ammo <= 0) startReload(e);
      else fire(e);
    }""")

sub("""      else if (k === 'h') throwNade(player, 'smoke');""",
"""      else if (k === 'h') throwNade(player, 'smoke');
      else if (k === 'v') melee(player);
      else if (k === 'x' && player.down) { player.hp = 0; kill(player, -1); }""")

# the swing, drawn as a short arc
sub("""      for (var cf = 0; cf < flags.length; cf++) {""",
"""      if (e.swingT > 0) {
        var sw2 = 1 - e.swingT / 0.18;
        ctx.strokeStyle = 'rgba(214,228,242,' + (0.75 * (1 - sw2)).toFixed(3) + ')';
        ctx.lineWidth = 3 / zoom;
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.r + 24, e.ang - 1.0 + sw2 * 2.0, e.ang - 0.7 + sw2 * 2.0);
        ctx.stroke();
      }
      for (var cf = 0; cf < flags.length; cf++) {""")

# ==================================================== bot behaviour ==========
sub("""    var reloadRetreat = D.smart && e.reloadT > 0 && e.target && dist(e, e.target) < 420;""",
"""    // carrying the flag outranks every other instinct
    var carrying = MODE.ctf && flags.length === 2 && flags[1 - e.team].carrier === e;
    // a squadmate on the floor within arm's reach: stand still and work
    var picking = null;
    for (var pv = 0; pv < ents.length; pv++) {
      var pc = ents[pv];
      if (pc !== e && pc.alive && pc.down && pc.team === e.team && dist(e, pc) < 26) { picking = pc; break; }
    }
    var reloadRetreat = D.smart && e.reloadT > 0 && e.target && dist(e, e.target) < 420;""")

sub("""      followPath(e, dt, speed);
      footstep(e, dt, true);
    } else if ((dry || reloadRetreat || hurtRetreat) && e.target) {""",
"""      followPath(e, dt, speed);
      footstep(e, dt, true);
    } else if (carrying) {
      // straight home, shooting on the move - no stopping to duel
      var own = flags[e.team];
      speed = 236;
      if (!e.path || e.repathT <= 0) pathTo(e, own.hx, own.hy, 1.1);
      followPath(e, dt, speed);
      footstep(e, dt, true);
    } else if (picking) {
      e.path = null;                     // hold position until they are up
    } else if ((dry || reloadRetreat || hurtRetreat) && e.target) {""")

# a dry bot at arm's length swings rather than running
sub("""    if (!w) return;

    if (e.target && e.reactT <= 0) {""",
"""    if (!w) {
      if (e.target && e.alive && dist(e, e.target) < 38) {
        var mdiff = ((Math.atan2(e.target.y - e.y, e.target.x - e.x) - e.ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
        e.ang += clamp(mdiff, -D.turn * dt, D.turn * dt);
        if (Math.abs(mdiff) < 0.7) melee(e);
      }
      return;
    }

    if (e.target && e.reactT <= 0) {""")

# ==================================================== give up ================
sub("""    var label = player.revT > 0
      ? 'BEING PICKED UP  ' + Math.ceil(2.6 - player.revT) + 's'
      : 'DOWNED  \\u00b7  ' + Math.ceil(player.downT) + 's';""",
"""    var label = player.revT > 0
      ? 'BEING PICKED UP  ' + Math.ceil(2.6 - player.revT) + 's'
      : 'DOWNED  \\u00b7  ' + Math.ceil(player.downT) + 's  \\u00b7  X TO GIVE UP';""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p26 applied')
