# -*- coding: utf-8 -*-
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read(); o = s

def sub(a, b):
    global s
    if a not in s:
        raise SystemExit('PATTERN NOT FOUND:\n' + a[:200])
    s = s.replace(a, b, 1)

# maps were capped by the tile-array stride; lift it well clear
sub("""  var STRIDE = 96;                 // max map dimension; maps vary inside it""",
    """  var STRIDE = 168;                // max map dimension; maps vary inside it""")

# longer paths need more room to search
sub("""    while (open.n.length && expanded < 7000) {""",
    """    while (open.n.length && expanded < 24000) {""")

sub("""  var NAMES = ['VESPER', 'MAGPIE', 'KESTREL', 'SABLE', 'JUNIPER', 'HOLLOW', 'CINDER', 'WREN', 'OTTER',
               'RAVEN', 'LARK', 'FINCH', 'HERON', 'SWIFT', 'PLOVER', 'MARTIN', 'ROOK', 'CRANE', 'TEAL'];""",
"""  var NAMES = ['VESPER', 'MAGPIE', 'KESTREL', 'SABLE', 'JUNIPER', 'HOLLOW', 'CINDER', 'WREN', 'OTTER',
               'RAVEN', 'LARK', 'FINCH', 'HERON', 'SWIFT', 'PLOVER', 'MARTIN', 'ROOK', 'CRANE', 'TEAL',
               'PETREL', 'SHRIKE', 'CURLEW', 'GANNET', 'BITTERN', 'AVOCET', 'DUNLIN', 'SISKIN', 'REDPOLL',
               'FULMAR', 'JACKDAW', 'CHOUGH', 'WIGEON'];""")

# --- bigger fields --------------------------------------------------------
sub("""    br:   { field: 10, zone: true,  loot: true,  respawn: false, label: 'ALIVE' },""",
    """    br:   { field: 26, zone: true,  loot: true,  respawn: false, label: 'ALIVE' },""")
sub("""    gun:  { field: 6,  zone: false, loot: false, respawn: true,  label: 'LEVEL' },""",
    """    gun:  { field: 10, zone: false, loot: false, respawn: true,  label: 'LEVEL' },""")
sub("""    team: { field: 10, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 30, teams: true },""",
    """    team: { field: 16, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 40, teams: true },""")
sub("""    war:  { field: 20, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 75, teams: true },""",
    """    war:  { field: 30, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 100, teams: true },""")
sub("""    ctf:  { field: 10, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 3, teams: true, ctf: true }""",
    """    ctf:  { field: 14, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 3, teams: true, ctf: true }""")

# --- bigger maps ----------------------------------------------------------
sub("""    else if (mode === 'gun') genRooms(66, 66, 6, 13, 30, 2, true);""",
    """    else if (mode === 'gun') genRooms(96, 96, 6, 13, 52, 2, true);""")
sub("""    else if (mode === 'team') genRooms(72, 72, 7, 14, 28, 2, true);""",
    """    else if (mode === 'team') genRooms(118, 118, 7, 15, 66, 2, true);""")
sub("""    else if (mode === 'war') genRooms(86, 86, 8, 16, 34, 2, true);""",
    """    else if (mode === 'war') genRooms(156, 156, 8, 18, 110, 2, true);""")
sub("""    else if (mode === 'ctf') genRooms(76, 76, 7, 14, 30, 2, true);""",
    """    else if (mode === 'ctf') genRooms(126, 126, 7, 15, 74, 2, true);""")
sub("""    else genRooms(62, 62, 5, 12, 34, 1, true);""",
    """    else genRooms(130, 130, 5, 13, 118, 1, true);""")

sub("""  function genWorld() {
    MAP_W = 92; MAP_H = 92;""",
"""  function genWorld() {
    MAP_W = 158; MAP_H = 158;""")
sub("""    for (i = 0; i < 420 && builds.length < 26; i++) {""",
    """    for (i = 0; i < 1400 && builds.length < 78; i++) {""")
sub("""    for (i = 0; i < 260; i++) {
      var cxx = 3 + rnd(MAP_W - 6), cyy = 3 + rnd(MAP_H - 6);""",
"""    for (i = 0; i < 820; i++) {
      var cxx = 3 + rnd(MAP_W - 6), cyy = 3 + rnd(MAP_H - 6);""")

# --- loot scales with the ground it is scattered over ---------------------
sub("""    var counts = mapKind === 'world' ? { gun: 46, ammo: 72, med: 26 } : { gun: 30, ammo: 46, med: 18 };""",
"""    var acreage = floorTiles.length;
    var counts = {
      gun: Math.max(24, Math.round(acreage / 72)),
      ammo: Math.max(36, Math.round(acreage / 46)),
      med: Math.max(14, Math.round(acreage / 118))
    };""")

assert s != o
io.open(p, 'w', encoding='utf-8').write(s)
print('p24 applied')
