# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# The infected outran everyone and killed in three touches, so the living were
# gone inside a minute. They should be faster than a walk and slower than a
# sprint - you can break contact, but only by making noise.
sub("""      var zspeed = 244;""", """      var zspeed = 198;""")
sub("""    var speed = isZombie(e) ? 244 : (w ? 165 : 186);""",
    """    var speed = isZombie(e) ? 198 : (w ? 165 : 186);""")
sub("""    var base = curW(e) ? 168 : (MODE.zombies && e.team === 1 ? 236 : 190);""",
    """    var base = curW(e) ? 168 : (MODE.zombies && e.team === 1 ? 196 : 190);""")

# a touch hurts, it does not delete you
sub("""      damage(o, 48, e.id, Math.atan2(dy, dx));""",
    """      damage(o, isZombie(e) ? 30 : 48, e.id, Math.atan2(dy, dx));""")

# easier to put down than a soldier
sub("""    e.hp = 100; e.alive = true; e.respawnT = 0;""",
    """    e.hp = (MODE.zombies && e.team === 1) ? 68 : 100;
    e.alive = true; e.respawnT = 0;""")

# they smell you out, but not from across the map
sub("""        var near2 = null, nd2 = 820;""", """        var near2 = null, nd2 = 520;""")

# fewer on the field at once, arriving less relentlessly
sub("""  var ZOMB_CAP = 22;""", """  var ZOMB_CAP = 14;""")
sub("""        zombSpawnT = 5.2 - 3.9 * gone;
        spawnZombie();
        if (gone > 0.45) spawnZombie();                        // in pairs later on
        if (gone > 0.8) spawnZombie();""",
"""        zombSpawnT = 6.5 - 3.3 * gone;
        spawnZombie();
        if (gone > 0.6) spawnZombie();                         // in pairs later on""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p34 applied')
