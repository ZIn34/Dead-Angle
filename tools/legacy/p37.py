# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# They arrived one at a time, which never reads as a horde. Now a wave lands
# as a pack out of one spot and walks in together - and each one is far less
# of a threat on its own, because there will be a lot of them.
sub("""  // Feed another one in, somewhere well away from the living.
  function spawnZombie() {
    var live = 0;
    for (var i = 0; i < ents.length; i++) if (ents[i].alive && ents[i].team === 1) live++;
    // the field they can hold grows as the clock runs down, so the last
    // minute is the hard one
    var gone = MODE.clock ? 1 - clamp(zombClock / MODE.clock, 0, 1) : 0;
    if (live >= 11 + Math.round(gone * 9) || ents.length > 80) return;
    var t = pickRespawnTile(player);
    var z = makeEnt(t, false, 'WALKER ' + (ents.length + 1));
    z.team = 1;
    ents.push(z);
    placeEnt(z, t);            // loadout reads the team, so it comes up empty-handed
    z.skin = ZOMBIE_SKIN;
    return z;
  }""",
"""  function zombiesUp() {
    var n = 0;
    for (var i = 0; i < ents.length; i++) if (ents[i].alive && ents[i].team === 1) n++;
    return n;
  }
  function zombCap() {
    var gone = MODE.clock ? 1 - clamp(zombClock / MODE.clock, 0, 1) : 0;
    return 18 + Math.round(gone * 26);       // 18 early, 44 by the end
  }
  function spawnZombieAt(t) {
    var z = makeEnt(t, false, 'WALKER ' + (ents.length + 1));
    z.team = 1;
    ents.push(z);
    placeEnt(z, t);            // loadout reads the team, so it comes up empty-handed
    z.skin = ZOMBIE_SKIN;
    return z;
  }
  // A wave: one spot, well away from the living, and a crowd out of it.
  function spawnZombie() {
    var cap = zombCap();
    if (zombiesUp() >= cap || ents.length > 120) return;
    var anchor = pickRespawnTile(player);
    var pack = 5 + rnd(5);
    for (var i = 0; i < pack; i++) {
      if (zombiesUp() >= cap || ents.length > 120) break;
      var t = anchor;
      for (var tries = 0; tries < 24; tries++) {
        var cx4 = anchor.x + rnd(11) - 5, cy4 = anchor.y + rnd(11) - 5;
        if (!isWall(cx4, cy4)) { t = { x: cx4, y: cy4 }; break; }
      }
      spawnZombieAt(t);
    }
  }""")

# waves, not a drip
sub("""        zombSpawnT = 6.5 - 3.3 * gone;
        spawnZombie();
        if (gone > 0.6) spawnZombie();                         // in pairs later on""",
"""        zombSpawnT = 13 - 7 * gone;                            // a wave, then a lull
        spawnZombie();""")

sub("""      zombSpawnT = 4;""", """      zombSpawnT = 2;""")

# weak individually - the threat is the number of them
sub("""    e.hp = (MODE.zombies && e.team === 1) ? 82 : 100;""",
    """    e.hp = (MODE.zombies && e.team === 1) ? 38 : 100;""")
sub("""      damage(o, isZombie(e) ? 30 : 48, e.id, Math.atan2(dy, dx));""",
    """      damage(o, isZombie(e) ? 13 : 48, e.id, Math.atan2(dy, dx));""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p37 applied')
