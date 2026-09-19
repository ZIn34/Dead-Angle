# -*- coding: utf-8 -*-
"""First to spot, first to shoot, wins: a vision cone, double gun damage, and
bleeding out below half health."""
import io, re, sys
G = sys.argv[1]
s = io.open(G, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:240])
    s = s.replace(a, b, 1)

# ---- double damage for every gun ---------------------------------------------
for key, old in (('pistol', '18'), ('shotgun', '11'), ('rifle', '38'), ('silenced', '16')):
    pat = re.compile(r"(\n    " + key + r":\s+\{ name: '[A-Z]+',\s+dmg: )" + old + r",")
    s, n = pat.subn(lambda m: m.group(1) + str(int(old) * 2) + ",", s, count=1)
    if n != 1:
        raise SystemExit('weapon not found: ' + key)

# ---- vision cone ---------------------------------------------------------------
sub("""  function visibleToPlayer(x, y) {""",
"""  // You see what is in front of you, plus a little circle right around you
  // (you would feel someone at your back). Bots get the same eyes.
  var FOV_HALF = 0.96, NEAR_SEE = 60;
  function inCone(e, x, y, half) {
    var dx = x - e.x, dy = y - e.y;
    if (dx * dx + dy * dy <= NEAR_SEE * NEAR_SEE) return true;
    var d = Math.atan2(dy, dx) - e.ang;
    d = ((d + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
    return Math.abs(d) <= (half || FOV_HALF);
  }
  function visibleToPlayer(x, y) {
    if (!inCone(player, x, y)) return false;""")
sub("""  function litVisible(x, y, reach) {""", """  function litVisible(x, y, reach) {
    if (!inCone(player, x, y)) return false;""")
# the lit region is the line of sight AND the cone
sub("""    poly.closePath();
    ctx.clip(poly);""",
"""    poly.closePath();
    ctx.clip(poly);
    var cone = new Path2D(), cR = VIEW_R + TILE * 3;
    cone.moveTo(player.x, player.y);
    cone.arc(player.x, player.y, cR, player.ang - FOV_HALF, player.ang + FOV_HALF);
    cone.closePath();
    cone.moveTo(player.x + NEAR_SEE, player.y);
    cone.arc(player.x, player.y, NEAR_SEE, 0, 6.2832);
    ctx.clip(cone);""")
# bots only pick up someone new that is in front of them (they still hear)
sub("""        if (d >= reach2 || !sightClear(e.x, e.y, o.x, o.y)) continue;""",
    """        if (d >= reach2 || !sightClear(e.x, e.y, o.x, o.y)) continue;
        if (o !== e.target && !inCone(e, o.x, o.y, FOV_HALF + 0.15)) continue;""")

# ---- bleeding out ------------------------------------------------------------------
sub("""    e.hp -= amount;
    e.useT = 0;""", """    e.hp -= amount;
    e.useT = 0;
    // shot down to half or worse: bleeding until a stim closes it up
    if (e.hp > 0 && e.hp <= 50 && !isZombie(e) && hitBy && hitBy !== e && !e.down) {
      if (!e.bleeding && e.local) feed('<b>BLEEDING</b> - use a stim', true);
      e.bleeding = true; e.bleedBy = fromId;
    }""")
# the stim closes the wound (players and bots)
s = s.replace("""if (e.useT <= 0) e.hp = Math.min(100, e.hp + 45);""",
              """if (e.useT <= 0) { e.hp = Math.min(100, e.hp + 45); e.bleeding = false; }""")
# revived, respawned or downed: no longer this kind of bleed
sub("""          e.down = false; e.revT = 0; e.downT = 0; e.downedBy = -1;""",
    """          e.down = false; e.revT = 0; e.downT = 0; e.downedBy = -1; e.bleeding = false;""")
sub("""    e.alive = true; e.respawnT = 0;""", """    e.alive = true; e.respawnT = 0; e.bleeding = false;""")
sub("""        e.down = true; e.downT = 22; e.revT = 0;""", """        e.down = true; e.downT = 22; e.revT = 0; e.bleeding = false;""")
# 5 HP a second; the one who shot you gets the kill
sub("""    if (mode === 'tut') tutTick(dt);""", """    for (i = 0; i < ents.length; i++) {
      var bl = ents[i];
      if (!bl.alive || !bl.bleeding || bl.down || bl.air) continue;
      if (godMode && bl === player) continue;
      bl.hp -= 5 * dt;
      if (bl.hp <= 0) { bl.hp = 0; bl.bleeding = false; hitCause = 'bleed'; kill(bl, ents[bl.bleedBy] && ents[bl.bleedBy] !== bl ? bl.bleedBy : -1); hitCause = 'gun'; }
    }
    if (mode === 'tut') tutTick(dt);""")
# drips while bleeding, even standing still
sub("""      if (!e.alive || e.air || e.hp >= 40 || !e.moving) continue;""",
    """      if (!e.alive || e.air || !(e.bleeding || (e.hp < 40 && e.moving))) continue;""")

# ---- tell the player -------------------------------------------------------------
sub("""  function renderDamage() {
    if (noOverlay) return;""", """  function renderDamage() {
    if (noOverlay) return;
    if (player.alive && player.bleeding && !player.down) {
      // a pulsing red edge and a reminder of the fix
      var bp = 0.18 + 0.12 * Math.sin(performance.now() / 180);
      var bg = ctx.createRadialGradient(cw / 2, ch / 2, Math.min(cw, ch) * 0.25, cw / 2, ch / 2, Math.max(cw, ch) * 0.6);
      bg.addColorStop(0, 'rgba(160,0,20,0)'); bg.addColorStop(1, 'rgba(160,0,20,' + bp.toFixed(3) + ')');
      ctx.fillStyle = bg; ctx.fillRect(0, 0, cw, ch);
      ctx.save();
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.font = '400 15px "Russo One", "Chakra Petch", sans-serif';
      var bt = 'BLEEDING  \\u00b7  ' + promptKey('F', 'Y') + ' TO USE A STIM' + (player.meds ? '' : ' (NONE - FIND ONE)');
      ctx.lineWidth = 4; ctx.strokeStyle = '#0d0f12'; ctx.strokeText(bt, cw / 2, ch * 0.78);
      ctx.fillStyle = '#ff5a68'; ctx.fillText(bt, cw / 2, ch * 0.78);
      ctx.restore();
    }""")

# ---- online guests need to know they are bleeding --------------------------------
sub("""               (e.air === 'plane' ? 8 : 0) | (e.air === 'chute' ? 16 : 0) | (e.bot ? 32 : 0);""",
    """               (e.air === 'plane' ? 8 : 0) | (e.air === 'chute' ? 16 : 0) | (e.bot ? 32 : 0) | (e.bleeding ? 64 : 0);""")
sub("""    e.air = (bits & 8) ? 'plane' : ((bits & 16) ? 'chute' : null); e.bot = !!(bits & 32);""",
    """    e.air = (bits & 8) ? 'plane' : ((bits & 16) ? 'chute' : null); e.bot = !!(bits & 32); e.bleeding = !!(bits & 64);""")

assert s != o
io.open(G, 'w', encoding='utf-8', newline='').write(s)
print('p58 applied')
