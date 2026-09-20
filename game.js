/* EARSHOT - dark-map shooter prototype.
   Rule of the build: nothing crosses the darkness except sound. Flashes,
   tracers and sparks render only inside the visibility polygon; what reaches
   you from the black is a sound ring and a damage direction, nothing else. */
(function () {
  'use strict';

  // ---------------------------------------------------------------- constants
  var TILE = 26;
  var STRIDE = 232;                // max map dimension; maps vary inside it
  var MAP_W = 62, MAP_H = 62;
  var WORLD_W = 0, WORLD_H = 0;
  var VIEW_BASE = 250;             // sight radius the camera zoom is built around
  var VIEW_BLACKOUT = 105;         // blackout: barely enough to walk by
  var FLASH_REACH = 1400;          // how far a muzzle flash carries in blackout
  var VIEW_R = VIEW_BASE;          // current sight radius, set per match
  var RESERVE_MAX = 180;
  var START_RESERVE = 40;

  var NAMES = ['VESPER', 'MAGPIE', 'KESTREL', 'SABLE', 'JUNIPER', 'HOLLOW', 'CINDER', 'WREN', 'OTTER',
               'RAVEN', 'LARK', 'FINCH', 'HERON', 'SWIFT', 'PLOVER', 'MARTIN', 'ROOK', 'CRANE', 'TEAL',
               'PETREL', 'SHRIKE', 'CURLEW', 'GANNET', 'BITTERN', 'AVOCET', 'DUNLIN', 'SISKIN', 'REDPOLL',
               'FULMAR', 'JACKDAW', 'CHOUGH', 'WIGEON', 'OSPREY', 'MERLIN', 'HOBBY', 'KITE', 'SHAG',
               'PIPIT', 'LINNET', 'BUNTING', 'DIPPER', 'NUTHATCH', 'TWITE', 'SCOTER', 'EIDER', 'SMEW',
               'GOSHAWK', 'KNOT', 'STINT', 'RUFF', 'QUAIL', 'CORNCRAKE', 'WHIMBREL', 'GODWIT', 'SNIPE',
               'TERN', 'SKUA', 'PUFFIN', 'GUILLEMOT', 'RAZORBILL'];

  // Each weapon's noise is its identity - you learn who is carrying what from
  // the size and colour of the ring their shot throws.
  // aud: how the shot is synthesised. rate/cut/hp shape the crack, body is the
  // low thump under it, vol is loudness at the muzzle.
  var WEAPONS = {
    pistol:   { name: 'PISTOL',   semi: true, tap: 0.075, dmg: 36, pellets: 1, interval: 0.22,  mag: 12, spread: 0.035, reload: 1.10, speed: 1150, tint: '#ffc95e', snd: { maxR: 900,  speed: 980,  color: '255,201,94',  w: 2.0, aud: { rate: 1.00, cut: 3200, hp: 220, decay: 0.17, body: 150, vol: 0.50 } } },
    shotgun:  { name: 'SHOTGUN',  dmg: 22, pellets: 7, interval: 0.78,  mag: 6,  spread: 0.155, reload: 2.00, speed: 980,  tint: '#ff7a4d', snd: { maxR: 1700, speed: 1040, color: '255,122,77',  w: 3.0, aud: { rate: 0.68, cut: 2100, hp: 90,  decay: 0.36, body: 78,  vol: 0.85 } } },
    rifle:    { name: 'SNIPER',   dmg: 76, pellets: 1, interval: 0.58,  mag: 8,  spread: 0.012, reload: 1.80, speed: 1500, tint: '#fff5cd', snd: { maxR: 2000, speed: 1080, color: '255,245,205', w: 2.6, aud: { rate: 0.85, cut: 4400, hp: 150, decay: 0.44, body: 104, vol: 0.92 } } },
    silenced: { name: 'RIFLE',    dmg: 32, pellets: 1, interval: 0.115,  mag: 30, spread: 0.030, reload: 1.20, speed: 1050, tint: '#9db0c4', snd: { maxR: 540,  speed: 760,  color: '157,176,196', w: 1.8, aud: { rate: 1.55, cut: 1900, hp: 380, decay: 0.10, body: 96,  vol: 0.58 } } }
  };
  var WEAPON_KEYS = ['pistol', 'shotgun', 'rifle', 'silenced'];
  var WEAPON_WEIGHT = [32, 22, 20, 26];
  var LADDER = ['pistol', 'shotgun', 'rifle', 'silenced'];

  var MOVE_SND = {
    sprint: { maxR: 520, speed: 780, color: '255,122,77',  w: 1.7, aud: { rate: 0.55, cut: 1500, hp: 240, decay: 0.09, body: 0,  vol: 0.20 } },
    walk:   { maxR: 260, speed: 700, color: '124,231,216', w: 1.3, aud: { rate: 0.50, cut: 950,  hp: 200, decay: 0.07, body: 0,  vol: 0.13 } },
    reload: { maxR: 340, speed: 760, color: '157,176,196', w: 1.5, aud: { rate: 2.20, cut: 5200, hp: 900, decay: 0.05, body: 0,  vol: 0.22, twice: 0.13 } },
    hit:    { maxR: 430, speed: 820, color: '255,77,141',  w: 2.0, aud: { rate: 1.90, cut: 4600, hp: 700, decay: 0.09, body: 95, vol: 0.40 } }
  };

  // react: delay before a newly spotted target is engaged.  lead: how much of
  // the target's velocity they compensate for.  smart: cover discipline -
  // breaking contact to reload, flanking a noise instead of walking into it.
  var DIFF = [
    { react: 0.52, spread: 0.135, sight: 225, rate: 1.30, ear: 0.72, dmg: 0.42, turn: 5.0,  lead: 0.25, smart: false, aimTol: 0.20, miss: 0.42, settle: 0.9, wob: 0.17, track: 1.8 },
    { react: 0.28, spread: 0.078, sight: 275, rate: 1.00, ear: 1.00, dmg: 0.55, turn: 8.5,  lead: 0.75, smart: true,  aimTol: 0.15, miss: 0.36, settle: 1.2, wob: 0.14, track: 2.4 },
    { react: 0.14, spread: 0.042, sight: 330, rate: 0.80, ear: 1.20, dmg: 0.70, turn: 12.0, lead: 1.00, smart: true,  aimTol: 0.10, miss: 0.28, settle: 1.6, wob: 0.105, track: 3.4 }
  ];

  // Zone radii are fractions of the map's short side, so every map closes well.
  var PHASES = [
    { wait: 26, shrink: 16, f: 0.44, dps: 2 },
    { wait: 17, shrink: 14, f: 0.31, dps: 3 },
    { wait: 15, shrink: 12, f: 0.21, dps: 5 },
    { wait: 13, shrink: 11, f: 0.14, dps: 7 },
    { wait: 11, shrink: 10, f: 0.085, dps: 10 },
    { wait: 10, shrink: 9,  f: 0.045, dps: 14 },
    { wait: 9,  shrink: 9,  f: 0.020, dps: 20 }
  ];

  var MODES = {
    br:   { field: 48, zone: true,  loot: true,  respawn: false, label: 'ALIVE' },
    duel: { field: 2,  zone: false, loot: false, respawn: true,  label: 'SCORE', target: 5 },
    gun:  { field: 10, zone: false, loot: false, respawn: true,  label: 'LEVEL' },
    team: { field: 16, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 40, teams: true },
    war:  { field: 30, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 100, teams: true },
    ctf:  { field: 14, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 3, teams: true, ctf: true },
    sect: { field: 16, zone: false, loot: false, respawn: true,  label: 'SCORE', target: 150, teams: true, sectors: 3 },
    zomb: { field: 20, zone: false, loot: false, respawn: true,  label: 'ALIVE', teams: true, zombies: true, clock: 190 },
    tut:  { field: 1,  zone: false, loot: false, respawn: false, label: 'TUTORIAL' }
  };
  var ZOMBIE_SKIN = 8;

  // A carried flag announces itself - the only way anyone finds the runner.
  var FLAG_SND = { maxR: 760, speed: 700, color: '242,189,29', w: 2.2,
                   aud: { rate: 0.9, cut: 2400, hp: 300, decay: 0.16, body: 120, vol: 0.30 } };

  // Cool skins for your side, warm for theirs, so a glimpse is enough.
  var TEAM_SKINS = [[1, 4, 15, 13, 9], [2, 0, 11, 10, 7]];
  var TEAM_TINT = ['124,231,216', '255,122,77'];
  var MODE_TEXT = {
    br_cqb: 'Forty-eight drop into a dark warren of rooms and corridors. You land with empty hands \u2014 find a weapon before someone finds you, and stay inside the closing zone.',
    br_world: 'Forty-eight drop into open ground scattered with buildings. Long sightlines, nowhere to hide in the open, and the loot is inside the structures.',
    duel: 'One opponent, identical loadouts, on a small arena. First to five rounds. No looting \u2014 just you, them, and who moves quieter.',
    gun: 'Every elimination hands you the next weapon up the ladder: pistol, shotgun, sniper, rifle. Get a kill with the rifle to win. Everyone respawns.',
    zomb: 'A few turn at the start and more keep coming, faster as the clock runs down. The infected carry nothing and cannot shoot - they are faster than you, they find you without needing to see you, and a hit puts you on their side. Survive the clock and the living win; lose the last human and it is over.',
    sect: 'Three sectors, eight a side. Outnumber the other team inside one and it flips to you; every sector you hold pays a point a second, first to a hundred and fifty. Holding all three is loud, obvious work - they will hear exactly where you are.',
    ctf: 'Two flags, five a side, first to three captures. Your own flag has to be home for a capture to count. Carrying the enemy flag makes you ring out across the map every second - taking it is the easy part.',
    war: 'Twenty fighters, ten a side, first to seventy-five. A big map and constant contact - you will rarely be more than a few seconds from a firefight, and the ring of a shot is the only warning you get.',
    team: 'Five against five, everyone respawns, first side to thirty eliminations. Your squad wears cool colours and theirs wears warm - but in the dark you will hear them long before you can tell.'
  };

  // ---------------------------------------------------------------- dom
  var $ = function (id) { return document.getElementById(id); };
  var canvas = $('c'), ctx = canvas.getContext('2d');
  var elHud = $('hud'), elMenu = $('menu'), elOver = $('over'), elPaused = $('paused');
  var elAlive = $('aliveN'), elAliveL = $('aliveL'), elZone = $('zoneLine'), elFeed = $('feed');
  var elHpFill = $('hpFill'), elHpN = $('hpN');
  var elMedsBox = $('medsBox'), elMedsN = $('medsN');
  var elWep = $('wepBox'), elWName = $('wName'), elAmmoN = $('ammoN'), elResN = $('resN');
  var elSlot = [$('slot0'), $('slot1')];
  var elRelBar = $('relBar'), elRelFill = $('relFill');

  var cw = 0, ch = 0, dpr = 1, zoom = 1;

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    cw = canvas.clientWidth || window.innerWidth;
    ch = canvas.clientHeight || window.innerHeight;
    canvas.width = Math.max(1, Math.round(cw * dpr));
    canvas.height = Math.max(1, Math.round(ch * dpr));
    zoom = Math.max(0.55, Math.min(2.4, Math.min(cw, ch) / (VIEW_BASE * 2 + 60)));
  }
  window.addEventListener('resize', resize);

  // ---------------------------------------------------------------- utils
  function rnd(n) { return Math.floor(Math.random() * n); }
  function rr(a, b) { return a + Math.random() * (b - a); }
  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }
  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) { var j = rnd(i + 1); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function fmtTime(s) {
    s = Math.max(0, Math.floor(s));
    return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2);
  }
  function rollWeapon() {
    var total = 0, i;
    for (i = 0; i < WEAPON_WEIGHT.length; i++) total += WEAPON_WEIGHT[i];
    var r = Math.random() * total;
    for (i = 0; i < WEAPON_WEIGHT.length; i++) { r -= WEAPON_WEIGHT[i]; if (r <= 0) return WEAPON_KEYS[i]; }
    return 'pistol';
  }
  function gunScore(key) { var w = WEAPONS[key]; return w.dmg * w.pellets / w.interval; }

  // ---------------------------------------------------------------- audio
  // Everything is synthesised - no files to load. The important part: a shot
  // is scheduled to reach your ears at dist / ringSpeed, so you hear it at the
  // exact moment its ring crosses you.
  var actx = null, master = null, noiseBuf = null, muted = false;
  var SFX_BUF = {};

  function decodeSamples() {
    var src = window.EARSHOT_SFX;
    if (!src || !actx) return;
    Object.keys(src).forEach(function (name) {
      if (SFX_BUF[name]) return;
      try {
        var bin = atob(src[name]);
        var buf = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
        var done = function (b) { SFX_BUF[name] = b; };
        var res = actx.decodeAudioData(buf.buffer, done, function () {});
        if (res && res.then) res.then(done, function () {});
      } catch (err) { /* a clip that will not decode simply stays synthesised */ }
    });
  }

  function sampleVoice(buf, when, gain, muffle, pan, rate) {
    var out = master;
    if (actx.createStereoPanner) {
      var pn = actx.createStereoPanner();
      pn.pan.value = clamp(pan, -1, 1);
      pn.connect(master);
      out = pn;
    }
    var src = actx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = rate || 1;
    var lp = actx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = Math.max(320, 17000 * muffle * muffle);
    var g = actx.createGain();
    g.gain.value = gain;
    src.connect(lp); lp.connect(g); g.connect(out);
    src.start(when);
  }
  var NADE_SND  = { maxR: 1900, speed: 1100, color: '255,150,60', w: 3.4,
                    sample: 'frag', sampleGain: 1.0,
                    aud: { rate: 0.40, cut: 1500, hp: 45, decay: 0.75, body: 52, vol: 1.0 } };
  var SMOKE_SND = { maxR: 700,  speed: 900,  color: '200,206,214', w: 2.0,
                    sample: 'smoke', sampleGain: 1.0,
                    aud: { rate: 0.75, cut: 2600, hp: 160, decay: 0.55, body: 0, vol: 0.55 } };
  var MELEE_SND = { maxR: 420,  speed: 780,  color: '198,212,227', w: 1.8,
                    aud: { rate: 0.85, cut: 2000, hp: 140, decay: 0.16, body: 88, vol: 0.45 } };
  var PIN_SND   = { maxR: 300,  speed: 760,  color: '200,200,180', w: 1.2,
                    aud: { rate: 2.3, cut: 5200, hp: 1100, decay: 0.05, body: 0, vol: 0.22 } };
  var DEATH_SND = { maxR: 620, speed: 820, aud: { rate: 0.45, cut: 780,  hp: 55,  decay: 0.50, body: 58,  vol: 0.55 } };
  var PICK_SND  = { maxR: 200, speed: 900, aud: { rate: 2.40, cut: 6000, hp: 1200, decay: 0.06, body: 0,  vol: 0.30 } };

  // ---- music: one looping track, quieter under a match than on the menu ----
  var music = null;
  function startMusic() {
    if (music) { if (music.paused && musicLevel() > 0) music.play().catch(function () {}); return; }
    try {
      music = new Audio('assets/music.mp3');
      music.loop = true; music.volume = 0; music.preload = 'auto';
      music.play().catch(function () {});
    } catch (err) { music = null; }
  }
  function musicLevel() {
    if (muted) return 0;
    var inMatch = state === 'play' || state === 'paused' || state === 'ending';
    return clamp((SET.music / 100) * (SET.vol / 100) * (inMatch ? 0.5 : 1), 0, 1);
  }
  function musicTick() {
    if (!music) return;
    var want = musicLevel();
    music.volume = clamp(music.volume + (want - music.volume) * 0.06, 0, 1);
    if (want > 0 && music.paused) music.play().catch(function () {});
  }
  // browsers only allow sound after the player has done something
  ['pointerdown', 'keydown', 'touchstart'].forEach(function (t) {
    window.addEventListener(t, function () { startMusic(); }, { passive: true });
  });

  function initAudio() {
    startMusic();
    if (actx) { if (actx.state === 'suspended') actx.resume(); return; }
    try {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      actx = new AC();
      master = actx.createGain();
      master.gain.value = SET.vol / 100;
      // a firefight can stack a lot of voices at once - keep it off the rails
      if (actx.createDynamicsCompressor) {
        var comp = actx.createDynamicsCompressor();
        comp.threshold.value = -14;
        comp.ratio.value = 12;
        comp.attack.value = 0.003;
        comp.release.value = 0.2;
        master.connect(comp);
        comp.connect(actx.destination);
      } else master.connect(actx.destination);
      var len = Math.floor(actx.sampleRate * 0.8);
      noiseBuf = actx.createBuffer(1, len, actx.sampleRate);
      var d = noiseBuf.getChannelData(0);
      for (var i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      decodeSamples();
    } catch (err) { actx = null; }
  }

  function voice(a, when, gain, muffle, pan) {
    var out = master;
    if (actx.createStereoPanner) {
      var pn = actx.createStereoPanner();
      pn.pan.value = clamp(pan, -1, 1);
      pn.connect(master);
      out = pn;
    }
    var src = actx.createBufferSource();
    src.buffer = noiseBuf;
    src.playbackRate.value = a.rate;
    var hp = actx.createBiquadFilter();
    hp.type = 'highpass';
    hp.frequency.value = a.hp * (0.4 + 0.6 * muffle);
    var lp = actx.createBiquadFilter();
    lp.type = 'lowpass';
    var cut = Math.max(180, a.cut * muffle);
    lp.frequency.setValueAtTime(cut, when);
    lp.frequency.exponentialRampToValueAtTime(Math.max(140, cut * 0.3), when + a.decay);
    var g = actx.createGain();
    g.gain.setValueAtTime(0.0001, when);
    g.gain.linearRampToValueAtTime(gain, when + 0.004);
    g.gain.exponentialRampToValueAtTime(0.0001, when + a.decay);
    src.connect(hp); hp.connect(lp); lp.connect(g); g.connect(out);
    src.start(when);
    src.stop(when + a.decay + 0.06);
    if (a.body) {
      var o = actx.createOscillator();
      o.type = 'sine';
      o.frequency.setValueAtTime(a.body, when);
      o.frequency.exponentialRampToValueAtTime(a.body * 0.45, when + 0.14);
      var og = actx.createGain();
      og.gain.setValueAtTime(Math.max(0.0001, gain * 0.8 * muffle), when);
      og.gain.exponentialRampToValueAtTime(0.0001, when + 0.18);
      o.connect(og); og.connect(out);
      o.start(when); o.stop(when + 0.22);
    }
  }

  function audioEmit(x, y, def, owner) {
    if (netRole === 'host' && netHostLive()) netEv.push(['a', Math.round(x), Math.round(y), netDefId(def), owner]);
    if (!actx || muted || !player) return;
    if (!def.aud && !def.sample) return;
    // heard from your own spot if it is yours, else from the nearer player
    var oe = owner >= 0 ? ents[owner] : null;
    var lis = onHere(oe) ? oe : nearestLocal(x, y);
    var dx = x - lis.x, dy = y - lis.y;
    var d = Math.sqrt(dx * dx + dy * dy);
    if (d > def.maxR) return;
    var mine = onHere(oe);
    var fall = 1 - d / def.maxR;
    var gain = mine ? def.aud.vol * 0.9 : def.aud.vol * fall * fall;
    if (gain < 0.008) return;
    var muffle = 0.22 + 0.78 * fall;
    if (!mine && d > 4 && !lineClear(lis.x, lis.y, x, y)) muffle *= 0.4;
    var when = actx.currentTime + (mine ? 0 : d / def.speed);
    var pan = clamp(dx / 420, -1, 1) * 0.8;
    try {
      var buf = def.sample ? SFX_BUF[def.sample] : null;
      if (buf) {
        sampleVoice(buf, when, gain * (def.sampleGain || 1), muffle, pan, def.rate || 1);
      } else if (def.aud) {
        voice(def.aud, when, gain, muffle, pan);
        if (def.aud.twice) voice(def.aud, when + def.aud.twice, gain * 0.8, muffle, pan);
      }
    } catch (err) { /* an audio hiccup must never break the frame */ }
  }

  // ---------------------------------------------------------------- map
  var grid = new Uint8Array(STRIDE * STRIDE);
  var explored = new Uint8Array(STRIDE * STRIDE);
  var mat = new Uint8Array(STRIDE * STRIDE);   // 1 = built wall, 2 = bush / rock
  var curMat = 1;                              // material generators are laying down
  var floorTiles = [];
  var insideTiles = [];     // interior of buildings \u2014 where loot clusters
  var segs = [];

  function isWall(tx, ty) {
    if (tx < 0 || ty < 0 || tx >= MAP_W || ty >= MAP_H) return true;
    return grid[ty * STRIDE + tx] === 1;
  }
  function wallAt(wx, wy) { return isWall(Math.floor(wx / TILE), Math.floor(wy / TILE)); }
  function setT(x, y, v) {
    if (x < 1 || y < 1 || x >= MAP_W - 1 || y >= MAP_H - 1) return;
    grid[y * STRIDE + x] = v;
    mat[y * STRIDE + x] = v ? curMat : 0;
  }
  function carve(x, y) { setT(x, y, 0); }

  function finishMap() {
    floorTiles.length = 0;
    // anything set straight into the grid (borders) counts as built wall
    for (var mi = 0; mi < STRIDE * STRIDE; mi++) if (grid[mi] === 1 && mat[mi] === 0) mat[mi] = 1;
    for (var ty = 0; ty < MAP_H; ty++) for (var tx = 0; tx < MAP_W; tx++) {
      if (tx === 0 || ty === 0 || tx === MAP_W - 1 || ty === MAP_H - 1) grid[ty * STRIDE + tx] = 1;
      if (grid[ty * STRIDE + tx] === 0) floorTiles.push({ x: tx, y: ty });
    }
    WORLD_W = MAP_W * TILE; WORLD_H = MAP_H * TILE;
    buildSegments();
  }

  function genRooms(w, h, rmin, rmax, count, corrW, pillars) {
    MAP_W = w; MAP_H = h;
    grid.fill(1);
    mat.fill(0); curMat = 1;
    var rooms = [], i;
    for (i = 0; i < 500 && rooms.length < count; i++) {
      var rw = rmin + rnd(rmax - rmin), rh = rmin + rnd(rmax - rmin);
      var x = 2 + rnd(Math.max(1, MAP_W - rw - 4)), y = 2 + rnd(Math.max(1, MAP_H - rh - 4));
      var ok = true;
      for (var j = 0; j < rooms.length; j++) {
        var o = rooms[j];
        if (x - 2 < o.x + o.w && x + rw + 2 > o.x && y - 2 < o.y + o.h && y + rh + 2 > o.y) { ok = false; break; }
      }
      if (ok) rooms.push({ x: x, y: y, w: rw, h: rh });
    }
    rooms.forEach(function (r) {
      for (var yy = r.y; yy < r.y + r.h; yy++) for (var xx = r.x; xx < r.x + r.w; xx++) carve(xx, yy);
    });
    function cx(r) { return r.x + (r.w >> 1); }
    function cy(r) { return r.y + (r.h >> 1); }
    function corridor(ax, ay, bx, by) {
      var x, y, k;
      for (x = Math.min(ax, bx); x <= Math.max(ax, bx); x++) for (k = 0; k < corrW; k++) carve(x, ay + k);
      for (y = Math.min(ay, by); y <= Math.max(ay, by); y++) for (k = 0; k < corrW; k++) carve(bx + k, y);
    }
    for (i = 1; i < rooms.length; i++) corridor(cx(rooms[i - 1]), cy(rooms[i - 1]), cx(rooms[i]), cy(rooms[i]));
    for (i = 0; i < Math.round(rooms.length * 0.35); i++) {
      var a = rooms[rnd(rooms.length)], b = rooms[rnd(rooms.length)];
      corridor(cx(a), cy(a), cx(b), cy(b));
    }
    if (pillars) {
      rooms.forEach(function (r) {
        if (r.w < 9 || r.h < 9) return;
        var n = 1 + rnd(3);
        for (var m = 0; m < n; m++) {
          var px = r.x + 2 + rnd(r.w - 4), py = r.y + 2 + rnd(r.h - 4);
          setT(px, py, 1);
          if (Math.random() < 0.5) setT(px + 1, py, 1); else setT(px, py + 1, 1);
        }
      });
    }
    insideTiles.length = 0;
    finishMap();
  }

  // Open ground with scattered buildings - long sightlines, loot indoors.
  function genWorld(span) {
    span = Math.max(56, span || 158);
    MAP_W = span; MAP_H = span;
    grid.fill(0);
    mat.fill(0); curMat = 1;
    insideTiles.length = 0;
    var i, j, x, y;
    for (x = 0; x < MAP_W; x++) for (y = 0; y < 2; y++) {
      grid[y * STRIDE + x] = 1; grid[(MAP_H - 1 - y) * STRIDE + x] = 1;
    }
    for (y = 0; y < MAP_H; y++) for (x = 0; x < 2; x++) {
      grid[y * STRIDE + x] = 1; grid[y * STRIDE + (MAP_W - 1 - x)] = 1;
    }

    var builds = [];
    // a few towns' worth of buildings on a lot of open ground
    var wantBuilds = Math.max(5, Math.round(span * span / 1150));
    for (i = 0; i < 1400 && builds.length < wantBuilds; i++) {
      var bw = 7 + rnd(9), bh = 7 + rnd(9);
      var bx = 4 + rnd(MAP_W - bw - 8), by = 4 + rnd(MAP_H - bh - 8);
      var ok = true;
      for (j = 0; j < builds.length; j++) {
        var o = builds[j];
        if (bx - 12 < o.x + o.w && bx + bw + 12 > o.x && by - 12 < o.y + o.h && by + bh + 12 > o.y) { ok = false; break; }
      }
      if (!ok) continue;
      builds.push({ x: bx, y: by, w: bw, h: bh });
      for (x = bx; x < bx + bw; x++) { setT(x, by, 1); setT(x, by + bh - 1, 1); }
      for (y = by; y < by + bh; y++) { setT(bx, y, 1); setT(bx + bw - 1, y, 1); }
      // doorways
      var doors = 2 + rnd(2);
      for (var d = 0; d < doors; d++) {
        var side = rnd(4);
        if (side === 0) { var dx0 = bx + 1 + rnd(bw - 3); carve(dx0, by); carve(dx0 + 1, by); }
        else if (side === 1) { var dx1 = bx + 1 + rnd(bw - 3); carve(dx1, by + bh - 1); carve(dx1 + 1, by + bh - 1); }
        else if (side === 2) { var dy0 = by + 1 + rnd(bh - 3); carve(bx, dy0); carve(bx, dy0 + 1); }
        else { var dy1 = by + 1 + rnd(bh - 3); carve(bx + bw - 1, dy1); carve(bx + bw - 1, dy1 + 1); }
      }
      // interior partition for some buildings
      if (bw > 10 && bh > 10 && Math.random() < 0.6) {
        var mid = by + 2 + rnd(bh - 5);
        for (x = bx + 1; x < bx + bw - 1; x++) setT(x, mid, 1);
        var gap = bx + 1 + rnd(bw - 3);
        carve(gap, mid); carve(gap + 1, mid);
      }
      for (x = bx + 1; x < bx + bw - 1; x++) for (y = by + 1; y < by + bh - 1; y++) {
        if (grid[y * STRIDE + x] === 0) insideTiles.push({ x: x, y: y });
      }
    }

    // scattered cover out in the open - bushes and rocks, not masonry
    curMat = 2;
    var wantCover = Math.max(50, Math.round(span * span / 44));
    for (i = 0; i < wantCover; i++) {
      var cxx = 3 + rnd(MAP_W - 6), cyy = 3 + rnd(MAP_H - 6);
      var inside = false;
      for (j = 0; j < builds.length; j++) {
        var b = builds[j];
        if (cxx >= b.x - 2 && cxx <= b.x + b.w + 1 && cyy >= b.y - 2 && cyy <= b.y + b.h + 1) { inside = true; break; }
      }
      if (inside) continue;
      setT(cxx, cyy, 1);
      if (Math.random() < 0.45) setT(cxx + 1, cyy, 1);
      if (Math.random() < 0.25) setT(cxx, cyy + 1, 1);
    }
    curMat = 1;
    finishMap();
  }

  function genArena() {
    MAP_W = 44; MAP_H = 44;
    grid.fill(0);
    mat.fill(0); curMat = 1;
    insideTiles.length = 0;
    var x, y, i;
    for (x = 0; x < MAP_W; x++) for (y = 0; y < 2; y++) {
      grid[y * STRIDE + x] = 1; grid[(MAP_H - 1 - y) * STRIDE + x] = 1;
    }
    for (y = 0; y < MAP_H; y++) for (x = 0; x < 2; x++) {
      grid[y * STRIDE + x] = 1; grid[y * STRIDE + (MAP_W - 1 - x)] = 1;
    }
    // a few small structures plus loose cover
    for (i = 0; i < 6; i++) {
      var bw = 6 + rnd(6), bh = 6 + rnd(6);
      var bx = 4 + rnd(MAP_W - bw - 8), by = 4 + rnd(MAP_H - bh - 8);
      for (x = bx; x < bx + bw; x++) { setT(x, by, 1); setT(x, by + bh - 1, 1); }
      for (y = by; y < by + bh; y++) { setT(bx, y, 1); setT(bx + bw - 1, y, 1); }
      var dxr = bx + 1 + rnd(bw - 3); carve(dxr, by); carve(dxr + 1, by);
      var dyr = by + 1 + rnd(bh - 3); carve(bx + bw - 1, dyr); carve(bx + bw - 1, dyr + 1);
    }
    for (i = 0; i < 90; i++) {
      var px = 3 + rnd(MAP_W - 6), py = 3 + rnd(MAP_H - 6);
      setT(px, py, 1);
      if (Math.random() < 0.4) setT(px + 1, py, 1);
    }
    finishMap();
  }

  function buildSegments() {
    segs.length = 0;
    var x, y, run;
    for (x = 0; x <= MAP_W; x++) {
      run = -1;
      for (y = 0; y <= MAP_H; y++) {
        var edgeV = y < MAP_H && (isWall(x - 1, y) !== isWall(x, y));
        if (edgeV && run < 0) run = y;
        else if (!edgeV && run >= 0) { pushSeg(x * TILE, run * TILE, x * TILE, y * TILE); run = -1; }
      }
    }
    for (y = 0; y <= MAP_H; y++) {
      run = -1;
      for (x = 0; x <= MAP_W; x++) {
        var edgeH = x < MAP_W && (isWall(x, y - 1) !== isWall(x, y));
        if (edgeH && run < 0) run = x;
        else if (!edgeH && run >= 0) { pushSeg(run * TILE, y * TILE, x * TILE, y * TILE); run = -1; }
      }
    }
  }
  function pushSeg(ax, ay, bx, by) { segs.push({ ax: ax, ay: ay, bx: bx, by: by, ex: bx - ax, ey: by - ay }); }

  function segDist(px, py, s) {
    var vx = s.ex, vy = s.ey;
    var wx = px - s.ax, wy = py - s.ay;
    var len2 = vx * vx + vy * vy;
    var t = len2 > 0 ? clamp((wx * vx + wy * vy) / len2, 0, 1) : 0;
    var dx = s.ax + vx * t - px, dy = s.ay + vy * t - py;
    return Math.sqrt(dx * dx + dy * dy);
  }

  // ---------------------------------------------------------------- sight
  function lineClear(ax, ay, bx, by) {
    var dx = bx - ax, dy = by - ay;
    var d = Math.sqrt(dx * dx + dy * dy);
    if (d < 1) return true;
    var steps = Math.ceil(d / (TILE * 0.4));
    for (var i = 1; i < steps; i++) {
      var t = i / steps;
      if (wallAt(ax + dx * t, ay + dy * t)) return false;
    }
    return !wallAt(bx, by);
  }
  // How much of a line runs through smoke. Enough of it and you see nothing -
  // a glance into the edge of a cloud still works, straight through does not.
  function smokeBlocks(ax, ay, bx, by) {
    if (!smokes.length) return false;
    var dx = bx - ax, dy = by - ay;
    var len2 = dx * dx + dy * dy;
    if (len2 < 1) return false;
    var len = Math.sqrt(len2), total = 0;
    for (var i = 0; i < smokes.length; i++) {
      var sm = smokes[i];
      if (sm.r < 8 || sm.alpha < 0.3) continue;
      var fx = ax - sm.x, fy = ay - sm.y;
      var b2 = 2 * (fx * dx + fy * dy);
      var c2 = fx * fx + fy * fy - sm.r * sm.r;
      var disc = b2 * b2 - 4 * len2 * c2;
      if (disc <= 0) continue;
      disc = Math.sqrt(disc);
      var t1 = clamp((-b2 - disc) / (2 * len2), 0, 1);
      var t2 = clamp((-b2 + disc) / (2 * len2), 0, 1);
      total += (t2 - t1) * len;
      if (total > 52) return true;
    }
    return false;
  }
  // Walls stop movement and bullets; smoke only stops eyes.
  function sightClear(ax, ay, bx, by) {
    return lineClear(ax, ay, bx, by) && !smokeBlocks(ax, ay, bx, by);
  }

  // You see what is in front of you, plus a little circle right around you
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
    if (!inCone(player, x, y)) return false;
    var dx = x - player.x, dy = y - player.y;
    return dx * dx + dy * dy < VIEW_R * VIEW_R && sightClear(player.x, player.y, x, y);
  }
  function litVisible(x, y, reach) {
    if (!inCone(player, x, y)) return false;
    var dx = x - player.x, dy = y - player.y;
    return dx * dx + dy * dy < reach * reach && sightClear(player.x, player.y, x, y);
  }

  var nearSegs = [];
  function cullSegs(px, py, radius) {
    nearSegs.length = 0;
    for (var i = 0; i < segs.length; i++) {
      if (segDist(px, py, segs[i]) < radius + 10) nearSegs.push(segs[i]);
    }
  }
  function raySeg(px, py, dx, dy, s) {
    var det = s.ex * dy - dx * s.ey;
    if (det > -1e-9 && det < 1e-9) return -1;
    var qx = s.ax - px, qy = s.ay - py;
    var t1 = (s.ex * qy - s.ey * qx) / det;
    var t2 = (dx * qy - dy * qx) / det;
    if (t1 <= 0 || t2 < 0 || t2 > 1) return -1;
    return t1;
  }

  var visPts = [];
  var rayBuf = [];
  function computeVisibility(px, py, radius) {
    cullSegs(px, py, radius);
    rayBuf.length = 0;
    for (var i = 0; i < nearSegs.length; i++) {
      var s = nearSegs[i];
      var a1 = Math.atan2(s.ay - py, s.ax - px);
      var a2 = Math.atan2(s.by - py, s.bx - px);
      rayBuf.push(a1 - 0.00016, a1 + 0.00016, a2 - 0.00016, a2 + 0.00016);
    }
    var N = 64;
    for (var k = 0; k < N; k++) rayBuf.push(k / N * Math.PI * 2);
    rayBuf.sort(function (a, b) { return a - b; });
    visPts.length = 0;
    for (var r = 0; r < rayBuf.length; r++) {
      var ang = rayBuf[r];
      var dx = Math.cos(ang), dy = Math.sin(ang);
      var best = radius;
      for (var j = 0; j < nearSegs.length; j++) {
        var t = raySeg(px, py, dx, dy, nearSegs[j]);
        if (t > 0 && t < best) best = t;
      }
      visPts.push(px + dx * best, py + dy * best);
    }
    return visPts;
  }

  // World-map ground: packed dirt with mud streaks, moss clumps and loose
  // stone, on a faint tile grid. Painted once into a 208-unit (8 tile) square
  // that repeats seamlessly - every feature is also drawn at the eight
  // neighbouring offsets so nothing is cut off at the seam.
  var groundLit = null, groundDim = null;
  var GSZ = 208;

  function makeGround() {
    var c = document.createElement('canvas');
    c.width = c.height = GSZ;
    var g = c.getContext('2d');

    function wrap(fn) {                       // draw at all 9 offsets
      for (var ox = -1; ox <= 1; ox++) for (var oy = -1; oy <= 1; oy++) {
        g.save(); g.translate(ox * GSZ, oy * GSZ); fn(); g.restore();
      }
    }

    g.fillStyle = '#6d4c30';
    g.fillRect(0, 0, GSZ, GSZ);

    // broad tonal variation - pale dust and wet mud
    var i, x, y, r;
    for (i = 0; i < 90; i++) {
      x = Math.random() * GSZ; y = Math.random() * GSZ; r = rr(14, 62);
      var pale = Math.random() < 0.40;
      var col = pale ? '154,118,74' : '58,38,21';
      (function (x, y, r, col) {
        wrap(function () {
          var rg = g.createRadialGradient(x, y, 0, x, y, r);
          rg.addColorStop(0, 'rgba(' + col + ',' + rr(0.22, 0.46).toFixed(2) + ')');
          rg.addColorStop(1, 'rgba(' + col + ',0)');
          g.fillStyle = rg;
          g.beginPath(); g.arc(x, y, r, 0, 6.2832); g.fill();
        });
      })(x, y, r, col);
    }

    // dark streaks where water has run
    for (i = 0; i < 48; i++) {
      (function (x, y, a, w, h) {
        wrap(function () {
          g.save(); g.translate(x, y); g.rotate(a);
          g.fillStyle = 'rgba(48,30,16,' + rr(0.18, 0.38).toFixed(2) + ')';
          g.beginPath(); g.ellipse(0, 0, w, h, 0, 0, 6.2832); g.fill();
          g.restore();
        });
      })(Math.random() * GSZ, Math.random() * GSZ, Math.random() * 3.14, rr(12, 40), rr(2.5, 7));
    }

    // faint tile grid, one line per world tile
    wrap(function () {
      g.strokeStyle = 'rgba(38,24,12,.17)';
      g.lineWidth = 1;
      for (var k = 0; k <= GSZ; k += TILE) {
        g.beginPath(); g.moveTo(k + .5, 0); g.lineTo(k + .5, GSZ); g.stroke();
        g.beginPath(); g.moveTo(0, k + .5); g.lineTo(GSZ, k + .5); g.stroke();
      }
    });

    // moss and grass clumps
    var GREENS = ['#54652a', '#647431', '#3c4a1b', '#5b6b2c'];
    for (i = 0; i < 26; i++) {
      (function (cx, cy, spread, blades) {
        wrap(function () {
          var rg = g.createRadialGradient(cx, cy, 0, cx, cy, spread * 1.3);
          rg.addColorStop(0, 'rgba(74,88,40,.55)');
          rg.addColorStop(1, 'rgba(74,88,40,0)');
          g.fillStyle = rg;
          g.beginPath(); g.arc(cx, cy, spread * 1.3, 0, 6.2832); g.fill();
          for (var b = 0; b < blades; b++) {
            var a = Math.random() * 6.2832, d = Math.random() * spread;
            g.fillStyle = GREENS[rnd(GREENS.length)];
            g.fillRect(cx + Math.cos(a) * d, cy + Math.sin(a) * d, rr(1.1, 1.9), rr(2.0, 4.2));
          }
        });
      })(Math.random() * GSZ, Math.random() * GSZ, rr(9, 24), 11 + rnd(15));
    }

    // loose stone, some of it gathered into drifts
    function stone(x, y, rx) {
      wrap(function () {
        g.fillStyle = 'rgba(52,48,42,.5)';
        g.beginPath(); g.ellipse(x, y + rx * 0.35, rx * 1.05, rx * 0.72, 0, 0, 6.2832); g.fill();
        g.fillStyle = '#7d766c';
        g.beginPath(); g.ellipse(x, y, rx, rx * 0.78, 0, 0, 6.2832); g.fill();
        g.fillStyle = 'rgba(164,156,142,.55)';
        g.beginPath(); g.ellipse(x - rx * 0.2, y - rx * 0.26, rx * 0.5, rx * 0.32, 0, 0, 6.2832); g.fill();
      });
    }
    for (i = 0; i < 22; i++) stone(Math.random() * GSZ, Math.random() * GSZ, rr(1.8, 3.4));
    for (i = 0; i < 6; i++) {
      var dx = Math.random() * GSZ, dy = Math.random() * GSZ;
      for (var k2 = 0; k2 < 4 + rnd(5); k2++) {
        stone(dx + rr(-15, 15), dy + rr(-11, 11), rr(2.4, 5.0));
      }
    }

    // settle the whole thing down a touch so it sits in a dark game
    g.fillStyle = 'rgba(26,16,7,.16)';
    g.fillRect(0, 0, GSZ, GSZ);

    // the remembered-terrain copy is the same ground, most of the light taken out
    var d = document.createElement('canvas');
    d.width = d.height = GSZ;
    var dg = d.getContext('2d');
    dg.drawImage(c, 0, 0);
    dg.fillStyle = 'rgba(5,7,10,.82)';
    dg.fillRect(0, 0, GSZ, GSZ);

    groundLit = ctx.createPattern(c, 'repeat');
    groundDim = ctx.createPattern(d, 'repeat');
  }
  function buildTextures() { makeGround(); makeBlood(); makeFlash(); makeImpact(); makeMetal(); makeDeath(); }

  // ---- effect sheets -----------------------------------------------------
  // Every effect is a grid of frames: cols x rows, read left to right, top to
  // bottom. These are generated at boot so the game is complete on its own;
  // EARSHOT.loadFx('blood'|'flash'|'impact', {...}) swaps in real artwork.
  var FX = { blood: null, flash: null, impact: null, impact_metal: null, death: null };

  function fxSheet(canvas, cols, rows, fps, hold) {
    return {
      img: canvas, cols: cols, rows: rows, frames: cols * rows,
      fw: Math.floor(canvas.width / cols), fh: Math.floor(canvas.height / rows),
      fps: fps, hold: hold || 0
    };
  }
  function fxDraw(sh, idx, alpha) {          // caller has already transformed
    var sx = (idx % sh.cols) * sh.fw, sy = Math.floor(idx / sh.cols) * sh.fh;
    ctx.globalAlpha = alpha;
    ctx.drawImage(sh.img, sx, sy, sh.fw, sh.fh, 0, 0, sh.fw, sh.fh);
    ctx.globalAlpha = 1;
  }
  function loadFx(name, cfg) {
    var img = new Image();
    img.onload = function () {
      var cols = cfg.cols || cfg.frames || 8, rows = cfg.rows || 1;
      var src = cfg.chroma === false ? img : chromaKey(img, cfg.chromaTol || 40);
      var sh = fxSheet(src, cols, rows, cfg.fps || 20, cfg.hold || 0);
      if (cfg.frames) sh.frames = cfg.frames;
      // 'split' marks where a one-shot burst ends and a lasting stain begins
      if (cfg.split !== undefined) { sh.split = cfg.split; sh.poolFps = cfg.poolFps || 8; }
      FX[name] = sh;
    };
    img.src = cfg.src;
  }

  // Eight frames of one splatter opening up: the same droplets thrown further
  // each frame, so it reads as a single hit rather than eight random blots.
  function makeBlood() {
    var n = 8, S = 64;
    var c = document.createElement('canvas');
    c.width = S * n; c.height = S;
    var g = c.getContext('2d');
    var drops = [], i, f;
    for (i = 0; i < 22; i++) drops.push({ a: rr(-1, 1), d: rr(0.12, 1), r: rr(0.9, 3.4), hue: Math.random() });
    for (f = 0; f < n; f++) {
      var pr = (f + 1) / n;
      var cx = f * S + S * 0.36, cy = S * 0.5;
      g.save();
      g.beginPath(); g.rect(f * S, 0, S, S); g.clip();
      for (i = 0; i < 6; i++) {
        g.fillStyle = i % 2 ? 'rgba(122,16,20,.92)' : 'rgba(92,10,14,.92)';
        g.beginPath();
        g.arc(cx + rr(-3, 3) * pr, cy + rr(-3, 3) * pr, (2.2 + pr * 8.5) * rr(0.55, 1.05), 0, 6.2832);
        g.fill();
      }
      for (i = 0; i < drops.length; i++) {
        var d = drops[i];
        if (d.d > pr * 1.12) continue;
        var dist = d.d * pr * 26;
        g.fillStyle = d.hue < 0.5 ? 'rgba(136,18,22,.88)' : 'rgba(98,11,15,.88)';
        g.beginPath();
        g.ellipse(cx + Math.cos(d.a) * dist, cy + Math.sin(d.a) * dist * 0.75,
                  d.r * (0.6 + 0.5 * pr), d.r * (0.5 + 0.45 * pr), d.a, 0, 6.2832);
        g.fill();
      }
      if (pr > 0.55) {
        for (i = 0; i < 4; i++) {
          var sa = rr(-0.5, 0.5), sd = rr(0.5, 1) * pr * 30;
          g.save();
          g.translate(cx + Math.cos(sa) * sd, cy + Math.sin(sa) * sd * 0.8);
          g.rotate(sa);
          g.fillStyle = 'rgba(126,16,20,.75)';
          g.beginPath(); g.ellipse(0, 0, rr(3, 7) * pr, rr(0.6, 1.4), 0, 0, 6.2832); g.fill();
          g.restore();
        }
      }
      g.restore();
    }
    FX.blood = fxSheet(c, n, 1, 20, 11);
  }

  // Muzzle flash: a spark, a gold cone that flares and spikes, then smoke.
  // Frames run left to right with the barrel at the left edge.
  function makeFlash() {
    var n = 8, W = 72, H = 52;
    var c = document.createElement('canvas');
    c.width = W * n; c.height = H;
    var g = c.getContext('2d');
    // fixed puff layout so the smoke grows out of one burst rather than
    // flickering into a new shape every frame
    var puffs = [];
    for (var q = 0; q < 14; q++) {
      puffs.push({ a: rr(-0.75, 0.75), d: rr(0.25, 1), r: rr(2.2, 6.4), warm: Math.random() });
    }
    for (var f = 0; f < n; f++) {
      var t = f / (n - 1);
      var heat = Math.sin(Math.min(1, t * 1.35) * Math.PI);
      var ox = f * W, cy = H / 2, bx = ox + 4;
      g.save();
      g.beginPath(); g.rect(ox, 0, W, H); g.clip();

      if (heat > 0.02) {
        // the hot core, thrown forward from the muzzle
        var len = 8 + heat * 40, wid = 3 + heat * 13;
        var lg = g.createLinearGradient(bx, cy, bx + len, cy);
        lg.addColorStop(0, 'rgba(255,255,246,' + (0.98 * heat).toFixed(3) + ')');
        lg.addColorStop(0.28, 'rgba(255,226,130,' + (0.95 * heat).toFixed(3) + ')');
        lg.addColorStop(0.7, 'rgba(246,158,40,' + (0.7 * heat).toFixed(3) + ')');
        lg.addColorStop(1, 'rgba(214,110,20,0)');
        g.fillStyle = lg;
        g.beginPath();
        g.moveTo(bx, cy - wid * 0.5);
        g.quadraticCurveTo(bx + len * 0.5, cy - wid, bx + len, cy);
        g.quadraticCurveTo(bx + len * 0.5, cy + wid, bx, cy + wid * 0.5);
        g.closePath(); g.fill();

        // spikes: two long down the barrel line, four short across it
        g.strokeStyle = 'rgba(255,248,214,' + (0.9 * heat).toFixed(3) + ')';
        g.lineCap = 'round';
        g.lineWidth = 2.6 * heat;
        var spikes = [[1, 0, 1.25], [-1, 0, 0.3], [0, -1, 0.55], [0, 1, 0.55], [0.7, -0.7, 0.7], [0.7, 0.7, 0.7]];
        for (var k = 0; k < spikes.length; k++) {
          var sp = spikes[k];
          g.beginPath();
          g.moveTo(bx, cy);
          g.lineTo(bx + sp[0] * len * sp[2], cy + sp[1] * len * sp[2] * 0.62);
          g.stroke();
        }
        g.fillStyle = 'rgba(255,255,255,' + (0.95 * heat).toFixed(3) + ')';
        g.beginPath(); g.arc(bx + 2, cy, 2 + heat * 3.5, 0, 6.2832); g.fill();
      }

      // rolling smoke, opening up as the flash dies back
      var smoke = Math.max(0, (t - 0.12) / 0.88);
      if (smoke > 0) {
        for (var i = 0; i < puffs.length; i++) {
          var pf = puffs[i];
          if (pf.d > smoke * 1.15) continue;
          var dd = 10 + pf.d * smoke * 46;
          var fade = (1 - smoke * 0.72) * (pf.warm > 0.45 ? 0.85 : 0.6);
          g.fillStyle = pf.warm > 0.45
            ? 'rgba(214,116,36,' + fade.toFixed(3) + ')'
            : 'rgba(158,86,30,' + fade.toFixed(3) + ')';
          g.beginPath();
          g.arc(bx + Math.cos(pf.a) * dd, cy + Math.sin(pf.a) * dd * 0.8,
                pf.r * (0.55 + smoke * 0.8), 0, 6.2832);
          g.fill();
        }
      }
      g.restore();
    }
    FX.flash = fxSheet(c, n, 1, 44, 0);
  }

  // Wall impact: chunks of masonry thrown out of a dust puff, 3x3.
  function makeImpact() {
    var cols = 3, rows = 3, S = 48;
    var c = document.createElement('canvas');
    c.width = S * cols; c.height = S * rows;
    var g = c.getContext('2d');
    var bits = [], i;
    for (i = 0; i < 14; i++) bits.push({ a: Math.random() * 6.2832, d: rr(0.2, 1), r: rr(1.4, 4.2), tone: Math.random() });
    for (var f = 0; f < cols * rows; f++) {
      var pr = (f + 1) / (cols * rows);
      var ox = (f % cols) * S, oy = Math.floor(f / cols) * S;
      var cx = ox + S / 2, cy = oy + S / 2;
      var fade = pr < 0.55 ? 1 : 1 - (pr - 0.55) / 0.45;
      g.save();
      g.beginPath(); g.rect(ox, oy, S, S); g.clip();
      var dg = g.createRadialGradient(cx, cy, 0, cx, cy, 4 + pr * 17);
      dg.addColorStop(0, 'rgba(190,186,178,' + (0.42 * fade).toFixed(3) + ')');
      dg.addColorStop(1, 'rgba(160,156,148,0)');
      g.fillStyle = dg;
      g.beginPath(); g.arc(cx, cy, 4 + pr * 17, 0, 6.2832); g.fill();
      for (i = 0; i < bits.length; i++) {
        var b = bits[i];
        if (b.d > pr * 1.15) continue;
        var dd = b.d * pr * 17;
        g.fillStyle = b.tone < 0.4 ? 'rgba(96,92,86,' + fade.toFixed(3) + ')'
                    : (b.tone < 0.75 ? 'rgba(148,143,134,' + fade.toFixed(3) + ')'
                                     : 'rgba(198,193,184,' + fade.toFixed(3) + ')');
        g.save();
        g.translate(cx + Math.cos(b.a) * dd, cy + Math.sin(b.a) * dd);
        g.rotate(b.a * 2);
        g.beginPath();
        g.ellipse(0, 0, b.r * (1.05 - pr * 0.3), b.r * (0.75 - pr * 0.2), 0, 0, 6.2832);
        g.fill();
        g.restore();
      }
      g.restore();
    }
    FX.impact = fxSheet(c, cols, rows, 30, 0);
  }

  // Metal strike: a hot core that throws a burst of thin sparks, 3x3.
  function makeMetal() {
    var cols = 3, rows = 3, S = 48;
    var c = document.createElement('canvas');
    c.width = S * cols; c.height = S * rows;
    var g = c.getContext('2d');
    var rays = [], i;
    for (i = 0; i < 13; i++) rays.push({ a: Math.random() * 6.2832, len: rr(0.55, 1), w: rr(0.9, 2.1) });
    var motes = [];
    for (i = 0; i < 9; i++) motes.push({ a: Math.random() * 6.2832, d: rr(0.4, 1), r: rr(0.7, 1.6) });
    for (var f = 0; f < cols * rows; f++) {
      var pr = (f + 1) / (cols * rows);
      var ox = (f % cols) * S, oy = Math.floor(f / cols) * S;
      var cx = ox + S / 2, cy = oy + S / 2;
      var fade = pr < 0.35 ? 1 : Math.max(0, 1 - (pr - 0.35) / 0.65);
      g.save();
      g.beginPath(); g.rect(ox, oy, S, S); g.clip();
      if (pr < 0.5) {                                  // white-hot point of contact
        var cg = g.createRadialGradient(cx, cy, 0, cx, cy, 3 + pr * 9);
        cg.addColorStop(0, 'rgba(255,255,240,' + (0.95 * (1 - pr * 1.6)).toFixed(3) + ')');
        cg.addColorStop(1, 'rgba(255,214,110,0)');
        g.fillStyle = cg;
        g.beginPath(); g.arc(cx, cy, 3 + pr * 9, 0, 6.2832); g.fill();
      }
      g.lineCap = 'round';
      for (i = 0; i < rays.length; i++) {
        var ry = rays[i];
        var inner = pr * 4, outer = pr * 21 * ry.len;
        if (outer <= inner) continue;
        g.strokeStyle = (i % 3 === 0)
          ? 'rgba(255,253,236,' + (fade * 0.95).toFixed(3) + ')'
          : 'rgba(246,206,96,' + (fade * 0.85).toFixed(3) + ')';
        g.lineWidth = ry.w * (1.1 - pr * 0.5);
        g.beginPath();
        g.moveTo(cx + Math.cos(ry.a) * inner, cy + Math.sin(ry.a) * inner);
        g.lineTo(cx + Math.cos(ry.a) * outer, cy + Math.sin(ry.a) * outer);
        g.stroke();
      }
      for (i = 0; i < motes.length; i++) {             // stray sparks flying off
        var mo = motes[i];
        if (mo.d > pr * 1.2) continue;
        g.fillStyle = 'rgba(255,238,178,' + (fade * 0.9).toFixed(3) + ')';
        g.beginPath();
        g.arc(cx + Math.cos(mo.a) * mo.d * pr * 22, cy + Math.sin(mo.a) * mo.d * pr * 22, mo.r, 0, 6.2832);
        g.fill();
      }
      g.restore();
    }
    FX.impact_metal = fxSheet(c, cols, rows, 30, 0);
  }

  // Death: seven frames of arterial spray, then five of the pool spreading
  // underneath. The last frame is a stain that stays for the rest of the match.
  function makeDeath() {
    var n = 12, split = 7, S = 64;
    var c = document.createElement('canvas');
    c.width = S * n; c.height = S;
    var g = c.getContext('2d');
    var jets = [], i, f;
    for (i = 0; i < 16; i++) jets.push({ a: rr(-1.15, 1.15), d: rr(0.3, 1), r: rr(1.1, 3.2) });
    for (f = 0; f < split; f++) {
      var pr = f / (split - 1);
      var reach = Math.sin(Math.min(1, pr * 1.15) * Math.PI * 0.85);   // out, then down
      var cx = f * S + S / 2, cy = S / 2;
      g.save();
      g.beginPath(); g.rect(f * S, 0, S, S); g.clip();
      g.fillStyle = 'rgba(112,13,17,.95)';
      g.beginPath();
      g.ellipse(cx, cy, 2.5 + pr * 7, 2 + pr * 5, 0, 0, 6.2832);
      g.fill();
      for (i = 0; i < jets.length; i++) {
        var j = jets[i];
        if (j.d > pr * 1.25) continue;
        var dd = j.d * reach * 25;
        g.fillStyle = i % 3 === 0 ? 'rgba(146,20,24,.9)' : 'rgba(104,12,16,.92)';
        g.save();
        g.translate(cx + Math.cos(j.a - 1.57) * dd * 0.55, cy + Math.sin(j.a - 1.57) * dd);
        g.rotate(j.a);
        g.beginPath();
        g.ellipse(0, 0, j.r * (0.7 + reach * 0.6), j.r * (0.9 + reach * 0.9), 0, 0, 6.2832);
        g.fill();
        g.restore();
      }
      g.restore();
    }
    for (f = split; f < n; f++) {
      var q = (f - split) / (n - split - 1);
      var px2 = f * S + S / 2, py2 = S / 2;
      g.save();
      g.beginPath(); g.rect(f * S, 0, S, S); g.clip();
      for (i = 0; i < 5; i++) {
        g.fillStyle = i % 2 ? 'rgba(104,12,16,.94)' : 'rgba(86,9,13,.94)';
        g.beginPath();
        g.ellipse(px2 + rr(-3, 3) * q, py2 + rr(-2, 2) * q,
                  (7 + q * 19) * rr(0.82, 1.06), (4.5 + q * 11) * rr(0.82, 1.06), rr(-0.3, 0.3), 0, 6.2832);
        g.fill();
      }
      for (i = 0; i < 4; i++) {             // a few drops flung clear of the pool
        var sa2 = Math.random() * 6.2832, sd2 = (10 + q * 20) * rr(0.9, 1.4);
        g.fillStyle = 'rgba(112,13,17,.8)';
        g.beginPath();
        g.ellipse(px2 + Math.cos(sa2) * sd2, py2 + Math.sin(sa2) * sd2 * 0.6, rr(0.8, 2.2), rr(0.7, 1.7), 0, 0, 6.2832);
        g.fill();
      }
      g.restore();
    }
    FX.death = fxSheet(c, n, 1, 16, 0);
    FX.death.split = split;
    FX.death.poolFps = 9;
  }

  // Fill one class of tile in one path. wantMat 0 means "any material".
  function tilePass(r0, r1, t0, t1, needExplored, wantSolid, wantMat, style) {
    ctx.beginPath();
    for (var ty = r0; ty <= r1; ty++) for (var tx = t0; tx <= t1; tx++) {
      var i = ty * STRIDE + tx;
      if (needExplored && !explored[i]) continue;
      if ((grid[i] === 1) !== wantSolid) continue;
      if (wantSolid && wantMat && mat[i] !== wantMat) continue;
      ctx.rect(tx * TILE, ty * TILE, TILE, TILE);
    }
    ctx.fillStyle = style;
    ctx.fill();
  }

  var exploreTick = 0;
  function markExplored(px, py) {
    var step = TILE * 0.55;
    for (var i = 0; i < visPts.length; i += 2) {
      var dx = visPts[i] - px, dy = visPts[i + 1] - py;
      var d = Math.sqrt(dx * dx + dy * dy);
      var n = Math.ceil(d / step);
      if (n < 1) continue;
      var ux = dx / n, uy = dy / n;
      for (var k = 0; k <= n; k++) {
        var tx = Math.floor((px + ux * k) / TILE), ty = Math.floor((py + uy * k) / TILE);
        if (tx >= 0 && ty >= 0 && tx < MAP_W && ty < MAP_H) explored[ty * STRIDE + tx] = 1;
      }
    }
  }

  // ---------------------------------------------------------------- pathing
  function Heap() { this.n = []; this.p = []; }
  Heap.prototype.push = function (node, pri) {
    var n = this.n, p = this.p, i = n.length;
    n.push(node); p.push(pri);
    while (i > 0) {
      var par = (i - 1) >> 1;
      if (p[par] <= p[i]) break;
      var tn = n[i]; n[i] = n[par]; n[par] = tn;
      var tp = p[i]; p[i] = p[par]; p[par] = tp;
      i = par;
    }
  };
  Heap.prototype.pop = function () {
    var n = this.n, p = this.p, top = n[0];
    var ln = n.pop(), lp = p.pop();
    if (n.length) {
      n[0] = ln; p[0] = lp;
      var i = 0;
      for (;;) {
        var l = 2 * i + 1, r = l + 1, s = i;
        if (l < n.length && p[l] < p[s]) s = l;
        if (r < n.length && p[r] < p[s]) s = r;
        if (s === i) break;
        var tn = n[i]; n[i] = n[s]; n[s] = tn;
        var tp = p[i]; p[i] = p[s]; p[s] = tp;
        i = s;
      }
    }
    return top;
  };

  var gScore = new Float64Array(STRIDE * STRIDE);
  var cameFrom = new Int32Array(STRIDE * STRIDE);
  var seenStamp = new Int32Array(STRIDE * STRIDE);
  var doneStamp = new Int32Array(STRIDE * STRIDE);
  var stamp = 0;
  var DX = [1, -1, 0, 0, 1, 1, -1, -1];
  var DY = [0, 0, 1, -1, 1, -1, 1, -1];

  function nearestFloor(tx, ty) {
    if (!isWall(tx, ty)) return { x: tx, y: ty };
    for (var r = 1; r < 8; r++) {
      for (var dy = -r; dy <= r; dy++) for (var dx = -r; dx <= r; dx++) {
        if (Math.abs(dx) !== r && Math.abs(dy) !== r) continue;
        if (!isWall(tx + dx, ty + dy)) return { x: tx + dx, y: ty + dy };
      }
    }
    return null;
  }

  function findPath(sx, sy, tx, ty) {
    var goalT = nearestFloor(tx, ty), startT = nearestFloor(sx, sy);
    if (!goalT || !startT) return null;
    sx = startT.x; sy = startT.y; tx = goalT.x; ty = goalT.y;
    if (sx === tx && sy === ty) return [];
    stamp++;
    var start = sy * STRIDE + sx, goal = ty * STRIDE + tx;
    var open = new Heap();
    gScore[start] = 0; cameFrom[start] = -1; seenStamp[start] = stamp;
    open.push(start, 0);
    var expanded = 0;

    function rebuild(node) {
      var out = [];
      while (node !== -1) {
        out.push({ x: (node % STRIDE) * TILE + TILE / 2, y: Math.floor(node / STRIDE) * TILE + TILE / 2 });
        node = cameFrom[node];
      }
      out.reverse();
      return out;
    }

    var bestNode = start;
    var bx0 = Math.abs(sx - tx), by0 = Math.abs(sy - ty);
    var bestH = (bx0 > by0) ? bx0 + 0.4142 * by0 : by0 + 0.4142 * bx0;

    while (open.n.length && expanded < 26000) {
      var cur = open.pop();
      if (doneStamp[cur] === stamp) continue;
      doneStamp[cur] = stamp;
      expanded++;
      if (cur === goal) return rebuild(cur);
      var ccx = cur % STRIDE, ccy = Math.floor(cur / STRIDE);
      var chx = Math.abs(ccx - tx), chy = Math.abs(ccy - ty);
      var ch2 = (chx > chy) ? chx + 0.4142 * chy : chy + 0.4142 * chx;
      if (ch2 < bestH) { bestH = ch2; bestNode = cur; }
      for (var d = 0; d < 8; d++) {
        var nx = ccx + DX[d], ny = ccy + DY[d];
        if (isWall(nx, ny)) continue;
        if (d >= 4 && (isWall(ccx + DX[d], ccy) || isWall(ccx, ccy + DY[d]))) continue;
        var ni = ny * STRIDE + nx;
        if (doneStamp[ni] === stamp) continue;
        var ng = gScore[cur] + (d >= 4 ? 1.4142 : 1);
        if (seenStamp[ni] !== stamp || ng < gScore[ni]) {
          seenStamp[ni] = stamp; gScore[ni] = ng; cameFrom[ni] = cur;
          var hx = Math.abs(nx - tx), hy = Math.abs(ny - ty);
          open.push(ni, ng + ((hx > hy) ? hx + 0.4142 * hy : hy + 0.4142 * hx));
        }
      }
    }
    // out of budget or walled off: go as far toward it as we got
    return bestNode !== start ? rebuild(bestNode) : null;
  }

  // ---------------------------------------------------------------- state
  var state = 'menu';
  var difficulty = 1, mode = 'br', mapKind = 'cqb', blackout = false, squad = 1;
  var botFill = 1;                   // share of the usual bot count: 1, 0.5 or 0.25
  // Everyone starts in plain grey; credits come from playing and buy the rest.
  var BASE_SKIN = 9;
  var WALLET = { coins: 0, owned: [BASE_SKIN], skin: BASE_SKIN };
  var CG_MODE = window.DEAD_ANGLE_PLATFORM === 'crazygames';
  var CG = null;                          // the CrazyGames SDK, once it is ready
  function storeGet(k) {
    try {
      if (CG && CG.data) { var v = CG.data.getItem(k); if (v !== null && v !== undefined) return v; }
      return localStorage.getItem(k);
    } catch (err) { return null; }
  }
  function storeSet(k, v) {
    try { if (CG && CG.data) CG.data.setItem(k, v); } catch (err) {}
    try { localStorage.setItem(k, v); } catch (err) {}
  }
  function loadWallet() {
    try {
      var raw = storeGet('earshot.wallet');
      if (raw) {
        var w = JSON.parse(raw);
        if (w && w.owned && w.owned.length) {
          WALLET = { coins: w.coins | 0, owned: w.owned, skin: w.skin | 0 };
          if (WALLET.owned.indexOf(WALLET.skin) < 0) WALLET.skin = BASE_SKIN;
        }
      }
    } catch (err) { /* private window or blocked storage - stay on the default */ }
  }
  function saveWallet() {
    storeSet('earshot.wallet', JSON.stringify(WALLET));
    if (typeof cloudWallet === 'function') cloudWallet();
  }
  function skinPrice(i) { return i === BASE_SKIN ? 0 : (i >= 12 ? 500 : 200); }

  var SET = { vol: 66, music: 45, dead: 18, shake: true, minimap: true, blood: true };
  function loadSettings() {
    try {
      var raw = storeGet('earshot.settings');
      if (raw) {
        var v = JSON.parse(raw);
        if (v) for (var k in SET) if (v[k] !== undefined) SET[k] = v[k];
      }
    } catch (err) { /* blocked storage: keep the defaults */ }
  }
  function saveSettings() {
    storeSet('earshot.settings', JSON.stringify(SET));
    if (master) master.gain.value = SET.vol / 100;
  }
  function skinOwned(i) { return WALLET.owned.indexOf(i) >= 0; }
  var fieldN = 10;                 // how many fighters this match actually has
  var MODE = MODES.br;
  var ents = [], bullets = [], sounds = [], parts = [], flashes = [], corpses = [], loot = [];
  var decals = [], impacts = [], deaths = [], nades = [], flags = [], smokes = [], sectors = [], secTick = 0;
  var zombClock = 0, zombSpawnT = 0;
  var teamNadeT = [0, 0];            // a whole side shares one throwing window
  var botFrags = 0;                  // thrown by bots this match, for tuning
  var botShots = 0, targetSwaps = 0; // diagnostics
  var botHits = 0, aimErrOn = true, botHitsOnYou = 0;
  var godMode = false;               // testing only: the player cannot be hurt
  var matchToken = 0;                // bumps every match, so stale timers can tell
  var hitCause = 'gun', killCauses = {};
  var ZOMB_CAP = 14;

  function zombiesUp() {
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
  }
  var player = null, zone = null;
  // Everyone playing on this machine. One normally; two in split screen, where
  // each owns a device and a slice of the screen.
  var locals = [], splitOn = false, splitWant = false;
  // online: netRole is 'host' or 'guest' while connected; netGuest is true
  // while this machine is drawing a match the host is running
  var netRole = null, netConn = null, netPeer = null, netGuest = false, netGuestPaused = false;
  // host side: everyone connected to us. { conn, name, skin, uid, party, in, ent, sigs }
  var netGuests = [], netPublic = false, netCode = '';
  var acctName = '';                 // the signed-in username, if any
  var NET_MAX = 8;                   // people in one match, host included
  // on this machine (not merely human - remote guests are local to the host's sim)
  function onHere(e) { return !!(e && e.local && !(e.ctl && e.ctl.net)); }
  var netGuestSkin = 0, netHostHeld = false;
  // The drop plane: a straight run across the map. Everyone rides it at the
  // start of a battle royale and bails out somewhere along the way.
  var plane = null;
  var PLANE_SPEED = 360, GLIDE_SPEED = 235, CHUTE_TIME = 3.2;
  var VX = 0, VY = 0, VW = 0, VH = 0;       // the viewport being drawn into
  // two people on one screen, on opposite sides
  function splitVs() { return splitOn && locals.length > 1 && locals[0].team !== locals[1].team; }
  function anyLocalAlive() {
    for (var i = 0; i < locals.length; i++) if (locals[i].alive) return true;
    return false;
  }
  function kbPlayer() {
    for (var i = 0; i < locals.length; i++) if (locals[i].ctl && locals[i].ctl.kb) return locals[i];
    return player;
  }
  function nearestLocal(x, y) {
    var best = player, bd = 1e18;
    for (var i = 0; i < locals.length; i++) {
      if (!onHere(locals[i])) continue;
      var L = locals[i], d = (L.x - x) * (L.x - x) + (L.y - y) * (L.y - y);
      if (d < bd) { bd = d; best = L; }
    }
    return best;
  }
  // Which pads to hand out: two pads -> one each; one pad -> P1 keeps the
  // keyboard and mouse, P2 takes the pad. No pads, no split.
  function padIndices() {
    var l = navigator.getGamepads ? navigator.getGamepads() : null, out = [];
    if (l) for (var i = 0; i < l.length; i++) if (l[i] && l[i].connected) out.push(i);
    return out;
  }
  function splitControls() {
    var p = padIndices();
    if (p.length >= 2) return { p1: p[0], p2: p[1] };
    if (p.length === 1) return { p1: -1, p2: p[0] };
    return null;
  }
  var alive = 10, matchTime = 0, shots = 0, hits = 0, kills = 0;
  var score = [0, 0], round = 1, roundBreak = 0, roundClock = 0;
  var result = null, overCause = '';
  var lastWinner = null;              // who closed out a free-for-all
  var dmgMarks = [], shake = 0;
  var cam = { x: 0, y: 0 };
  var mouse = { sx: 0, sy: 0, wx: 0, wy: 0, down: false };
  var keys = {};
  var sticks = { move: null, aim: null };
  var touchMode = false;
  var promptItem = null;

  function makeEnt(tile, isPlayer, name) {
    return {
      id: ents.length, name: name, bot: !isPlayer, alive: true,
      x: tile.x * TILE + TILE / 2, y: tile.y * TILE + TILE / 2, r: 8.5,
      vx: 0, vy: 0, px: 0, py: 0,
      hp: 100, ang: Math.random() * Math.PI * 2,
      slots: [null, null], slot: 0, reserve: START_RESERVE, meds: 0, nades: 0, smokes: 0, level: 0,
      fireT: 0, reloadT: 0, stepT: 0, useT: 0, respawnT: 0, meleeT: 0, swingT: 0, throwT: 0,
      path: null, pathI: 0, repathT: 0, lootGoal: null,
      target: null, lostT: 0, reactT: 0, burst: 0, holdT: 0,
      alertX: 0, alertY: 0, alertT: 0,
      strafe: Math.random() < 0.5 ? 1 : -1, strafeT: rr(0.6, 1.6),
      senseT: Math.random() * 0.2, stuckT: 0, lastX: 0, lastY: 0, swapT: 0,
      nadeT: rr(3, 9), smokeT: rr(5, 14), skip: {},
      animT: Math.random(), animFire: 0, moving: false,
      _spd: 0, kills: 0, skin: 0, team: 0, down: false, downT: 0, revT: 0
    };
  }
  function curSlot(e) { return e.slots[e.slot]; }
  function foes(a, b) { return a.team !== b.team; }
  function isZombie(e) { return !!(MODE.zombies && e.team === 1); }
  // Which of the two carried guns suits this range: shotguns fall off hard,
  // snipers are clumsy in a corridor, an empty magazine is worth little.
  function bestSlotFor(e, d) {
    var best = e.slot, bestScore = -1;
    for (var i = 0; i < 2; i++) {
      var s = e.slots[i];
      if (!s) continue;
      var w = WEAPONS[s.key];
      var eff = w.dmg * w.pellets / w.interval;
      if (w.pellets > 1) eff *= d < 220 ? 1.7 : 0.25;
      else if (w.interval > 0.4) eff *= d > 380 ? 1.5 : 0.55;
      if (s.ammo === 0) eff *= 0.2;
      if (eff > bestScore) { bestScore = eff; best = i; }
    }
    return best;
  }
  function curW(e) { var s = e.slots[e.slot]; return s ? WEAPONS[s.key] : null; }

  // ---------------------------------------------------------------- loot
  function addLoot(tx, ty, type, key, n) {
    loot.push({
      x: tx * TILE + TILE / 2 + rr(-5, 5), y: ty * TILE + TILE / 2 + rr(-5, 5),
      type: type, key: key || null, spin: rr(0, 6.2832),
      ammo: type === 'gun' ? WEAPONS[key].mag : 0, n: n || 0, seen: false
    });
  }
  function spawnLoot(spawnTiles) {
    loot.length = 0;
    if (!MODE.loot) return;
    var acreage = floorTiles.length;
    var counts = {
      gun: Math.max(24, Math.round(acreage / 72)),
      ammo: Math.max(36, Math.round(acreage / 46)),
      med: Math.max(14, Math.round(acreage / 118))
    };
    // guarantee a weapon within a short sprint of every drop point
    spawnTiles.forEach(function (st) {
      for (var tries = 0; tries < 260; tries++) {
        var t = floorTiles[rnd(floorTiles.length)];
        var d = Math.sqrt((t.x - st.x) * (t.x - st.x) + (t.y - st.y) * (t.y - st.y));
        if (d > 3 && d < 10) { addLoot(t.x, t.y, 'gun', Math.random() < 0.55 ? 'pistol' : rollWeapon()); return; }
      }
    });
    function spot() {
      // on the world map, most loot sits inside the buildings
      if (insideTiles.length && Math.random() < 0.5) return insideTiles[rnd(insideTiles.length)];
      return floorTiles[rnd(floorTiles.length)];
    }
    var i, t2;
    for (i = 0; i < counts.gun; i++) { t2 = spot(); addLoot(t2.x, t2.y, 'gun', rollWeapon()); }
    for (i = 0; i < counts.ammo; i++) { t2 = spot(); addLoot(t2.x, t2.y, 'ammo', null, 30); }
    for (i = 0; i < counts.med; i++) { t2 = spot(); addLoot(t2.x, t2.y, 'med', null, 1); }
    for (i = 0; i < Math.round(counts.med * 0.8); i++) { t2 = spot(); addLoot(t2.x, t2.y, 'nade', null, 1); }
    for (i = 0; i < Math.round(counts.med * 0.7); i++) { t2 = spot(); addLoot(t2.x, t2.y, 'smoke', null, 1); }
  }

  function takeGun(e, it, idx) {
    var empty = e.slots[0] === null ? 0 : (e.slots[1] === null ? 1 : -1);
    if (empty >= 0) { e.slots[empty] = { key: it.key, ammo: it.ammo }; e.slot = empty; }
    else {
      var old = e.slots[e.slot];
      e.slots[e.slot] = { key: it.key, ammo: it.ammo };
      loot.push({ x: e.x, y: e.y, type: 'gun', key: old.key, ammo: old.ammo, n: 0, seen: true });
    }
    loot.splice(idx, 1);
    e.reloadT = 0;
    if (e === player) { feed('picked up <b>' + WEAPONS[it.key].name + '</b>', true); audioEmit(e.x, e.y, PICK_SND, e.id); }
  }
  function autoPickup(e) {
    if (isZombie(e)) return;                  // the infected carry nothing
    for (var i = loot.length - 1; i >= 0; i--) {
      var it = loot[i];
      var dx = it.x - e.x, dy = it.y - e.y;
      if (dx * dx + dy * dy > 22 * 22) continue;
      if (it.type === 'ammo') {
        if (e.reserve < RESERVE_MAX) { e.reserve = Math.min(RESERVE_MAX, e.reserve + it.n); loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }
      } else if (it.type === 'med') {
        if (e.meds < 3) { e.meds++; loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }
      } else if (it.type === 'nade') {
        if (e.nades < 3) { e.nades++; loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }
      } else if (it.type === 'smoke') {
        if (e.smokes < 3) { e.smokes++; loot.splice(i, 1); if (e === player) audioEmit(e.x, e.y, PICK_SND, e.id); }
      } else if (it.type === 'gun' && e.bot && !isZombie(e)) {
        var empty = e.slots[0] === null || e.slots[1] === null;
        if (empty || gunScore(it.key) > gunScore(curSlot(e).key) * 1.15) takeGun(e, it, i);
      }
    }
  }
  function nearestLoot(e, type, range) {
    var best = null, bestD = range * range;
    for (var i = 0; i < loot.length; i++) {
      var it = loot[i];
      if (it.type !== type) continue;
      var dx = it.x - e.x, dy = it.y - e.y, d2 = dx * dx + dy * dy;
      if (d2 < bestD) { bestD = d2; best = it; }
    }
    return best;
  }

  // ---------------------------------------------------------------- spawning
  function pickSpawns(n) {
    var cands = floorTiles.slice();
    if (MODE.zone && zone) {
      var filtered = cands.filter(function (t) {
        var dx = t.x * TILE - zone.cx, dy = t.y * TILE - zone.cy;
        return Math.sqrt(dx * dx + dy * dy) < zone.r * 0.82;
      });
      if (filtered.length >= n) cands = filtered;
    }
    shuffle(cands);
    for (var minD = Math.min(30, Math.floor(MAP_W * 0.45)); minD >= 3; minD -= 3) {
      var out = [];
      for (var i = 0; i < cands.length; i++) {
        var t = cands[i], ok = true;
        for (var j = 0; j < out.length; j++) {
          var dx = out[j].x - t.x, dy = out[j].y - t.y;
          if (Math.sqrt(dx * dx + dy * dy) < minD) { ok = false; break; }
        }
        if (ok) out.push(t);
        if (out.length === n) return out;
      }
    }
    return cands.slice(0, n);
  }
  function pickRespawnTile(e) {
    var best = null, bestScore = -1e9;
    for (var i = 0; i < 48; i++) {
      var t = floorTiles[rnd(floorTiles.length)];
      var wx = t.x * TILE, wy = t.y * TILE, minD = 1e9, friend = 1e9;
      for (var j = 0; j < ents.length; j++) {
        var o = ents[j];
        if (o === e || !o.alive) continue;
        var dx = o.x - wx, dy = o.y - wy;
        var d = Math.sqrt(dx * dx + dy * dy);
        if (foes(e, o)) minD = Math.min(minD, d);
        else friend = Math.min(friend, d);
      }
      // far from the other side, but not stranded from your own
      var sc = minD - (friend < 1e8 ? friend * 0.25 : 0);
      if (sc > bestScore) { bestScore = sc; best = t; }
    }
    return best || floorTiles[0];
  }

  // Squads land together: one anchor per squad, members a step apart.
  function squadSpawns(nTeams, per) {
    var anchors = pickSpawns(nTeams), out = [];
    for (var i = 0; i < nTeams; i++) {
      var a = anchors[i % anchors.length];
      for (var k = 0; k < per; k++) {
        var t = a;
        for (var tries = 0; tries < 30; tries++) {
          var cx2 = a.x + rnd(5) - 2, cy2 = a.y + rnd(5) - 2;
          if (!isWall(cx2, cy2)) { t = { x: cx2, y: cy2 }; break; }
        }
        out.push(t);
      }
    }
    return out;
  }

  // Two anchors as far apart as the map allows, one per side.
  function teamSpawns(n) {
    var a = floorTiles[rnd(floorTiles.length)], b = a, far = -1, i, t, d;
    for (i = 0; i < floorTiles.length; i += 3) {
      t = floorTiles[i];
      d = (t.x - a.x) * (t.x - a.x) + (t.y - a.y) * (t.y - a.y);
      if (d > far) { far = d; b = t; }
    }
    far = -1;
    for (i = 0; i < floorTiles.length; i += 3) {
      t = floorTiles[i];
      d = (t.x - b.x) * (t.x - b.x) + (t.y - b.y) * (t.y - b.y);
      if (d > far) { far = d; a = t; }
    }
    function near(anchor, count) {
      var pool = floorTiles.slice().sort(function (p, q) {
        return ((p.x - anchor.x) * (p.x - anchor.x) + (p.y - anchor.y) * (p.y - anchor.y)) -
               ((q.x - anchor.x) * (q.x - anchor.x) + (q.y - anchor.y) * (q.y - anchor.y));
      });
      var out = [];
      for (var k = 0; k < pool.length && out.length < count; k++) {
        var ok = true;
        for (var m = 0; m < out.length; m++) {
          var ddx = out[m].x - pool[k].x, ddy = out[m].y - pool[k].y;
          if (ddx * ddx + ddy * ddy < 16) { ok = false; break; }
        }
        if (ok) out.push(pool[k]);
      }
      return out;
    }
    var half = n >> 1;
    return near(a, half).concat(near(b, n - half));
  }

  function giveLoadout(e) {
    if (mode === 'tut') {
      e.slots = [e.dummy ? null : { key: 'pistol', ammo: WEAPONS.pistol.mag }, null];
      e.slot = 0; e.reserve = e.dummy ? 0 : 90; e.meds = 0; e.nades = 0; e.smokes = 0;
      return;
    }
    if (mode === 'gun') {
      var key = LADDER[Math.min(e.level, LADDER.length - 1)];
      e.slots = [{ key: key, ammo: WEAPONS[key].mag }, null];
      e.slot = 0; e.reserve = 9999; e.meds = 0; e.nades = 1; e.smokes = 0;
    } else if (MODE.zombies && e.team === 1) {
      e.slots = [null, null]; e.slot = 0; e.reserve = 0;
      e.meds = 0; e.nades = 0; e.smokes = 0;
      e.skin = ZOMBIE_SKIN;
    } else if (MODE.teams) {
      var prim = ['shotgun', 'rifle', 'silenced'][rnd(3)];
      e.slots = [{ key: prim, ammo: WEAPONS[prim].mag }, { key: 'pistol', ammo: WEAPONS.pistol.mag }];
      e.slot = 0; e.reserve = 140; e.meds = 1; e.nades = 2; e.smokes = 1;
    } else if (mode === 'duel') {
      e.slots = [{ key: 'rifle', ammo: WEAPONS.rifle.mag }, { key: 'pistol', ammo: WEAPONS.pistol.mag }];
      e.slot = 0; e.reserve = 120; e.meds = 1; e.nades = 2; e.smokes = 1;
    } else {
      e.slots = [null, null]; e.slot = 0; e.reserve = START_RESERVE; e.meds = 0; e.nades = 0; e.smokes = 0;
    }
  }
  function placeEnt(e, tile) {
    e.x = tile.x * TILE + TILE / 2; e.y = tile.y * TILE + TILE / 2;
    e.px = e.x; e.py = e.y; e.vx = 0; e.vy = 0;
    e.hp = (MODE.zombies && e.team === 1) ? 38 : 100;
    e.alive = true; e.respawnT = 0; e.bleeding = false;
    e.fireT = 0; e.reloadT = 0; e.useT = 0; e.stepT = 0;
    e.down = false; e.downT = 0; e.revT = 0;
    e.target = null; e.path = null; e.pathI = 0; e.repathT = 0;
    e.alertT = 0; e.lostT = 0; e.reactT = 0; e.burst = 0; e.holdT = 0;
    e.lootGoal = null; e.lastX = e.x; e.lastY = e.y; e.stuckT = 0;
    giveLoadout(e);
    if (e.local && e.cam) { e.cam.x = e.x; e.cam.y = e.y; }
    if (e === player) {
      cam.x = e.x; cam.y = e.y;
      mouse.wx = e.x + Math.cos(e.ang) * 100;
      mouse.wy = e.y + Math.sin(e.ang) * 100;
    }
  }
  function respawn(e) { placeEnt(e, pickRespawnTile(e)); }

  // ---------------------------------------------------------------- match
  function startMatch() {
    initAudio();
    matchToken++;
    MODE = MODES[mode];
    VIEW_R = blackout ? VIEW_BLACKOUT : VIEW_BASE;
    var FOOTPRINT = {
      duel: 52, gun: 96, team: 118, war: 156, ctf: 126, sect: 122, zomb: 112, br: 224
    };
    var span = FOOTPRINT[mode] || 118;
    if (mapKind === 'world' && mode !== 'tut') genWorld(span);
    else if (mode === 'duel' || mode === 'tut') genArena();
    else genRooms(span, span, mode === 'br' ? 5 : 7, mode === 'war' ? 18 : 15,
                  Math.round(span * span / 230), mode === 'br' ? 1 : 2, true);

    explored.fill(0);
    ents = []; bullets = []; sounds = []; parts = []; flashes = []; corpses = []; loot = [];
    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = []; secTick = 0;
    drops = []; splats = [];
    teamNadeT = [0, 0]; botFrags = 0; botShots = 0; targetSwaps = 0; killCauses = {}; botHits = 0;
    dmgMarks = []; shake = 0; promptItem = null;
    alive = MODE.field; matchTime = 0; shots = 0; hits = 0; kills = 0;
    score = [0, 0]; round = 1; roundBreak = 0; roundClock = 75;
    result = null; overCause = ''; lastWinner = null;

    if (MODE.zone) {
      var span = Math.min(WORLD_W, WORLD_H);
      zone = {
        cx: WORLD_W / 2 + rr(-span * 0.08, span * 0.08),
        cy: WORLD_H / 2 + rr(-span * 0.08, span * 0.08),
        span: span, r: span * 0.62, tx: 0, ty: 0,
        phase: 0, timer: PHASES[0].wait, closing: false, dps: 1
      };
      zone.tx = zone.cx; zone.ty = zone.cy;
      planNextRing();
    } else zone = null;

    var per = MODE.teams ? (MODE.field >> 1) : squad;
    fieldN = MODE.field;
    if (squad > 1 && !MODE.teams && mode === 'duel') fieldN = 4;   // 1v1 becomes 2v2
    // fewer bots if asked, never so few there is nobody to fight
    if (botFill < 1 && mode !== 'duel' && mode !== 'tut') {
      var humN = 1 + (netRole === 'host' ? netGuests.length : 0) + (splitWant ? 1 : 0);
      fieldN = Math.max(humN + 2, Math.round(fieldN * botFill));
      if (MODE.teams && fieldN % 2) fieldN++;
    }
    alive = fieldN;
    var sp = MODE.teams ? teamSpawns(fieldN)
           : (squad > 1 ? squadSpawns(Math.ceil(fieldN / squad), squad) : pickSpawns(fieldN));
    player = makeEnt(sp[0], true, 'YOU');
    player.local = true; player.ctl = { any: true, kb: true }; player.cam = cam;
    ents.push(player);
    locals = [player]; splitOn = false;
    var online = netRole === 'host' && netGuests.length > 0 && mode !== 'tut';
    var sc = (online || mode === 'tut') ? null : (splitWant ? splitControls() : null);
    if (!online && splitWant && !sc) feed('split screen needs a <b>controller</b> for player 2', true);
    if (netRole === 'host') player.name = acctName || 'HOST';
    for (var gq = 0; gq < netGuests.length; gq++) netGuests[gq].ent = null;
    if (sc) {
      var p2 = makeEnt(sp[1 % sp.length], true, 'P2');
      p2.local = true; p2.ctl = { pad: sc.p2, kb: false }; p2.cam = { x: 0, y: 0 }; p2.padPrev = {};
      player.name = 'P1'; player.ctl = { pad: sc.p1, kb: true }; player.padPrev = {};
      ents.push(p2); locals.push(p2);
      splitOn = true;
    }
    for (var i = ents.length; i < fieldN; i++) ents.push(makeEnt(sp[i % sp.length], false, NAMES[i - 1]));
    if (MODE.zombies) {
      ents.forEach(function (e, idx) { e.team = 0; e.skin = idx % 16; });
      var seeds = Math.max(3, Math.round(fieldN * 0.22));
      for (var zs = 0; zs < seeds; zs++) {
        var patient = locals.length + rnd(Math.max(1, fieldN - locals.length));   // never a local player
        ents[patient].team = 1;
        ents[patient].skin = ZOMBIE_SKIN;
      }
      zombClock = MODE.clock;
      zombSpawnT = 2;
    } else if (MODE.teams) {
      var half = fieldN >> 1;
      ents.forEach(function (e, idx) {
        e.team = idx < half ? 0 : 1;
        var set = TEAM_SKINS[e.team];
        e.skin = set[(idx % half) % set.length];
      });
    } else if (squad > 1) {
      var pool2 = [];
      for (var k2 = 0; k2 < 16; k2++) pool2.push(k2);
      shuffle(pool2);
      ents.forEach(function (e, idx) {
        e.team = Math.floor(idx / squad);         // partners share a team
        e.skin = pool2[idx % pool2.length];
      });
    } else {
      // a different skin each, so people are told apart by more than a colour
      var pool = [];
      for (var k = 0; k < 16; k++) pool.push(k);
      shuffle(pool);
      ents.forEach(function (e, idx) { e.skin = pool[idx % pool.length]; e.team = idx; });
    }
    player.skin = WALLET.skin;
    if ((locals.length > 1) && !MODE.teams && !MODE.zombies && locals[1].skin === player.skin) locals[1].skin = (player.skin + 5) % 16;
    elHud.classList.toggle('split', splitOn);

    charCache = {};
    ents.forEach(function (e, i) { placeEnt(e, sp[i % sp.length]); });

    if (MODE.ctf) {
      var acc = [{ x: 0, y: 0, n: 0 }, { x: 0, y: 0, n: 0 }];
      ents.forEach(function (e) {
        var a = acc[e.team];
        a.x += e.x; a.y += e.y; a.n++;
      });
      flags = [0, 1].map(function (t) {
        var a = acc[t], hx = a.n ? a.x / a.n : WORLD_W / 2, hy = a.n ? a.y / a.n : WORLD_H / 2;
        return { team: t, hx: hx, hy: hy, x: hx, y: hy, home: true, carrier: null, ping: 0 };
      });
    }

    if (MODE.sectors) {
      var st = pickSpawns(MODE.sectors);
      sectors = st.map(function (t, i) {
        return {
          x: t.x * TILE + TILE / 2, y: t.y * TILE + TILE / 2, r: 108,
          name: 'ABC'.charAt(i), owner: -1, cap: -1, prog: 0
        };
      });
    }

    spawnLoot(sp);
    // friends in the lobby step into bots' bodies before the plane boards
    if (netRole === 'host' && mode !== 'tut') for (var gi = 0; gi < netGuests.length; gi++) admitGuest(netGuests[gi], true);
    if (mode === 'tut') tutSetup();
    plane = null;
    if (mode === 'br') boardPlane();
    elFeed.innerHTML = '';
    elMenu.hidden = true; elOver.hidden = true; elHud.hidden = false; elPaused.hidden = true;
    $('online').hidden = true; $('account').hidden = true; $('friends').hidden = true;
    if ($('chat') && !$('chat').hidden) closeChat(), $('friends').hidden = true;
    state = 'play';
    syncHud();
    cgGame('gameplayStart'); cgRoom();
    if (netRole === 'host') for (var gs = 0; gs < netGuests.length; gs++) if (netGuests[gs].ent) netSendTo(netGuests[gs], startMsg(netGuests[gs]));
    lobbyTouch();
  }

  function boardPlane() {
    // a line through the middle third of the map, edge to edge and beyond
    var a = Math.random() * Math.PI * 2;
    var dx = Math.cos(a), dy = Math.sin(a);
    var cx = WORLD_W / 2 + rr(-0.16, 0.16) * WORLD_W, cy = WORLD_H / 2 + rr(-0.16, 0.16) * WORLD_H;
    var half = Math.max(WORLD_W, WORLD_H) * 0.62;
    plane = { x0: cx - dx * half, y0: cy - dy * half, dx: dx, dy: dy, len: half * 2, t: 0, x: 0, y: 0 };
    plane.dur = plane.len / PLANE_SPEED;
    plane.x = plane.x0; plane.y = plane.y0;
    // Squads leave together; strangers spread along the whole run. A bot
    // flying with a person waits for them.
    var teamAt = {};
    for (var i = 0; i < ents.length; i++) {
      var e = ents[i];
      e.air = 'plane'; e.airT = 0;
      e.x = plane.x; e.y = plane.y;
      if (!e.bot) continue;
      if (teamAt[e.team] === undefined) teamAt[e.team] = rr(0.1, 0.9) * plane.dur;
      e.dropAt = Math.max(JUMP_AFTER + rr(0, 1.5), teamAt[e.team] + rr(0, 0.4));
      e.follow = false;
      for (var j = 0; j < locals.length; j++) if (locals[j].team === e.team) e.follow = true;
    }
  }

  function jumpOut(e) {
    if (e.air !== 'plane' || !plane) return;
    e.air = 'chute'; e.airT = 0;
    e.x = clamp(plane.x, TILE * 2, WORLD_W - TILE * 2);
    e.y = clamp(plane.y, TILE * 2, WORLD_H - TILE * 2);
    e.ang = Math.atan2(plane.dy, plane.dx);
    if (e.bot) {
      // pick a spot off to one side of the line to glide for
      var side = rr(-1, 1) * GLIDE_SPEED * CHUTE_TIME * 0.95, ahead = rr(0, 0.5) * GLIDE_SPEED * CHUTE_TIME;
      e.landX = clamp(e.x - plane.dy * side + plane.dx * ahead, TILE * 3, WORLD_W - TILE * 3);
      e.landY = clamp(e.y + plane.dx * side + plane.dy * ahead, TILE * 3, WORLD_H - TILE * 3);
      if (zone) {
        // pull the spot inside the circle (with room to spare)
        var lzx = e.landX - zone.cx, lzy = e.landY - zone.cy, lzd = Math.sqrt(lzx * lzx + lzy * lzy) || 1;
        var safeR = zone.r * 0.8;
        if (lzd > safeR) { e.landX = zone.cx + lzx / lzd * safeR; e.landY = zone.cy + lzy / lzd * safeR; }
      }
    }
    if (e.local) audioEmit(e.x, e.y, PICK_SND, e.id);
    // a partner bot bails out right behind you
    if (e.local) for (var i = 0; i < ents.length; i++) {
      var m = ents[i];
      if (m.bot && m.air === 'plane' && m.team === e.team) m.dropAt = Math.min(m.dropAt, plane.t + 0.35), m.follow = false;
    }
  }

  function land(e) {
    // down on the nearest open ground
    var tx = clamp(Math.floor(e.x / TILE), 1, MAP_W - 2), ty = clamp(Math.floor(e.y / TILE), 1, MAP_H - 2);
    var spot = null;
    for (var r = 0; r < 40 && !spot; r++) {
      for (var oy = -r; oy <= r && !spot; oy++) for (var ox = -r; ox <= r; ox++) {
        if (Math.max(Math.abs(ox), Math.abs(oy)) !== r) continue;
        var x = tx + ox, y = ty + oy;
        if (x < 1 || y < 1 || x >= MAP_W - 1 || y >= MAP_H - 1) continue;
        if (!isWall(x, y)) { spot = { x: x, y: y }; break; }
      }
    }
    if (spot) { e.x = spot.x * TILE + TILE / 2; e.y = spot.y * TILE + TILE / 2; }
    e.air = null; e.airT = 0;
    e.path = null; e.pathI = 0; e.repathT = 0; e.lootGoal = null; e.target = null;
    e.lastX = e.x; e.lastY = e.y; e.stuckT = 0;
    spark(e.x, e.y, 6, '210,190,150', 90);
  }

  function updateDrop(dt) {
    if (!plane) return;
    plane.t += dt;
    var k = Math.min(plane.t, plane.dur) * PLANE_SPEED;
    plane.x = plane.x0 + plane.dx * k; plane.y = plane.y0 + plane.dy * k;
    var inWorld = plane.x > TILE * 2 && plane.y > TILE * 2 && plane.x < WORLD_W - TILE * 2 && plane.y < WORLD_H - TILE * 2;
    plane.overLand = inWorld;
    var riders = 0;
    for (var i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e.alive) continue;
      if (e.air === 'plane') {
        e.x = plane.x; e.y = plane.y;
        var late = plane.t >= plane.dur * 0.93 || (!inWorld && plane.t > plane.dur * 0.5);
        if (inWorld && (late || (e.bot && !e.follow && plane.t >= e.dropAt))) jumpOut(e);
        else if (late && !inWorld) {
          // flew past the edge: tip them out over the last stretch of land
          plane.x = clamp(plane.x, TILE * 3, WORLD_W - TILE * 3);
          plane.y = clamp(plane.y, TILE * 3, WORLD_H - TILE * 3);
          jumpOut(e);
        }
        if (e.air === 'plane') riders++;
      } else if (e.air === 'chute') {
        e.airT += dt;
        if (e.bot) {
          var gx = e.landX - e.x, gy = e.landY - e.y, gl = Math.sqrt(gx * gx + gy * gy);
          if (gl > 4) {
            var st = Math.min(gl, GLIDE_SPEED * dt);
            e.x += gx / gl * st; e.y += gy / gl * st;
            e.ang = Math.atan2(gy, gx);
          }
        }
        if (e.airT >= CHUTE_TIME) land(e);
      }
    }
    plane.riders = riders;
    if (plane.t > plane.dur + 2 && !riders) {
      var still = false;
      for (i = 0; i < ents.length; i++) if (ents[i].air) { still = true; break; }
      if (!still) plane = null;
    }
  }

  // Your own hands in the air: jump from the plane, then steer the chute.
  // the door opens a few seconds in, once the plane is over the island
  var JUMP_AFTER = 5;
  function jumpOpen() { return !!plane && plane.t >= JUMP_AFTER && !!plane.overLand; }
  function airControl(e, I, dt) {
    if (e.air === 'plane') {
      var go = (I.pad && (I.hit(PAD.jump) || I.hit(PAD.pickup))) || (I.kb && e.jumpReq);
      e.jumpReq = false;
      if (go && jumpOpen()) jumpOut(e);
      return;
    }
    var ix = 0, iy = 0;
    if (I.pad) { ix = I.ax(0); iy = I.ax(1); }
    if (!ix && !iy && I.kb) {
      if (keys['a']) ix -= 1; if (keys['d']) ix += 1;
      if (keys['w']) iy -= 1; if (keys['s']) iy += 1;
    }
    if (!ix && !iy && I.touch && sticks.move) {
      ix = sticks.move.x - sticks.move.ox; iy = sticks.move.y - sticks.move.oy;
      if (Math.abs(ix) + Math.abs(iy) < 8) ix = iy = 0;
    }
    var l = Math.sqrt(ix * ix + iy * iy);
    if (l > 0) {
      ix /= Math.max(1, l); iy /= Math.max(1, l);
      e.x = clamp(e.x + ix * GLIDE_SPEED * dt, TILE * 2, WORLD_W - TILE * 2);
      e.y = clamp(e.y + iy * GLIDE_SPEED * dt, TILE * 2, WORLD_H - TILE * 2);
    }
    if (I.kb && mouse.sx !== undefined && !I.padOn) e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);
  }

  // ---------------------------------------------------------------- tutorial
  // A small arena, three standing targets, and one thing to learn at a time.
  // Each step waits for you to actually do it.
  var tut = { i: 0, t: 0, moved: 0, sprint: 0, kills: 0, lx: 0, ly: 0, slotWas: 0, flash: 0 };
  var TUT = [
    { title: 'MOVE', k: 'W A S D to walk', p: 'LEFT STICK to walk',
      done: function () { return tut.moved > 260; } },
    { title: 'AIM', k: 'Point with the MOUSE - you always face it', p: 'Point with the RIGHT STICK',
      done: function () { return tut.t > 2.5; } },
    { title: 'SHOOT', k: 'Follow the gold marker to the targets. CLICK to shoot one', p: 'Follow the gold marker to the targets. RT to shoot one', mark: 'targets',
      done: function () { return tut.hits >= 1; } },
    { title: 'RELOAD', k: 'R to reload', p: 'A to reload',
      start: function () { var sl = curSlot(player); if (sl) sl.ammo = Math.min(sl.ammo, 4); },
      done: function () { return player.reloadT > 0; } },
    { title: 'PICK UP', k: 'Walk to the rifle (gold marker) and press E', p: 'Walk to the rifle (gold marker) and press X', mark: 'item',
      start: function () { tutDrop('gun', 'silenced'); },
      done: function () { return hasGun(player, 'silenced'); } },
    { title: 'SWAP', k: 'Q (or 1 / 2) swaps weapons', p: 'LB or RB swaps weapons',
      start: function () { tut.slotWas = player.slot; },
      done: function () { return player.slot !== tut.slotWas; } },
    { title: 'SPRINT', k: 'Hold SHIFT while walking - fast, but loud', p: 'Hold LT while walking - fast, but loud',
      done: function () { return tut.sprint > 1.2; } },
    { title: 'FRAG', k: 'G throws a frag - hit the group', p: 'D-PAD LEFT throws a frag - hit the group', mark: 'targets',
      start: function () { player.nades = Math.max(player.nades, 1); tut.have = player.nades; },
      done: function () { return player.nades < tut.have; } },
    { title: 'SMOKE', k: 'H throws smoke - nobody sees through it', p: 'D-PAD RIGHT throws smoke - nobody sees through it',
      start: function () { player.smokes = Math.max(player.smokes, 1); tut.have = player.smokes; },
      done: function () { return player.smokes < tut.have; } },
    { title: 'HEAL', k: 'You are hurt. F uses a stim', p: 'You are hurt. Y uses a stim',
      start: function () { player.hp = Math.min(player.hp, 45); player.meds = Math.max(player.meds, 1); tut.have = player.meds; },
      done: function () { return player.meds < tut.have; } },
    { title: 'MELEE', k: 'V swings the gun butt - works with no ammo', p: 'D-PAD UP (or click the right stick) swings the gun butt',
      done: function () { return player.meleeT > 0; } },
    { title: 'LISTEN', k: 'Every shot and footstep makes noise, and bots hunt by ear. In BLACKOUT you only see sound rings - a muzzle flash is the one exact giveaway.',
      p: null, wait: 7, done: function () { return tut.t > 7; } },
    { title: 'TEAM UP', k: 'In squad and team modes, stand beside a downed teammate to revive them. Blue markers are always your side.',
      p: null, wait: 7, done: function () { return tut.t > 7; } },
    { title: 'DROP IN', k: 'Battle royale starts in a plane: SPACE to jump, then steer your chute with W A S D. Stay inside the closing ring.',
      p: 'Battle royale starts in a plane: A to jump, then steer your chute with the LEFT STICK. Stay inside the closing ring.',
      wait: 8, done: function () { return tut.t > 8; } },
    { title: 'READY', k: 'That is everything. Press ENTER for the menu.', p: 'That is everything. Press A for the menu.',
      last: true, done: function () { return false; } }
  ];
  function hasGun(e, key) { return !!((e.slots[0] && e.slots[0].key === key) || (e.slots[1] && e.slots[1].key === key)); }
  function tutDrop(type, key) {
    // a couple of steps in front of you, on open floor
    var tx = Math.floor((player.x + Math.cos(player.ang) * 70) / TILE), ty = Math.floor((player.y + Math.sin(player.ang) * 70) / TILE);
    var t = { x: clamp(tx, 1, MAP_W - 2), y: clamp(ty, 1, MAP_H - 2) };
    if (isWall(t.x, t.y)) t = besideTile({ x: Math.floor(player.x / TILE), y: Math.floor(player.y / TILE) }, 1);
    addLoot(t.x, t.y, type, key, 0);
    tut.item = loot[loot.length - 1];
  }
  function tutSetup() {
    tut = { i: 0, t: 0, moved: 0, sprint: 0, kills: 0, lx: player.x, ly: player.y, slotWas: 0, flash: 0, have: 0 };
    // three targets in a loose group across the arena, facing you
    var px = Math.floor(player.x / TILE), py = Math.floor(player.y / TILE);
    var far = null, best = -1;
    for (var i = 0; i < floorTiles.length; i += 2) {
      var f = floorTiles[i], d = (f.x - px) * (f.x - px) + (f.y - py) * (f.y - py);
      if (d > 90 && d < 260 && d > best && lineClear(player.x, player.y, f.x * TILE + TILE / 2, f.y * TILE + TILE / 2)) { best = d; far = f; }
    }
    if (!far) far = floorTiles[rnd(floorTiles.length)];
    for (var k = 0; k < 3; k++) {
      var spot = k ? besideTile(far, k) : far;
      var d2 = makeEnt(spot, false, 'TARGET');
      d2.dummy = true; d2.team = 1; d2.skin = 3 + k; d2.home = spot;
      ents.push(d2);
      placeEnt(d2, spot);
      d2.ang = Math.atan2(player.y - d2.y, player.x - d2.x);
    }
    charCache = {};
    if (TUT[0].start) TUT[0].start();
  }
  function tutOn(what, e) {
    if (what === 'kill' && e && e.dummy) tut.kills++;
  }
  var tutEnterPrev = false;
  function tutTick(dt) {
    var i;
    // targets stand back up where they stood, and always face you
    for (i = 0; i < ents.length; i++) {
      var d = ents[i];
      if (!d.dummy) continue;
      if (!d.alive) {
        d.respawnT -= dt;
        if (d.respawnT <= 0) { placeEnt(d, d.home); d.slots = [null, null]; }
      } else d.ang = Math.atan2(player.y - d.y, player.x - d.x);
    }
    if (!player.alive) {
      player.respawnT -= dt;
      if (player.respawnT <= 0) placeEnt(player, { x: Math.floor(player.x / TILE), y: Math.floor(player.y / TILE) });
      return;
    }
    tut.moved += Math.sqrt((player.x - tut.lx) * (player.x - tut.lx) + (player.y - tut.ly) * (player.y - tut.ly));
    tut.lx = player.x; tut.ly = player.y;
    if ((player._spd || 0) > 200) tut.sprint += dt;
    tut.t += dt;
    if (tut.flash > 0) tut.flash -= dt;
    var st = TUT[tut.i];
    if (tut.leaving) return;
    if (st.last) {
      var go = !!keys['enter'] || padDown(0);
      // leave after this frame finishes - the rest of it still expects a tutorial
      if (go && !tutEnterPrev) { tut.leaving = true; setTimeout(tutDone, 0); }
      tutEnterPrev = go;
      return;
    }
    if (st.done()) {
      tut.i++; tut.t = 0; tut.flash = 0.9;
      tutEnterPrev = !!keys['enter'] || padDown(0);
      audioEmit(player.x, player.y, PICK_SND, player.id);
      if (TUT[tut.i].start) TUT[tut.i].start();
    }
  }
  function tutDone() {
    storeSet('earshot.tutDone', '1');
    goHome();
    syncTutBtn();
  }
  function syncTutBtn() {
    var done = false;
    done = storeGet('earshot.tutDone') === '1';
    var b = $('tutBtn');
    if (b) { b.className = done ? 'go ghost' : 'go'; b.textContent = done ? 'TUTORIAL' : 'TUTORIAL \u2014 START HERE'; }
  }
  function renderTutorial() {
    if (mode !== 'tut' || !player) return;
    var st = TUT[tut.i];
    var txt = (usingPad(player) && st.p) ? st.p : st.k;
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    // wrap the instruction to the width of the screen
    ctx.font = '500 13px "IBM Plex Mono", monospace';
    var maxW = Math.min(cw - 40, 520), words = txt.split(' '), lines = [], line = '';
    for (var w = 0; w < words.length; w++) {
      var tryL = line ? line + ' ' + words[w] : words[w];
      if (ctx.measureText(tryL).width > maxW - 36 && line) { lines.push(line); line = words[w]; } else line = tryL;
    }
    if (line) lines.push(line);
    var miniB = 0;
    var bw = maxW, bh = 52 + lines.length * 19, bx = cw / 2 - bw / 2, by = Math.max(ch * 0.14, miniB, 84);
    ctx.fillStyle = '#2e4559'; ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 3;
    ctx.fillRect(bx, by, bw, bh); ctx.strokeRect(bx, by, bw, bh);
    if (tut.flash > 0) {
      ctx.fillStyle = 'rgba(242,189,29,' + (tut.flash * 0.5).toFixed(3) + ')';
      ctx.fillRect(bx, by, bw, bh);
    }
    ctx.fillStyle = '#f2bd1d';
    ctx.font = '400 17px "Russo One", "Chakra Petch", sans-serif';
    ctx.fillText((tut.i + 1) + '/' + TUT.length + '  ' + st.title, cw / 2, by + 22);
    ctx.font = '500 13px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#f1e7d0';
    for (var li = 0; li < lines.length; li++) ctx.fillText(lines[li], cw / 2, by + 46 + li * 19);
    var marks = [];
    if (st.mark === 'targets') { for (var mi = 0; mi < ents.length; mi++) if (ents[mi].dummy && ents[mi].alive) marks.push(ents[mi]); }
    else if (st.mark === 'item' && tut.item && loot.indexOf(tut.item) >= 0) marks.push(tut.item);
    for (var mk = 0; mk < marks.length; mk++) {
      var sx = (marks[mk].x - cam.x) * zoom + cw / 2, sy = (marks[mk].y - cam.y) * zoom + ch / 2 - 22;
      var pad = 26, off = sx < pad || sx > cw - pad || sy < pad || sy > ch - pad;
      var ex = clamp(sx, pad, cw - pad), ey = clamp(sy, pad, ch - pad);
      ctx.save();
      ctx.translate(ex, ey);
      if (off) ctx.rotate(Math.atan2(sy - ch / 2, sx - cw / 2) - Math.PI / 2);
      ctx.fillStyle = '#f2bd1d'; ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 2.5;
      ctx.beginPath(); ctx.moveTo(-8, -7); ctx.lineTo(8, -7); ctx.lineTo(0, 5); ctx.closePath();
      ctx.fill(); ctx.stroke();
      ctx.restore();
    }
    // timed steps show how long is left
    if (st.wait) {
      ctx.fillStyle = '#1d2d3b'; ctx.fillRect(bx + 3, by + bh - 7, bw - 6, 4);
      ctx.fillStyle = '#f2bd1d'; ctx.fillRect(bx + 3, by + bh - 7, (bw - 6) * clamp(tut.t / st.wait, 0, 1), 4);
    }
    ctx.restore();
  }

  function newRound() {
    var sp = pickSpawns(2), seat = [0, 0];
    ents.forEach(function (e) {
      var t = e.team & 1, base = sp[t % sp.length], k = seat[t]++;
      placeEnt(e, k ? besideTile(base, k) : base);
    });
    corpses.length = 0; bullets.length = 0;
    round++; roundClock = 75; roundBreak = 0;
  }

  // an open tile a step or two from `t`, so partners do not stack
  function besideTile(t, k) {
    var offs = [[2, 0], [0, 2], [-2, 0], [0, -2], [2, 2], [-2, -2]];
    for (var i = 0; i < offs.length; i++) {
      var o2 = offs[(k - 1 + i) % offs.length], x = t.x + o2[0], y = t.y + o2[1];
      if (x > 0 && y > 0 && x < MAP_W - 1 && y < MAP_H - 1 && !isWall(x, y)) return { x: x, y: y };
    }
    return t;
  }

  function feed(html, mine) {
    if (netRole === 'host' && netHostLive()) netEv.push(['f', html, !!mine]);
    var d = document.createElement('div');
    d.innerHTML = html;
    if (mine) d.className = 'you';
    elFeed.appendChild(d);
    while (elFeed.children.length > 5) elFeed.removeChild(elFeed.firstChild);
    setTimeout(function () { if (d.parentNode) d.parentNode.removeChild(d); }, 6000);
  }

  // ---------------------------------------------------------------- effects
  function emit(x, y, def, owner, kind) {
    if (sounds.length > 150) sounds.shift();
    sounds.push({ x: x, y: y, r: 0, maxR: def.maxR, speed: def.speed, color: def.color, w: def.w, kind: kind, owner: owner, heard: {} });
    audioEmit(x, y, def, owner);
  }
  function spark(x, y, n, color, spd) {
    if (netRole === 'host' && netHostLive()) netEv.push(['k', Math.round(x), Math.round(y), n, color, spd]);
    for (var i = 0; i < n; i++) {
      var a = Math.random() * Math.PI * 2, s = rr(spd * 0.3, spd);
      parts.push({ x: x, y: y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: rr(0.18, 0.45), max: 0.45, color: color, sz: rr(1, 2.4) });
    }
    if (parts.length > 400) parts.splice(0, parts.length - 400);
  }

  // ---- blood ------------------------------------------------------------
  // Droplets are thrown along the shot, arc through the air and land as
  // stains that stay on the ground. The fallen leave a spreading pool; the
  // badly hurt leave drips behind them. The infected bleed a dark green.
  var drops = [], splats = [], SPLAT_MAX = 320, splatArt = null;
  var BLOOD_RED = ['#810322', '#a4072c', '#b80a33'], BLOOD_ZOMB = ['#27430b', '#355a0f', '#446f14'];
  // the stain art: three splats side by side (red), and the same in green
  var BLOOD_ART = { red: new Image(), zomb: new Image() }, bloodArtReady = 0, BLOOD_CELL_BLOB = 92;
  BLOOD_ART.red.onload = BLOOD_ART.zomb.onload = function () { if (++bloodArtReady === 2) splatArt = null; };
  BLOOD_ART.red.src = 'assets/blood_splat.png';
  BLOOD_ART.zomb.src = 'assets/blood_splat_zomb.png';
  function bakeSplats() {
    if (bloodArtReady === 2) {
      // cut the drawn splats out of their sheets
      splatArt = { red: [], zomb: [], drawn: true };
      ['red', 'zomb'].forEach(function (k) {
        var img = BLOOD_ART[k], cell = img.height;
        for (var i = 0; i < 3; i++) {
          var c = document.createElement('canvas'); c.width = c.height = cell;
          c.getContext('2d').drawImage(img, i * cell, 0, cell, cell, 0, 0, cell, cell);
          splatArt[k].push(c);
        }
      });
      return;
    }
    // until the art arrives: a few simple stain shapes
    splatArt = { red: [], zomb: [] };
    [['red', BLOOD_RED], ['zomb', BLOOD_ZOMB]].forEach(function (pal) {
      for (var v = 0; v < 6; v++) {
        var c = document.createElement('canvas'); c.width = c.height = 96;
        var g = c.getContext('2d');
        g.translate(48, 48);
        g.fillStyle = pal[1][0];
        var n = 7 + (v % 3) * 2;
        g.beginPath();
        for (var k = 0; k <= n; k++) {                        // a lumpy blob
          var a = k / n * 6.2832, rr0 = 22 + ((v * 37 + k * 53) % 11);
          var px = Math.cos(a) * rr0, py = Math.sin(a) * rr0 * (0.8 + (v % 2) * 0.2);
          if (k === 0) g.moveTo(px, py); else g.quadraticCurveTo(Math.cos(a - 3.1416 / n) * (rr0 + 6), Math.sin(a - 3.1416 / n) * (rr0 + 4), px, py);
        }
        g.fill();
        g.fillStyle = pal[1][1];                                // wetter middle
        g.beginPath(); g.ellipse(-3, -2, 14, 11, v, 0, 6.2832); g.fill();
        g.fillStyle = pal[1][0];
        for (var d = 0; d < 9; d++) {                           // flecks thrown clear
          var da = (v * 1.7 + d * 0.9), dr = 28 + ((d * 29 + v * 11) % 16);
          g.beginPath(); g.arc(Math.cos(da) * dr, Math.sin(da) * dr, 1.5 + (d % 3), 0, 6.2832); g.fill();
        }
        splatArt[pal[0]].push(c);
      }
    });
  }
  function bloodOf(e) { return (e && isZombie(e)) ? 'zomb' : 'red'; }
  function addSplat(x, y, r, pal, kind) {
    if (!SET.blood) return;
    if (splats.length >= SPLAT_MAX) splats.shift();
    splats.push({ x: x, y: y, r: r, ang: Math.random() * 6.2832, v: rnd(6), pal: pal, t: 0,
                  grow: kind === 'pool' ? 2.4 : 0.12, kind: kind || 'drop' });
  }
  // x, y: where; ang: the way the round was travelling; amount: how hard
  function bleed(x, y, ang, amount, big, pal) {
    if (netRole === 'host' && netHostLive()) netEv.push(['g', Math.round(x), Math.round(y), +(ang || 0).toFixed(2), Math.round(amount), big ? 1 : 0, pal || 'red']);
    if (!SET.blood) { spark(x, y, big ? 10 : 4, '170,150,150', 120); return; }
    pal = pal || 'red';
    if (ang === undefined || ang === null || isNaN(ang)) ang = Math.random() * 6.2832;
    var n = Math.min(26, 4 + Math.round(amount / 5) + (big ? 12 : 0));
    for (var i = 0; i < n; i++) {
      // most of it goes out the far side, a little back toward the shooter
      var back = Math.random() < 0.18;
      var a = ang + (back ? Math.PI : 0) + rr(-0.55, 0.55) * (big ? 1.8 : 1);
      var sp = rr(60, big ? 260 : 210) * (back ? 0.5 : 1);
      if (drops.length > 260) drops.shift();
      drops.push({ x: x, y: y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, z: rr(6, 14), vz: rr(20, 90),
                   sz: rr(1.3, big ? 3.6 : 2.8), pal: pal });
    }
    addSplat(x + Math.cos(ang) * 6, y + Math.sin(ang) * 6, big ? 14 : rr(8, 12), pal, 'drop');
    if (big) addSplat(x, y, 40 + rr(0, 10), pal, 'pool');
  }
  function goreTick(dt) {
    var i;
    for (i = drops.length - 1; i >= 0; i--) {
      var d = drops[i];
      d.vz -= 420 * dt; d.z += d.vz * dt;
      var nx = d.x + d.vx * dt, ny = d.y + d.vy * dt;
      if (wallAt(nx, ny)) { d.vx *= -0.2; d.vy *= -0.2; nx = d.x; ny = d.y; }   // spatters on the wall
      d.x = nx; d.y = ny;
      d.vx *= Math.pow(0.35, dt); d.vy *= Math.pow(0.35, dt);
      if (d.z <= 0) { addSplat(d.x, d.y, d.sz * rr(1.2, 2.2), d.pal, 'drop'); drops.splice(i, 1); }
    }
    for (i = 0; i < splats.length; i++) splats[i].t += dt;
    // the badly hurt leave a trail
    for (i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e.alive || e.air || !(e.bleeding || (e.hp < 40 && e.moving))) continue;
      e.dripT = (e.dripT || 0) - dt;
      if (e.dripT <= 0) {
        e.dripT = rr(0.18, 0.4) * (0.5 + e.hp / 80);
        addSplat(e.x + rr(-4, 4), e.y + rr(-4, 4), rr(1.8, 3.4), bloodOf(e), 'drop');
      }
    }
    // the downed keep bleeding where they lie
    for (i = 0; i < ents.length; i++) {
      var dn = ents[i];
      if (!dn.alive || !dn.down) continue;
      dn.dripT = (dn.dripT || 0) - dt;
      if (dn.dripT <= 0) { dn.dripT = rr(0.6, 1.1); addSplat(dn.x + rr(-6, 6), dn.y + rr(-6, 6), rr(3, 6), bloodOf(dn), 'drop'); }
    }
  }
  function drawSplats() {
    if (!splats.length) return;
    if (!splatArt) bakeSplats();
    for (var i = 0; i < splats.length; i++) {
      var p = splats[i];
      // stains spread for a moment, then slowly dry and fade over a minute or two
      var grow = Math.min(1, p.t / p.grow);
      var r = p.r * (p.kind === 'pool' ? (0.25 + 0.75 * (1 - Math.pow(1 - grow, 2))) : (0.6 + 0.4 * grow));
      var a = p.t < 60 ? 0.92 : Math.max(0, 0.92 - (p.t - 60) / 90);
      if (a <= 0.02) continue;
      var set = splatArt[p.pal], art = set[p.v % set.length];
      ctx.save();
      ctx.globalAlpha = a;
      ctx.translate(p.x, p.y); ctx.rotate(p.ang);
      if (splatArt.drawn) {
        // pixel art stays crisp; the big double splat is for pools only
        if (p.kind === 'pool') art = set[2]; else art = set[p.v % 2];
        ctx.imageSmoothingEnabled = false;
        var sz = art.width * (r / BLOOD_CELL_BLOB);
        ctx.drawImage(art, -sz / 2, -sz / 2, sz, sz);
      } else {
        var sc = r / 26;
        ctx.drawImage(art, -48 * sc, -48 * sc, 96 * sc, 96 * sc);
      }
      ctx.restore();
    }
  }
  function drawDrops() {
    for (var i = 0; i < drops.length; i++) {
      var d = drops[i], col = (d.pal === 'zomb' ? BLOOD_ZOMB : BLOOD_RED)[1];

      ctx.fillStyle = 'rgba(0,0,0,.25)';                        // its shadow on the ground
      ctx.beginPath(); ctx.arc(d.x + d.z * 0.3, d.y + d.z * 0.3, d.sz * 0.8, 0, 6.2832); ctx.fill();
      ctx.fillStyle = col;
      ctx.beginPath(); ctx.arc(d.x, d.y - d.z * 0.5, d.sz, 0, 6.2832); ctx.fill();
    }
  }

  function fire(e) {
    var w = curW(e);
    if (!w || e.reloadT > 0 || e.fireT > 0 || e.useT > 0) return;
    var slot = curSlot(e);
    if (slot.ammo <= 0) { startReload(e); return; }
    var spread = w.spread + (e.bot ? DIFF[difficulty].spread : (e._spd > 200 ? 0.055 : (e._spd > 0 ? 0.022 : 0)));
    var muzzle = muzzleOff(e);
    // never let a long barrel push the shot through a wall you are hugging
    if (wallAt(e.x + Math.cos(e.ang) * muzzle, e.y + Math.sin(e.ang) * muzzle)) muzzle = e.r + 6;
    for (var p = 0; p < w.pellets; p++) {
      var ang = e.ang + rr(-spread, spread);
      bullets.push({
        x: e.x + Math.cos(ang) * muzzle, y: e.y + Math.sin(ang) * muzzle,
        vx: Math.cos(ang) * w.speed, vy: Math.sin(ang) * w.speed,
        owner: e.id, dmg: w.dmg * (e.bot ? DIFF[difficulty].dmg : 1), life: 1.25
      });
    }
    slot.ammo--;
    if (e.bot) {
      botShots += w.pellets;
      // each shot kicks the hand off line; long bursts spray
      if (e.aimOff !== undefined) e.aimOff += rr(-1, 1) * (w.interval < 0.2 ? 0.05 : 0.025);
    }
    // a semi-auto only waits a moment between clicks (bots keep their pace)
    e.fireT = e.bot ? w.interval * DIFF[difficulty].rate : (w.semi ? w.tap : w.interval);
    e.animFire = 0.17;
    var fdur = blackout ? 0.16 : (FX.flash ? FX.flash.frames / FX.flash.fps : 0.075);
    var fscale = w.pellets > 1 ? 1.35 : (w.interval > 0.4 ? 1.4 : (w.snd.maxR < 400 ? 0.5 : 1));
    flashes.push({
      x: e.x + Math.cos(e.ang) * muzzle, y: e.y + Math.sin(e.ang) * muzzle,
      ang: e.ang, t: fdur, max: fdur, tint: w.tint, scale: fscale
    });
    emit(e.x, e.y, w.snd, e.id, 'shot');
    if (onHere(e)) shots++;
    if (e === player) { shake = Math.min(shake + (w.pellets > 1 ? 3 : 1.6), 6); }
    return true;
  }
  function startReload(e) {
    var w = curW(e);
    if (!w) return;
    var slot = curSlot(e);
    if (e.reloadT > 0 || slot.ammo === w.mag || e.reserve <= 0) return;
    e.reloadT = w.reload;
    emit(e.x, e.y, MOVE_SND.reload, e.id, 'reload');
  }
  function finishReload(e) {
    var w = curW(e);
    if (!w) return;
    var slot = curSlot(e);
    var take = Math.min(w.mag - slot.ammo, e.reserve);
    slot.ammo += take;
    if (e.reserve < 9000) e.reserve -= take;
  }
  function throwNade(e, kind, ang, power) {
    var have = kind === 'smoke' ? e.smokes : e.nades;
    if (have <= 0 || e.useT > 0 || !e.alive || e.down || isZombie(e)) return;
    if (kind === 'smoke') e.smokes--; else e.nades--;
    var a = (ang === undefined) ? e.ang : ang;
    var v = power || 560;
    e.throwT = 0.34;
    nades.push({
      x: e.x + Math.cos(a) * (e.r + 4), y: e.y + Math.sin(a) * (e.r + 4),
      vx: Math.cos(a) * v, vy: Math.sin(a) * v,
      fuse: kind === 'smoke' ? 1.05 : 1.35, spin: Math.random() * 6.2832,
      owner: e.id, kind: kind || 'frag'
    });
    emit(e.x, e.y, PIN_SND, e.id, 'pin');
  }

  // How hard to throw so it lands about `d` away, given the skid.
  function throwPower(d) { return clamp(d * 1.95, 240, 620); }

  function popSmoke(g) {
    emit(g.x, g.y, SMOKE_SND, g.owner, 'smoke');
    spark(g.x, g.y, 14, '198,204,212', 150);
    smokes.push({ x: g.x, y: g.y, t: 0, r: 0, maxR: 148, alpha: 0, life: 17 });
  }

  function updateSmoke(dt) {
    for (var i = smokes.length - 1; i >= 0; i--) {
      var sm = smokes[i];
      sm.t += dt;
      sm.r = sm.maxR * Math.min(1, sm.t / 1.3);
      if (sm.t < 1.3) sm.alpha = sm.t / 1.3;
      else if (sm.t > sm.life - 3.5) sm.alpha = Math.max(0, (sm.life - sm.t) / 3.5);
      else sm.alpha = 1;
      if (sm.t >= sm.life) smokes.splice(i, 1);
    }
  }

  function blast(g) {
    var R = 135;
    emit(g.x, g.y, NADE_SND, g.owner, 'shot');
    spark(g.x, g.y, 34, '255,186,90', 420);
    spark(g.x, g.y, 18, '150,150,150', 180);
    if (FX.impact_metal) {
      impacts.push({ x: g.x, y: g.y, ang: Math.random() * 6.2832, t: 0, scale: 2.6, fx: 'impact_metal' });
    }
    for (var i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e.alive || e.air) continue;
      var d = Math.sqrt((e.x - g.x) * (e.x - g.x) + (e.y - g.y) * (e.y - g.y));
      if (d > R || !lineClear(g.x, g.y, e.x, e.y)) continue;
      var dmg = 88 * (1 - d / R) + 14;
      hitCause = 'frag';
      damage(e, dmg, g.owner, Math.atan2(e.y - g.y, e.x - g.x));
      hitCause = 'gun';
    }
    if (dist({ x: g.x, y: g.y }, player) < R * 1.6) shake = Math.min(shake + 9, 14);
  }

  function flagState(f) { return f.carrier ? 'TAKEN' : (f.home ? 'HOME' : 'DROPPED'); }

  function updateSectors(dt) {
    var i, j;
    for (i = 0; i < sectors.length; i++) {
      var sc = sectors[i];
      var head = [0, 0];
      for (j = 0; j < ents.length; j++) {
        var e = ents[j];
        if (!e.alive || e.down) continue;
        var dx = e.x - sc.x, dy = e.y - sc.y;
        if (dx * dx + dy * dy < sc.r * sc.r) head[e.team]++;
      }
      var lead = head[0] > head[1] ? 0 : (head[1] > head[0] ? 1 : -1);
      if (lead >= 0 && lead !== sc.owner) {
        if (sc.cap !== lead) { sc.cap = lead; sc.prog = 0; }
        sc.prog += dt * 0.16 * Math.min(3, Math.abs(head[0] - head[1]));
        if (sc.prog >= 1) {
          sc.owner = lead; sc.prog = 0; sc.cap = -1;
          var mine = lead === player.team;
          feed('sector <b>' + sc.name + '</b> ' + (mine ? 'taken' : 'lost'), mine);
        }
      } else {
        sc.prog = Math.max(0, sc.prog - dt * 0.22);
        if (sc.prog === 0) sc.cap = -1;
      }
    }

    secTick += dt;
    while (secTick >= 1) {
      secTick -= 1;
      for (i = 0; i < sectors.length; i++) {
        if (sectors[i].owner >= 0) score[sectors[i].owner]++;
      }
      for (var t = 0; t < 2; t++) {
        if (score[t] >= MODE.target) {
          var won = t === player.team;
          finish(won, won ? 'Held the ground long enough. That is the match.'
                          : 'They held more of it for longer.');
          return;
        }
      }
    }
  }

  function updateFlags(dt) {
    for (var i = 0; i < flags.length; i++) {
      var f = flags[i];

      // a carrier who is dead or down loses it where they fell
      if (f.carrier && (!f.carrier.alive || f.carrier.down)) {
        f.x = f.carrier.x; f.y = f.carrier.y;
        f.carrier = null; f.home = false;
        feed('<b>' + (f.team === player.team ? 'YOUR' : 'THEIR') + '</b> flag dropped', f.team !== player.team);
      }

      if (f.carrier) {
        f.x = f.carrier.x; f.y = f.carrier.y;
        f.ping -= dt;
        if (f.ping <= 0) { f.ping = 1.0; emit(f.x, f.y, FLAG_SND, -1, 'flag'); }
        // home with it? only counts if your own flag is on its stand
        var own = flags[f.carrier.team];
        var d = Math.sqrt((f.carrier.x - own.hx) * (f.carrier.x - own.hx) + (f.carrier.y - own.hy) * (f.carrier.y - own.hy));
        if (d < 34 && !(own.home && !own.carrier) && f.carrier.local && (f.warnT || 0) <= matchTime) {
          f.warnT = matchTime + 4;
          feed('<b>CANNOT SCORE YET</b> - your flag has to be back on its stand', true);
        }
        if (d < 34 && own.home && !own.carrier) {
          score[f.carrier.team]++;
          var mine = f.carrier.team === player.team;
          feed('<b>' + (f.carrier === player ? 'YOU' : f.carrier.name) + '</b> captured', mine);
          f.carrier = null; f.home = true; f.x = f.hx; f.y = f.hy;
          if (score[mine ? player.team : 1 - player.team] >= MODE.target) {
            finish(mine, mine ? 'Three flags home. That is the match.'
                              : 'They ran the third one home.');
            return;
          }
        }
        continue;
      }

      // on the ground: enemies take it, teammates send it back
      for (var j = 0; j < ents.length; j++) {
        var e = ents[j];
        if (!e.alive || e.down) continue;
        var dd = Math.sqrt((e.x - f.x) * (e.x - f.x) + (e.y - f.y) * (e.y - f.y));
        if (dd > 24) continue;
        if (e.team !== f.team) {
          f.carrier = e; f.home = false; f.ping = 0.5;
          feed('<b>' + (e === player ? 'YOU' : e.name) + '</b> took ' + (f.team === player.team ? 'your' : 'their') + ' flag',
               e.team === player.team);
          break;
        } else if (!f.home) {
          f.home = true; f.x = f.hx; f.y = f.hy;
          feed('<b>' + (f.team === player.team ? 'YOUR' : 'THEIR') + '</b> flag returned', f.team === player.team);
          break;
        }
      }
    }
  }

  function updateNades(dt) {
    for (var i = nades.length - 1; i >= 0; i--) {
      var g = nades[i];
      g.fuse -= dt;
      g.spin += dt * 9;
      var nx = g.x + g.vx * dt, ny = g.y + g.vy * dt;
      if (wallAt(nx, g.y)) { g.vx = -g.vx * 0.42; nx = g.x; }
      if (wallAt(g.x, ny)) { g.vy = -g.vy * 0.42; ny = g.y; }
      g.x = nx; g.y = ny;
      var damp = Math.pow(0.2, dt);           // skids to a stop
      g.vx *= damp; g.vy *= damp;
      if (g.fuse <= 0) { if (g.kind === 'smoke') popSmoke(g); else blast(g); nades.splice(i, 1); }
    }
  }

  // Out of ammo is not out of the fight - swing the gun.
  function melee(e) {
    if (!e.alive || e.down || e.meleeT > 0 || e.useT > 0) return;
    e.meleeT = 0.55;
    e.swingT = 0.18;
    e.reloadT = 0;
    emit(e.x, e.y, MELEE_SND, e.id, 'melee');
    var hitAny = false;
    for (var i = 0; i < ents.length; i++) {
      var o = ents[i];
      if (o === e || !o.alive || o.air || !foes(e, o)) continue;
      var dx = o.x - e.x, dy = o.y - e.y;
      var d = Math.sqrt(dx * dx + dy * dy);
      if (d > 40) continue;
      var diff = ((Math.atan2(dy, dx) - e.ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
      if (Math.abs(diff) > 1.0) continue;
      if (!lineClear(e.x, e.y, o.x, o.y)) continue;
      hitCause = 'melee';
      damage(o, isZombie(e) ? 13 : 48, e.id, Math.atan2(dy, dx));
      hitCause = 'gun';
      hitAny = true;
    }
    if (hitAny && e === player) shake = Math.min(shake + 3, 8);
  }

  function useMed(e) {
    if (e.meds <= 0 || e.hp >= 100 || e.useT > 0 || e.reloadT > 0) return;
    e.meds--; e.useT = 1.6;
  }

  function damage(e, amount, fromId, ang) {
    if (!e.alive) return;
    var hitBy = ents[fromId];
    if (hitBy && hitBy.bot && hitBy !== e) botHits++;
    if (hitBy && hitBy.bot && e === player) botHitsOnYou++;
    if (mode === 'tut' && e.dummy && hitBy && hitBy.local) tut.hits = (tut.hits || 0) + 1;
    if (godMode && e === player) return;
    e.hp -= amount;
    e.useT = 0;
    // shot down to half or worse: bleeding until a stim closes it up
    if (e.hp > 0 && e.hp <= 50 && !isZombie(e) && hitBy && hitBy !== e && !e.down) {
      if (!e.bleeding && e.local) feed('<b>BLEEDING</b> - use a stim', true);
      e.bleeding = true; e.bleedBy = fromId;
      e.bleedLeft = 20;                         // a wound costs at most 20 HP
    }
    if (e.bot) { e.flinch = 0.35; if (e.aimOff !== undefined) e.aimOff += rr(-0.06, 0.06); }
    bleed(e.x, e.y, ang, amount, false, bloodOf(e));
    e.lastHitAng = ang;
    if (FX.blood && SET.blood && amount >= 30) {
      if (decals.length > 90) decals.shift();
      decals.push({
        x: e.x + Math.cos(ang) * 5, y: e.y + Math.sin(ang) * 5,
        ang: ang + rr(-0.25, 0.25), t: 0,
        scale: rr(0.8, 1.25) * (1 + Math.min(amount, 40) / 90)
      });
    }
    emit(e.x, e.y, MOVE_SND.hit, e.id, 'hit');
    if (e === player) shake = Math.min(shake + 3, 9);
    if (e.local) dmgMarks.push({ ang: ang, t: 1.1, who: e.id });
    if (e.hp > 0 && e.bot && !e.down) {
      var atk = ents[fromId];
      if (atk && atk.alive && foes(e, atk) && e.target !== atk) {
        if (e.skip) e.skip[atk.id] = -1;
        e.target = atk;
        e.reactT = Math.min(e.reactT, DIFF[difficulty].react * 0.5);
        e.lostT = 0;
      }
    }
    if (e.hp <= 0) kill(e, fromId);
    else if (e.bot && !e.target) {
      var src = ents[fromId];
      if (src) { e.alertX = src.x; e.alertY = src.y; e.alertT = 5; e.path = null; e.repathT = 0; }
    }
  }

  function kill(e, fromId) {
    // someone still standing on your side? then you go down, not out
    if (!e.down) {
      var helper = false;
      for (var h = 0; h < ents.length; h++) {
        var m = ents[h];
        if (m !== e && m.alive && !m.down && m.team === e.team) { helper = true; break; }
      }
      if (helper) {
        e.down = true; e.downT = 22; e.revT = 0; e.bleeding = false;
        e.hp = 24;
        e.target = null; e.path = null; e.reloadT = 0; e.useT = 0;
        bleed(e.x, e.y, e.lastHitAng, 30, false, bloodOf(e));
        emit(e.x, e.y, MOVE_SND.hit, e.id, 'hit');
        var dn = ents[fromId];
        e.downedBy = fromId;                      // who gets the kill cam if they bleed out
        if (e === player) feed('<b>DOWNED</b> - hold on for a teammate', true);
        else if (e.team === player.team) feed('<b>' + e.name + '</b> is down', true);
        else if (dn === player) feed('<b>YOU</b> downed ' + e.name, true);
        return;
      }
    }
    e.alive = false; e.hp = 0; e.down = false;
    corpses.push({ x: e.x, y: e.y });
    bleed(e.x, e.y, e.lastHitAng, 60, true, bloodOf(e));
    audioEmit(e.x, e.y, DEATH_SND, -1);
    if (FX.death && SET.blood) {
      if (deaths.length > 60) deaths.shift();
      deaths.push({ x: e.x, y: e.y, ang: Math.random() * 6.2832, t: 0, scale: rr(0.95, 1.25) });
    }
    var cause = fromId < 0 ? 'zone/bleed' : hitCause;
    killCauses[cause] = (killCauses[cause] || 0) + 1;
    dropKit(e);
    var killer = ents[fromId];
    var kn = killer ? killer.name : 'THE ZONE';
    // who the kill cam shows: whoever finished you, or whoever put you down
    // if you bled out or gave up
    var kcK = (killer && killer !== e) ? killer : (e.downedBy >= 0 ? ents[e.downedBy] : null);
    if (kcK && (!kcK.alive || kcK === e)) kcK = null;
    e.downedBy = -1;
    // a friend online was killed: their game plays its own kill cam
    if (e.ctl && e.ctl.net && kcK && netRole === 'host' && netHostLive()) {
      var kgw = curW(kcK);
      netEv.push(['c', e.id, kcK.id, kgw ? kgw.name : 'BARE HANDS', Math.max(0, Math.round(kcK.hp)), Math.round(dist(e, kcK))]);
    }
    // someone playing on this machine was killed: their camera goes to the
    // killer for a moment (each split-screen player gets their own)
    if (onHere(e) && kcK && !netGuest && mode !== 'tut') {
      var kw = curW(kcK);
      e.kc = { k: kcK, victim: e, t: 0, dur: 3.2, after: null,
                  gun: kw ? kw.name : 'BARE HANDS', hp: Math.max(0, Math.round(kcK.hp)), d: Math.round(dist(e, kcK)) };
    }
    if (killer && killer !== e) killer.kills++;
    if (killer && killer.local && killer !== e) {
      if (onHere(killer)) kills++;
      feed('<b>' + ((locals.length > 1) ? killer.name : 'YOU') + '</b> eliminated ' + e.name, true);
    }
    else if (e.local) { feed('<b>' + kn + '</b> eliminated ' + ((locals.length > 1) ? e.name : 'YOU'), true); }
    else feed('<b>' + kn + '</b> &rsaquo; ' + e.name, !!(killer && killer.team === player.team));

    if (mode === 'tut') { e.respawnT = e.dummy ? 1.3 : 2; tutOn('kill', e); return; }
    if (MODE.zombies) {
      if (e.team === 0) {
        e.team = 1;
        e.skin = ZOMBIE_SKIN;
        charCache = {};
        if (e === player) feed('<b>YOU TURNED</b>', true);
        else feed('<b>' + e.name + '</b> turned', false);
      }
      e.respawnT = 3.2;
      return;
    }
    if (mode === 'ctf' || mode === 'sect') {
      e.respawnT = 2.4;
      return;
    }
    if (mode === 'team' || mode === 'war') {
      if (killer && killer !== e && foes(killer, e)) {
        score[killer.team]++;
        if (score[killer.team] >= MODE.target) {
          var won = killer.team === player.team;
          finish(won, won ? 'Your side took it ' + score[player.team] + '-' + score[1 - player.team] + '.'
                          : 'They closed it out ' + score[1 - player.team] + '-' + score[player.team] + '.');
          return;
        }
      }
      e.respawnT = 2.2;
      return;
    }
    if (mode === 'duel') {
      for (var dq = 0; dq < ents.length; dq++) {
        if (ents[dq] !== e && ents[dq].alive && ents[dq].team === e.team) return;   // their partner fights on
      }
      var wt = 1 - e.team;                       // two sides: 0 and 1
      score[wt]++;
      if (score[wt] >= MODE.target) {
        for (var dw = 0; dw < ents.length; dw++) if (ents[dw].team === wt) { lastWinner = ents[dw]; break; }
        var mine2 = wt === player.team, sw = score[wt], sl = score[1 - wt];
        var who = squad > 1 ? (mine2 ? 'Your side' : 'Their side')
                            : (mine2 ? (locals.length > 1 ? player.name : 'You') : (lastWinner ? lastWinner.name : kn));
        finish(mine2, who + ' took it ' + sw + '\u2013' + sl + '.');
        return;
      }
      roundBreak = 1.8;
      return;
    }
    if (mode === 'gun') {
      if (killer && killer !== e) {
        killer.level++;
        if (killer.level >= LADDER.length) {
          lastWinner = killer;
          finish(!!killer.local, killer.local
            ? ((locals.length > 1) ? killer.name + ' ran the whole ladder first.' : 'You ran the whole ladder and closed it out with the rifle.')
            : kn + ' finished the ladder first.');
          return;
        }
        giveLoadout(killer);
        if (killer.local) feed(((locals.length > 1) ? '<b>' + killer.name + '</b> ' : '') + 'promoted to <b>' + WEAPONS[LADDER[killer.level]].name + '</b>', true);
      }
      e.respawnT = 2.5;
      return;
    }

    // battle royale
    alive--;

    if (e.local) e.place = alive + 1;
    if (e.local && !anyLocalAlive()) {
      finishAfterCam(e, false, killer && killer !== e
        ? kn + ' put ' + ((locals.length > 1) ? e.name : 'you') + ' down at ' + Math.round(dist(e, killer)) + ' units.'
        : 'The zone closed over ' + ((locals.length > 1) ? e.name : 'you') + '.', alive + 1);
    } else if (anyLocalAlive()) {
      var live = {}, nTeams = 0;
      for (var q = 0; q < ents.length; q++) {
        if (ents[q].alive && !live[ents[q].team]) { live[ents[q].team] = 1; nTeams++; }
      }
      if (nTeams === 1) {
        var champ = null;
        for (var q2 = 0; q2 < locals.length; q2++) if (locals[q2].alive) champ = locals[q2];
        lastWinner = champ;
        finish(true, squad > 1 ? 'Your squad is the last one moving.'
                   : ((locals.length > 1) ? champ.name + ' is the last one standing.' : 'Last one standing. Nothing left to hear.'), 1);
      }
    }
  }
  // Whatever they were carrying hits the floor, whatever the mode.
  function dropKit(e) {
    function put(type, key, ammo, n) {
      loot.push({
        x: e.x + rr(-16, 16), y: e.y + rr(-16, 16), type: type, key: key || null,
        spin: rr(0, 6.2832), ammo: ammo || 0, n: n || 0, seen: false
      });
    }
    // Most fighters die mid-fight with an empty magazine, so their guns hit
    // the floor dry and read as useless. Spend their spare rounds loading the
    // guns first; only what is left over drops as a box.
    var pool = (e.reserve > 0 && e.reserve < 9000) ? e.reserve : 0;
    if (e.reserve >= 9000) pool = 60;                  // gun game: no finite reserve
    for (var sx2 = 0; sx2 < 2; sx2++) {
      var ds = e.slots[sx2];
      if (!ds || !WEAPONS[ds.key]) continue;
      var fill = Math.max(0, Math.min(WEAPONS[ds.key].mag - ds.ammo, pool));
      pool -= fill;
      put('gun', ds.key, ds.ammo + fill, 0);
    }
    if (pool > 10) put('ammo', null, 0, Math.min(60, pool));
    while (e.meds > 0) { put('med', null, 0, 1); e.meds--; }
    while (e.nades > 0) { put('nade', null, 0, 1); e.nades--; }
    while (e.smokes > 0) { put('smoke', null, 0, 1); e.smokes--; }
    if (loot.length > 900) loot.splice(0, loot.length - 900);
  }

  function dist(a, b) { var dx = a.x - b.x, dy = a.y - b.y; return Math.sqrt(dx * dx + dy * dy); }

  // `won` arrives from the host's side of things; turn it into this person's.
  function wonFor(e, hostWon) {
    if (MODE.teams || MODE.zombies) return e.team === player.team ? hostWon : !hostWon;
    if (!lastWinner) return false;
    return lastWinner === e || (squad > 1 && lastWinner.team === e.team);
  }
  function finishAfterCam(e, won, msg, place) {
    if (e.kc) { e.kc.after = [won, msg, place]; return; }
    finish(won, msg, place);
  }
  function killcamTick(dt) {
    for (var i = 0; i < locals.length; i++) {
      var L = locals[i], kc = L.kc;
      if (!kc) continue;
      kc.t += dt;
      // over when it has run, or the moment they are back on their feet
      var done = kc.t >= kc.dur || (L.alive && kc.t > 0.4);
      if (!kc.k.alive && kc.t > 1.4) done = true;                   // the killer died too
      if (!done) continue;
      L.kc = null;
      if (kc.after && state === 'play') finish(kc.after[0], kc.after[1], kc.after[2]);
    }
  }
  function finish(won, msg, place) {
    cgGame('gameplayStop');
    // With several people playing, each wins or loses for their own side.
    var hostSide = won;
    if (locals.length > 1) won = wonFor(player, hostSide);
    var vsRes = splitVs() ? [won, wonFor(locals[1], hostSide)] : null;
    for (var gz = 0; gz < netGuests.length; gz++) {
      var gg = netGuests[gz];
      if (gg.ent) netSendOver(gg, wonFor(gg.ent, hostSide), msg, gg.ent.alive ? 1 : (gg.ent.place || place));
    }
    var big, small;
    if (mode === 'br') { big = '#' + place; small = 'OF ' + fieldN; }
    else if (mode === 'duel') { big = won ? 'WIN' : 'LOSS'; small = score[player.team] + ' \u2014 ' + score[1 - player.team]; }
    else if (MODE.teams) {
      big = won ? 'WIN' : 'LOSS';
      small = score[player.team] + ' \u2014 ' + score[1 - player.team];
    }
    else {
      big = won ? 'WIN' : 'LOSS';
      small = 'LEVEL ' + Math.min(player.level + 1, LADDER.length) + ' / ' + LADDER.length;
    }
    if (won) cgGame('happytime');
    var earned = kills * 12 + Math.round(matchTime / 6) + (won ? 80 : 0);
    WALLET.coins += earned;
    saveWallet();
    result = { big: big, small: small, won: won, earned: earned };
    overCause = msg + '  +' + earned + ' credits.';
    state = 'ending';
    // Everything the results screen needs is captured now: if a new match has
    // started by the time this fires, it must leave that match alone.
    var tok = matchToken, res = result, why = overCause, vs = vsRes;
    var k = kills, t = matchTime, sh = shots, ht = hits;
    setTimeout(function () {
      if (tok !== matchToken) return;
      state = 'over';
      $('placeN').textContent = res.big;
      $('placeN').className = res.won ? 'win' : '';
      $('placeL').textContent = res.small;
      // versus on one screen: each half gets its own verdict
      $('vsRes').hidden = !vs;
      document.querySelector('#over .place').hidden = !!vs;
      if (vs) {
        [['vsL', vs[0], 'P1'], ['vsR', vs[1], 'P2']].forEach(function (v) {
          var el = $(v[0]);
          el.className = 'vshalf ' + (v[1] ? 'win' : 'loss');
          el.querySelector('b').textContent = v[1] ? 'VICTORY' : 'LOSS';
          el.querySelector('s').textContent = v[2];
        });
        $('vsRes').className = 'vsres ' + (cw >= ch ? 'side' : 'stack');
      }
      $('overMsg').textContent = why;
      $('stKills').textContent = k;
      $('stTime').textContent = fmtTime(t);
      $('stAcc').textContent = (sh ? Math.round(ht / sh * 100) : 0) + '%';
      elHud.hidden = true;
      elOver.hidden = false;
      if (netRole === 'host' && netPublic) {
        $('overMsg').textContent = why + '  Next match in 10s.';
        setTimeout(function () {
          if (tok === matchToken && state === 'over' && netRole === 'host' && netPublic) startMatch();
        }, 10000);
      }
    }, 850);
  }

  // ---------------------------------------------------------------- movement
  function solid(x, y, r) {
    var x0 = Math.floor((x - r) / TILE), x1 = Math.floor((x + r) / TILE);
    var y0 = Math.floor((y - r) / TILE), y1 = Math.floor((y + r) / TILE);
    for (var ty = y0; ty <= y1; ty++) for (var tx = x0; tx <= x1; tx++) if (isWall(tx, ty)) return true;
    return false;
  }
  function moveEnt(e, dx, dy) {
    if (dx) { e.x += dx; if (solid(e.x, e.y, e.r)) e.x -= dx; }
    if (dy) { e.y += dy; if (solid(e.x, e.y, e.r)) e.y -= dy; }
  }
  function footstep(e, dt, sprinting) {
    e.stepT -= dt;
    if (e.stepT <= 0) {
      e.stepT = sprinting ? 0.27 : 0.44;
      emit(e.x, e.y, sprinting ? MOVE_SND.sprint : MOVE_SND.walk, e.id, sprinting ? 'sprint' : 'walk');
    }
  }
  function followPath(e, dt, speed) {
    if (!e.path || e.pathI >= e.path.length) return false;
    var look = Math.min(e.path.length - 1, e.pathI + 8);
    for (var i = look; i > e.pathI; i--) {
      if (lineClear(e.x, e.y, e.path[i].x, e.path[i].y)) { e.pathI = i; break; }
    }
    var w = e.path[e.pathI];
    var dx = w.x - e.x, dy = w.y - e.y;
    var d = Math.sqrt(dx * dx + dy * dy);
    if (d < 15) { e.pathI++; return true; }
    moveEnt(e, dx / d * speed * dt, dy / d * speed * dt);
    return true;
  }
  function pathTo(e, gx, gy, cool) {
    e.path = findPath(Math.floor(e.x / TILE), Math.floor(e.y / TILE), Math.floor(gx / TILE), Math.floor(gy / TILE));
    e.pathI = 0;
    // nothing usable came back - try again shortly rather than standing about
    e.repathT = (e.path && e.path.length) ? cool : 0.4;
  }

  // ---------------------------------------------------------------- AI
  function botThink(e, dt) {
    var D = DIFF[difficulty];

    // healing: like a player, a bot can keep moving while the stim goes in
    // (it just cannot shoot) - freezing on the spot left them standing in
    // the storm
    if (e.useT > 0) {
      e.useT -= dt;
      if (e.useT <= 0) { e.hp = Math.min(100, e.hp + 45); e.bleeding = false; }
    }

    // --- senses
    e.senseT -= dt;
    if (e.senseT <= 0) {
      e.senseT = 0.15;
      // In blackout nobody can see - bots go as blind as you do and have to
      // work off sound and muzzle flashes like everyone else.
      var sightR = blackout ? VIEW_BLACKOUT * (0.95 + difficulty * 0.13) : D.sight;
      var best = null, bestScore = -1, curScore = -1;
      for (var i = 0; i < ents.length; i++) {
        var o = ents[i];
        if (o === e || !o.alive || o.air || !foes(e, o)) continue;
        var d = dist(e, o);
        // In a free-for-all every face is an enemy. Only pick a NEW fight up
        // close - unless you are carrying the sniper - and keep your current
        // one out to full sight.
        var reach2 = sightR;
        if (mode === 'br' && o !== e.target) {
          var cw3 = curW(e);
          if (!(cw3 && cw3.snd.maxR >= 1900)) reach2 = sightR * 0.62;
        }
        if (d >= reach2 || !sightClear(e.x, e.y, o.x, o.y)) continue;
        if (o !== e.target && !inCone(e, o.x, o.y, FOV_HALF + 0.15)) continue;
        if (mode === 'br' && o !== e.target) {
          if ((e.skip[o.id] || 0) > matchTime) continue;          // already let them go
          if (e.skip[o.id] === undefined || e.skip[o.id] <= matchTime) {
            // early on most people avoid a fight; later it is kill or be killed
            var takeIt = Math.random() < (matchTime < 75 ? 0.3 : 0.62);
            if (!takeIt) { e.skip[o.id] = matchTime + rr(4, 8); continue; }
            e.skip[o.id] = -1;                                    // decided: fight
          }
        }
        var sc = (1 - d / sightR) + (1 - o.hp / 100) * 0.6;   // finish the wounded one
        if (o === e.target) curScore = sc;
        if (sc > bestScore) { bestScore = sc; best = o; }
      }
      // Stay on whoever you are already shooting while they are in sight,
      // unless someone else is clearly the better shot. Flipping between
      // targets every tick used to keep resetting the reaction delay, so a
      // bot would fire once and then never again.
      if (best && e.target && best !== e.target && curScore >= 0 && bestScore < curScore + 0.3) {
        best = e.target;
      }
      // the infected do not need to see you
      if (!best && isZombie(e)) {
        var near2 = null, nd2 = 520;
        for (var zi = 0; zi < ents.length; zi++) {
          var zo = ents[zi];
          if (!zo.alive || zo.team === e.team) continue;
          var zd = dist(e, zo);
          if (zd < nd2) { nd2 = zd; near2 = zo; }
        }
        best = near2;
      }
      if (best) {
        if (e.target !== best) {
          e.reactT = e.target ? D.react * 0.3 : D.react;   // already fighting: quick switch
          targetSwaps++;
        }
        e.target = best; e.lostT = 0;
        e.alertX = best.x; e.alertY = best.y; e.alertT = 6;
      } else if (e.target) {
        e.lostT += 0.15;
        if (e.lostT > (mode === 'br' ? 0.45 : 1.4)) { e.target = null; e.path = null; }
      }
    }
    if (e.target && !e.target.alive) { e.target = null; e.path = null; }
    if (e.alertT > 0) e.alertT -= dt;
    if (e.reactT > 0) e.reactT -= dt;

    autoPickup(e);
    var w = curW(e), slot = curSlot(e);

    var dry = !w || (slot.ammo <= 0 && e.reserve <= 0);
    var zd = 0, outside = false, zgx = 0, zgy = 0, zgr = 0;
    if (zone) {
      var zdx = e.x - zone.cx, zdy = e.y - zone.cy;
      zd = Math.sqrt(zdx * zdx + zdy * zdy);
      outside = zd > zone.r - 40;
      zgx = zone.cx; zgy = zone.cy; zgr = zone.r;
      // the circle is shrinking: get inside where it will stop, not where it is
      if (zone.closing) {
        var tdx = e.x - zone.tx, tdy = e.y - zone.ty, td = Math.sqrt(tdx * tdx + tdy * tdy);
        if (td > zone.shrinkTo - 50) { outside = true; zgx = zone.tx; zgy = zone.ty; zgr = zone.shrinkTo; zd = td; }
      }
    }
    var speed = isZombie(e) ? 150 : (w ? 165 : 186);
    e.repathT -= dt;

    // Reloading in the open is how bots die - break contact while they do it.
    // carrying the flag outranks every other instinct
    var carrying = MODE.ctf && flags.length === 2 && flags[1 - e.team].carrier === e;
    // a squadmate on the floor within arm's reach: stand still and work
    var picking = null;
    for (var pv = 0; pv < ents.length; pv++) {
      var pc = ents[pv];
      if (pc !== e && pc.alive && pc.down && pc.team === e.team && dist(e, pc) < 26) { picking = pc; break; }
    }
    e.nadeT -= dt;
    e.smokeT -= dt;
    // Nothing to fight with: run from anyone who does, and from gunfire.
    // An empty-handed stranger is no threat - keep looting past them.
    var threat = null;
    if (dry && !isZombie(e)) {
      if (e.target && curW(e.target)) threat = e.target;
      else if (e.alertT > 0 && e.alertShot) threat = { x: e.alertX, y: e.alertY };
    }
    var reloadRetreat = D.smart && e.reloadT > 0 && e.target && dist(e, e.target) < 420;
    var hurtRetreat = D.smart && e.hp < 34 && e.meds > 0 && e.target && dist(e, e.target) > 260;

    if (outside) {
      speed = w ? 232 : 254;
      if (!e.path || e.repathT <= 0) {
        pathTo(e, zgx + ((e.x - zgx) / (zd || 1)) * zgr * 0.45,
                  zgy + ((e.y - zgy) / (zd || 1)) * zgr * 0.45, 2.2);
      }
      followPath(e, dt, speed);
      footstep(e, dt, true);
    } else if (isZombie(e) && e.target) {
      // straight at them, no cover, no hesitation
      var zt = e.target;
      var zdx = zt.x - e.x, zdy = zt.y - e.y;
      var zl = Math.sqrt(zdx * zdx + zdy * zdy) || 1;
      var zspeed = 150;
      var zbx = e.x, zby = e.y;
      moveEnt(e, zdx / zl * zspeed * dt, zdy / zl * zspeed * dt);
      if (Math.abs(e.x - zbx) + Math.abs(e.y - zby) < zspeed * dt * 0.4) {
        if (!e.path || e.repathT <= 0) pathTo(e, zt.x, zt.y, 0.7);
        followPath(e, dt, zspeed);
      }
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
    } else if (threat) {
      // Pick somewhere well away from the danger and sprint for it. Running in
      // a straight line away just pins them against the nearest wall.
      if (!e.path || e.pathI >= e.path.length || e.repathT <= 0) {
        var here = dist(e, threat), bestT = null, bestS = -1e9;
        for (var ft = 0; ft < 18; ft++) {
          var cand = floorTiles[rnd(floorTiles.length)];
          var cx5 = cand.x * TILE, cy5 = cand.y * TILE;
          var dT = Math.sqrt((cx5 - threat.x) * (cx5 - threat.x) + (cy5 - threat.y) * (cy5 - threat.y));
          var dM = Math.sqrt((cx5 - e.x) * (cx5 - e.x) + (cy5 - e.y) * (cy5 - e.y));
          if (dT < here + 120 || dM > 900) continue;
          var sc5 = dT - dM * 0.35;
          if (sc5 > bestS) { bestS = sc5; bestT = cand; }
        }
        if (bestT) pathTo(e, bestT.x * TILE, bestT.y * TILE, 1.1);
        else e.repathT = 0.3;
      }
      if (!followPath(e, dt, 254)) {
        // no route yet: at least get out of the line of fire
        var tdx = e.x - threat.x, tdy = e.y - threat.y, tl = Math.sqrt(tdx * tdx + tdy * tdy) || 1;
        moveEnt(e, tdx / tl * 254 * dt, tdy / tl * 254 * dt);
      }
      footstep(e, dt, true);
    } else if ((reloadRetreat || hurtRetreat) && e.target) {
      // back off - reloading, or patching up
      var fspeed = 200;
      var fdx = e.x - e.target.x, fdy = e.y - e.target.y;
      var fl = Math.sqrt(fdx * fdx + fdy * fdy) || 1;
      var bx0 = e.x, by0 = e.y;
      moveEnt(e, fdx / fl * fspeed * dt, fdy / fl * fspeed * dt);
      if (Math.abs(e.x - bx0) + Math.abs(e.y - by0) < fspeed * dt * 0.4) {
        // cornered - slide sideways instead of grinding into the wall
        moveEnt(e, -fdy / fl * fspeed * dt * e.strafe, fdx / fl * fspeed * dt * e.strafe);
        e.strafe *= -1;
      }
      footstep(e, dt, false);
      if (hurtRetreat && !lineClear(e.x, e.y, e.target.x, e.target.y)) useMed(e);
    } else if (dry) {
      if (!e.lootGoal || e.repathT <= 0 || loot.indexOf(e.lootGoal) < 0) {
        e.lootGoal = nearestLoot(e, w ? 'ammo' : 'gun', 1400) || nearestLoot(e, w ? 'gun' : 'ammo', 1400);
        if (e.lootGoal) pathTo(e, e.lootGoal.x, e.lootGoal.y, 2.0);
        else { var rt = floorTiles[rnd(floorTiles.length)]; pathTo(e, rt.x * TILE, rt.y * TILE, 3.0); }
      }
      if (followPath(e, dt, speed)) footstep(e, dt, false);
    } else if (e.target && e.reactT <= 0 && mode !== 'br' && !sightClear(e.x, e.y, e.target.x, e.target.y)) {
      // They ducked behind something. Strafing on the spot never gets the
      // shot back - push to where they were last seen and take the corner.
      if (!e.path || e.pathI >= e.path.length || e.repathT <= 0) pathTo(e, e.alertX, e.alertY, 0.6);
      if (!followPath(e, dt, speed)) {
        var cdx = e.alertX - e.x, cdy = e.alertY - e.y, cl2 = Math.sqrt(cdx * cdx + cdy * cdy) || 1;
        moveEnt(e, cdx / cl2 * speed * dt, cdy / cl2 * speed * dt);
      }
      footstep(e, dt, false);
    } else if (e.target && e.reactT <= 0) {
      var t = e.target, td = dist(e, t);
      e.swapT -= dt;
      if (e.swapT <= 0) {
        e.swapT = 0.8;
        var wantSlot = bestSlotFor(e, td);
        if (wantSlot !== e.slot) {
          e.slot = wantSlot; e.reloadT = 0;
          e.fireT = Math.max(e.fireT, 0.3);          // swapping costs you a beat
          w = curW(e); slot = curSlot(e);
        }
      }
      var ux = (t.x - e.x) / (td || 1), uy = (t.y - e.y) / (td || 1);
      e.strafeT -= dt;
      if (e.strafeT <= 0) { e.strafe *= -1; e.strafeT = rr(0.7, 1.8); }
      var ideal = w.pellets > 1 ? 140 : (w.snd.maxR > 1800 ? 340 : 250);
      var mx = 0, my = 0;
      if (td > ideal * 1.3) { mx += ux; my += uy; }
      else if (td < ideal * 0.6) { mx -= ux; my -= uy; }
      mx += -uy * e.strafe * 0.9; my += ux * e.strafe * 0.9;
      var ml = Math.sqrt(mx * mx + my * my) || 1;
      // good shots plant their feet for a moment
      var mv = (D.smart && e.fireT > 0 && e.burst > 0) ? 0.45 : 1;
      var px0 = e.x, py0 = e.y;
      moveEnt(e, mx / ml * speed * mv * dt, my / ml * speed * mv * dt);
      if (Math.abs(e.x - px0) + Math.abs(e.y - py0) < speed * mv * dt * 0.4) e.strafe *= -1;
      footstep(e, dt, false);
      e.path = null;
    } else {
      if (e.hp < 48 && e.meds > 0 && e.reloadT <= 0) useMed(e);
      var goal = null;
      if (e.alertT > 0) {
        goal = { x: e.alertX, y: e.alertY };
        // don't walk straight down the barrel - come at the noise off-axis
        if (D.smart) {
          var aa = Math.atan2(e.alertY - e.y, e.alertX - e.x) + (e.strafe * 0.7);
          var ad = Math.max(60, dist(e, { x: e.alertX, y: e.alertY }) * 0.7);
          goal = { x: e.alertX - Math.cos(aa) * ad * 0.35, y: e.alertY - Math.sin(aa) * ad * 0.35 };
        }
      }
      if (!e.path || e.pathI >= e.path.length || e.repathT <= 0) {
        if (!goal) {
          var want = null, following = false;
          if (MODE.loot) {
            if (e.hp < 65 && e.meds === 0) want = nearestLoot(e, 'med', 800);
            if (!want && e.reserve < (mode === 'br' ? 80 : 40)) want = nearestLoot(e, 'ammo', 700);
            // fill both hands before going looking for trouble
            if (!want && mode === 'br' && (!e.slots[0] || !e.slots[1])) want = nearestLoot(e, 'gun', 900);
          }
          // squadmates regroup on you instead of wandering off alone
          if (MODE.sectors && sectors.length) {
            var post = (e.id + Math.floor(matchTime / 28)) % sectors.length;
            var pick = sectors[post];
            if (pick.owner === e.team) {
              // ours already - go help somewhere it is not
              for (var si = 1; si < sectors.length; si++) {
                var alt = sectors[(post + si) % sectors.length];
                if (alt.owner !== e.team) { pick = alt; break; }
              }
            }
            want = { x: pick.x + rr(-70, 70), y: pick.y + rr(-70, 70) };
            following = true;
          }
          if (MODE.ctf && flags.length === 2) {
            var ours = flags[e.team], theirs = flags[1 - e.team];
            if (theirs.carrier === e) want = { x: ours.hx, y: ours.hy };          // run it home
            else if (!ours.home && !ours.carrier) want = { x: ours.x, y: ours.y }; // recover ours
            else if (!theirs.carrier) want = { x: theirs.x, y: theirs.y };         // go get theirs
            else if (theirs.carrier.team === e.team) want = { x: theirs.carrier.x, y: theirs.carrier.y };
            else want = { x: ours.hx, y: ours.hy };                                // hold home
            if (want) following = true;
          }
          // a downed squadmate outranks anything else lying around
          var hurt = null, hurtD = 900;
          for (var dq = 0; dq < ents.length; dq++) {
            var cand = ents[dq];
            if (!cand.alive || !cand.down || cand.team !== e.team) continue;
            var cd = dist(e, cand);
            if (cd < hurtD) { hurtD = cd; hurt = cand; }
          }
          if (hurt) { want = { x: hurt.x, y: hurt.y }; following = true; }
          if (!want && player.alive && !player.air && e.team === player.team && dist(e, player) > 230) {
            want = { x: player.x, y: player.y };
            following = true;
          }
          if (!want && zone && !zone.closing && zone.nr) {
            // rotate into the next ring early instead of getting caught out
            var ndx = e.x - zone.nx, ndy = e.y - zone.ny;
            if (Math.sqrt(ndx * ndx + ndy * ndy) > zone.nr - 60) want = { x: zone.nx, y: zone.ny };
          }
          // In battle royale the zone brings people together; hunting on top
          // of it turned the first minute into a bloodbath. Elsewhere there
          // is nothing else to close the distance, so they go looking.
          if (!want && Math.random() < (mode === 'br' ? 0.18 : 0.7)) {
            var hunt = [];
            for (var hq = 0; hq < ents.length; hq++) {
              var ho = ents[hq];
              if (ho.alive && foes(e, ho)) hunt.push(ho);
            }
            if (hunt.length) {
              var mark = hunt[rnd(hunt.length)];
              want = { x: mark.x + rr(-140, 140), y: mark.y + rr(-140, 140) };
            }
          }
          if (want) goal = want;
          else {
            var ft2 = floorTiles[rnd(floorTiles.length)];
            if (zone) {
              var gdx = ft2.x * TILE - zone.cx, gdy = ft2.y * TILE - zone.cy;
              if (Math.sqrt(gdx * gdx + gdy * gdy) > zone.r * 0.8) ft2 = { x: Math.floor(zone.cx / TILE), y: Math.floor(zone.cy / TILE) };
            }
            goal = { x: ft2.x * TILE, y: ft2.y * TILE };
          }
        }
        pathTo(e, goal.x, goal.y, following ? 0.9 : (e.alertT > 0 ? 1.2 : 3.4));
      }
      if (followPath(e, dt, speed)) footstep(e, dt, false);
    }

    // --- grenades. Thrown at something they can actually see, pitched to
    //     land on it, and never onto their own side.
    if (e.nades > 0 && e.nadeT <= 0 && teamNadeT[e.team] <= 0 && !e.down) {
      var gt = e.target;                      // something they can see, not a rumour
      if (gt) {
        var gd = dist(e, gt);
        var recently = gt.fragAt !== undefined && matchTime - gt.fragAt < 10;
        if (!recently && gd > 140 && gd < 330 && lineClear(e.x, e.y, gt.x, gt.y)) {
          var clear = true;
          for (var fq = 0; fq < ents.length; fq++) {
            var fm = ents[fq];
            if (fm === e || !fm.alive || foes(e, fm)) continue;
            if (dist(fm, gt) < 150) { clear = false; break; }
          }
          if (clear) {
            var ga3 = Math.atan2(gt.y - e.y, gt.x - e.x) + rr(-0.09, 0.09);
            throwNade(e, 'frag', ga3, throwPower(gd));
            gt.fragAt = matchTime;             // nobody else frags them for a while
            botFrags++;
            e.nadeT = rr(D.smart ? 12 : 22, D.smart ? 24 : 40);
            teamNadeT[e.team] = rr(6, 10);
            e.fireT = Math.max(e.fireT, 0.45);
          }
        }
      }
    }

    // --- smoke, to break a line they are losing
    if (D.smart && e.smokes > 0 && e.smokeT <= 0 && e.target && !e.down) {
      var wantSmoke = (e.hp < 45) || dry || (reloadRetreat && e.hp < 70) || carrying;
      var sd2 = dist(e, e.target);
      if (wantSmoke && sd2 > 90 && sd2 < 420 && lineClear(e.x, e.y, e.target.x, e.target.y)) {
        var sa3 = Math.atan2(e.target.y - e.y, e.target.x - e.x);
        throwNade(e, 'smoke', sa3, throwPower(sd2 * 0.55));
        e.smokeT = rr(26, 48);
      }
    }

    // --- stuck detection
    e.stuckT += dt;
    if (e.stuckT > 0.7) {
      if (Math.abs(e.x - e.lastX) + Math.abs(e.y - e.lastY) < 10) {
        e.path = null; e.repathT = 0.25; e.alertT = 0; e.lootGoal = null; e.strafe *= -1;
        // nudge free of whatever corner has them
        moveEnt(e, rr(-14, 14), rr(-14, 14));
      }
      e.lastX = e.x; e.lastY = e.y; e.stuckT = 0;
    }

    // --- aim & shoot
    e.fireT -= dt;
    if (e.flinch > 0) e.flinch -= dt;
    if (e.reloadT > 0) {
      e.reloadT -= dt;
      if (e.reloadT <= 0) finishReload(e);
    }
    if (!w) {
      // Empty-handed - the infected included. Turn to face whoever you are
      // coming for the whole way in, not only once you are on top of them.
      if (e.target && e.alive) {
        var mdiff = ((Math.atan2(e.target.y - e.y, e.target.x - e.x) - e.ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
        e.ang += clamp(mdiff, -D.turn * dt, D.turn * dt);
        if (dist(e, e.target) < 38 && Math.abs(mdiff) < 0.7) melee(e);
      } else if (e.path && e.pathI < e.path.length) {
        var wp = e.path[e.pathI];
        var wdiff = ((Math.atan2(wp.y - e.y, wp.x - e.x) - e.ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
        e.ang += clamp(wdiff, -D.turn * 0.7 * dt, D.turn * 0.7 * dt);
      }
      return;
    }

    if (e.target && e.reactT <= 0) {
      var tt = e.target, dd = dist(e, tt);
      // lead the shot by the target's own velocity over the bullet's flight
      var tof = dd / w.speed;
      // The hand trails the eye: aim at where they were a moment ago, catching
      // up at this bot's pace, and only half-guess where they are going. A
      // target that keeps moving is genuinely harder to hit.
      if (e.trkT !== tt) { e.trkT = tt; e.trkX = tt.x; e.trkY = tt.y; }
      var trk = 1 - Math.exp(-(D.track || 3) * dt);
      e.trkX += (tt.x - e.trkX) * trk; e.trkY += (tt.y - e.trkY) * trk;
      var aimX = e.trkX + tt.vx * tof * D.lead * 0.3;
      var aimY = e.trkY + tt.vy * tof * D.lead * 0.3;
      var want2 = Math.atan2(aimY - e.y, aimX - e.x);
      if (aimErrOn) want2 += aimError(e, tt, dd, dt, D);
      var diff = ((want2 - e.ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
      e.ang += clamp(diff, -D.turn * dt, D.turn * dt);
      var maxRange = w.pellets > 1 ? 250 : 620;
      // Pull the trigger whenever the barrel actually covers the target - the
      // angle the target subtends at this range, plus a small margin. This is
      // a decision to shoot, not an aimbot: where the round goes is still
      // governed by weapon spread, reaction delay and how fast they can turn.
      var angW = Math.atan2(tt.r + 3, Math.max(1, dd));
      var tol = Math.max(angW * 1.7, D.aimTol * 0.55);
      if (dd < maxRange && Math.abs(diff) < tol && sightClear(e.x, e.y, tt.x, tt.y) && !mateInLine(e, dd)) {
        if (slot.ammo <= 0 && e.reserve <= 0) { if (dd < 38) melee(e); }
        else if (slot.ammo <= 0) startReload(e);
        else {
          if (e.burst <= 0) e.burst = w.pellets > 1 ? 1 : (w.interval < 0.12 ? 6 + rnd(6) : 3 + rnd(3));
          if (fire(e)) {
            e.burst--;
            if (e.burst <= 0) e.fireT += rr(0.06, 0.16);
          }
        }
      }
      // top up the magazine the moment contact breaks
      if (!lineClear(e.x, e.y, tt.x, tt.y) && slot.ammo < w.mag * 0.5) startReload(e);
    } else {
      if (slot.ammo < w.mag * 0.5) startReload(e);
      var vx = 0, vy = 0;
      if (e.path && e.pathI < e.path.length) { vx = e.path[e.pathI].x - e.x; vy = e.path[e.pathI].y - e.y; }
      if (e.alertT > 0) { vx = e.alertX - e.x; vy = e.alertY - e.y; }
      if (vx || vy) {
        var wa = Math.atan2(vy, vx);
        var df = ((wa - e.ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
        e.ang += clamp(df, -D.turn * 0.6 * dt, D.turn * 0.6 * dt);
      }
    }
  }

  // Nobody fires through their own teammate, even if the round would pass.
  function mateInLine(e, range) {
    var cx = Math.cos(e.ang), cy = Math.sin(e.ang);
    for (var i = 0; i < ents.length; i++) {
      var m = ents[i];
      if (m === e || !m.alive || foes(e, m)) continue;
      var rx = m.x - e.x, ry = m.y - e.y;
      var along = rx * cx + ry * cy;
      if (along <= 0 || along > range) continue;
      var off = Math.abs(rx * cy - ry * cx);
      if (off < m.r + 7) return true;
    }
    return false;
  }

  // Where a bot's hand actually is, relative to a perfect line on the target.
  // A fresh target starts well off to one side and the shots walk in; after
  // that a slow sway stays, bigger when the target is strafing, the bot is
  // moving, or it has just been hit.
  function aimError(e, tt, dd, dt, D) {
    if (e.aimTgt !== tt) {
      e.aimTgt = tt;
      e.aimOff = (Math.random() < 0.5 ? -1 : 1) * rr(0.55, 1) * D.miss;
      e.aimPh = rr(0, 6.28); e.aimPh2 = rr(0, 6.28);
    }
    e.aimOff *= Math.exp(-D.settle * dt);
    // sideways speed of the target as seen from here, in radians per second
    var ux = (tt.x - e.x) / (dd || 1), uy = (tt.y - e.y) / (dd || 1);
    var lat = Math.abs((tt.vx || 0) * -uy + (tt.vy || 0) * ux) / Math.max(dd, 60);
    var sway = D.wob * (1 + Math.min(lat * 2.2, 1.6) + ((e._spd || 0) > 40 ? 0.6 : 0) + (e.flinch > 0 ? 1.2 : 0));
    var t = matchTime;
    return e.aimOff + sway * (Math.sin(t * 2.1 + e.aimPh) * 0.65 + Math.sin(t * 5.3 + e.aimPh2) * 0.35);
  }

  // ---------------------------------------------------------------- player
  // One set of controls, read from whatever device this player owns. A lone
  // player takes whichever is in use; in split screen each has their own.
  // A reload (and jump) - B drop (give up when downed) - X pick up - Y stim
  // LB/RB swap - LT sprint - RT fire - d-pad left frag, right smoke, up melee
  // (the right stick click melees too) - Start pause
  var PAD = { reload: 0, jump: 0, drop: 1, giveup: 1, pickup: 2, stim: 3, swapL: 4, swapR: 5,
              sprint: 6, fire: 7, pause: 9, melee2: 11, melee: 12, frag: 14, smoke: 15 };
  function inputFor(e) {
    var c = e.ctl || { any: true, kb: true };
    if (c.net) {
      var n = c.net.in;
      return {
        any: false, net: true, pad: true, kb: false, touch: false, padOn: true,
        hit: function (i) { var b = 1 << i; if (n.hits & b) { n.hits &= ~b; return true; } return false; },
        down: function (i) { return !!(n.down & (1 << i)); },
        ax: function (i) {
          if (i < 2) return n.ax[i] || 0;
          if (n.aim === null || n.aim === undefined) return 0;
          return i === 2 ? Math.cos(n.aim) : Math.sin(n.aim);
        }
      };
    }
    if (c.any) {
      return { any: true, pad: pad, hit: padHit, down: padDown, ax: padAxis,
               raw: function () { return pad && pad.axes.length > 3 ? [pad.axes[2], pad.axes[3]] : [0, 0]; },
               kb: true, touch: true, padOn: padActive() };
    }
    var g = getPad(c.pad);
    if (!e.padPrev) e.padPrev = {};
    if (g && padBusy(g)) e.padLast = performance.now();
    return {
      any: false, pad: g,
      hit: function (i) { return hitOf(g, e.padPrev, i); },
      down: function (i) { return downOf(g, i); },
      ax: function (i) { return axOf(g, i); },
      raw: function () { return g && g.axes.length > 3 ? [g.axes[2], g.axes[3]] : [0, 0]; },
      kb: !!c.kb, touch: false, padOn: usingPad(e)
    };
  }

  function updateLocal(e, dt) {
    var I = inputFor(e);
    if (!e.alive) { if (I.pad && I.hit(9)) pause(); return; }
    if (e.air) {
      e._spd = 0; e.prompt = null;
      if (e === player) promptItem = null;
      if (I.pad && I.hit(9)) { pause(); return; }
      airControl(e, I, dt);
      return;
    }
    if (e.down) {
      e._spd = 0; e.prompt = null;
      if (e === player) promptItem = null;
      if (I.pad && I.hit(1)) { e.hp = 0; kill(e, -1); }        // B gives up
      if (I.pad && I.hit(9)) pause();
      return;
    }
    autoPickup(e);

    e.prompt = null;
    var bestD = 26 * 26;
    for (var i = 0; i < loot.length; i++) {
      var it = loot[i];
      if (it.type !== 'gun') continue;
      var ddx = it.x - e.x, ddy = it.y - e.y, d2 = ddx * ddx + ddy * ddy;
      if (d2 < bestD) { bestD = d2; e.prompt = it; }
    }
    if (e === player) promptItem = e.prompt;

    if (e.useT > 0) {
      e.useT -= dt;
      if (e.useT <= 0) { e.hp = Math.min(100, e.hp + 45); e.bleeding = false; }
    }

    var ix = 0, iy = 0;
    var padMove = false;
    if (I.pad) {
      var lx = I.ax(0), ly = I.ax(1);
      if (lx || ly) {
        var ll = Math.sqrt(lx * lx + ly * ly);
        ix = lx / (ll > 1 ? ll : 1); iy = ly / (ll > 1 ? ll : 1);
        padMove = true;
      }
      if (I.hit(PAD.pickup)) playerPickup(e);
      if (I.hit(PAD.drop)) dropWeapon(e);
      if (I.hit(PAD.reload)) startReload(e);
      if (I.hit(PAD.stim)) useMed(e);
      if (I.hit(PAD.swapL) || I.hit(PAD.swapR)) swapSlot(undefined, e);
      if (I.hit(PAD.frag)) throwNade(e, 'frag');
      if (I.hit(PAD.smoke)) throwNade(e, 'smoke');
      if (I.hit(PAD.melee) || I.hit(PAD.melee2)) melee(e);
      if (I.hit(PAD.pause)) { pause(); return; }
    }
    if (!padMove && I.touch && sticks.move) {
      var sdx = sticks.move.x - sticks.move.ox, sdy = sticks.move.y - sticks.move.oy;
      var sl = Math.sqrt(sdx * sdx + sdy * sdy);
      if (sl > 8) { ix = sdx / sl; iy = sdy / sl; }
    } else if (!padMove && I.kb) {
      if (keys['a']) ix -= 1; if (keys['d']) ix += 1;
      if (keys['w']) iy -= 1; if (keys['s']) iy += 1;
      var l = Math.sqrt(ix * ix + iy * iy);
      if (l > 0) { ix /= l; iy /= l; }
    }
    var sprinting = ((I.kb && !!keys['shift']) || (!!I.pad && I.down(PAD.sprint))) && (ix || iy);
    var base = curW(e) ? 168 : (MODE.zombies && e.team === 1 ? 168 : 190);
    var speed = sprinting ? base * 1.45 : base;
    e._spd = (ix || iy) ? speed : 0;
    if (ix || iy) { moveEnt(e, ix * speed * dt, iy * speed * dt); footstep(e, dt, sprinting); }
    else e.stepT = 0.14;

    // Face the right stick if it is pushed; otherwise where you are walking on
    // a pad; otherwise the cursor. Never left pointing at nothing.
    // Right stick. Read raw, so the angle is true in every direction (a
    // per-axis deadzone bends diagonals). Any push past the deadzone means
    // "I am aiming" - walking never steals your aim then - but only a firm
    // push turns you, so a stick springing back to centre does not flick.
    var rx = 0, ry = 0, nowA = performance.now();
    if (I.net) { rx = I.ax(2); ry = I.ax(3); }
    else if (I.pad && I.raw) {
      var ra = I.raw(), rm = Math.sqrt(ra[0] * ra[0] + ra[1] * ra[1]), dz = SET.dead / 100;
      if (rm >= dz) {
        e.stickAimAt = nowA;
        if (rm >= dz + 0.1) { rx = ra[0]; ry = ra[1]; }
      }
    }
    var aimingStick = nowA - (e.stickAimAt || -1e9) < 600;
    if (rx || ry) {
      e.stickAimAt = nowA;
      e.ang = Math.atan2(ry, rx);
    } else if (aimingStick) {
      // holding the aim where the stick last put it
    } else if (I.touch && sticks.aim) {
      var adx = sticks.aim.x - sticks.aim.ox, ady = sticks.aim.y - sticks.aim.oy;
      if (Math.sqrt(adx * adx + ady * ady) > 10) e.ang = Math.atan2(ady, adx);
    } else if (I.kb && mouse.sx !== undefined && !I.padOn) {
      // on keyboard and mouse you always face the cursor, whatever you walk
      e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);
    }
    // walking never turns you: on a pad only the right stick aims

    e.fireT -= dt;
    if (e.reloadT > 0) {
      e.reloadT -= dt;
      if (e.reloadT <= 0) finishReload(e);
    }
    var firing = (I.kb && mouse.down) || (!!I.pad && I.down(7)) ||
      (I.touch && sticks.aim && Math.abs(sticks.aim.x - sticks.aim.ox) + Math.abs(sticks.aim.y - sticks.aim.oy) > 26);
    // semi-auto: a shot per press, not per held frame (a friend's quick click
    // arrives as a button press, so it is never lost between messages)
    var semiW = curW(e) && curW(e).semi;
    var pressed = I.net ? (I.hit(7) || (firing && !e.trigHeld)) : (firing && !e.trigHeld);
    e.trigHeld = firing;
    if (semiW && !pressed) firing = false;
    if (firing) {
      var cw2 = curW(e), cs2 = curSlot(e);
      if (!cw2 || (cs2.ammo <= 0 && e.reserve <= 0)) melee(e);   // nothing to shoot with
      else if (cs2.ammo <= 0) startReload(e);
      else fire(e);
    }
  }

  function playerPickup(e) {
    e = e || kbPlayer();
    var it = e.prompt;
    if (!it) return;
    var idx = loot.indexOf(it);
    if (idx >= 0) takeGun(e, it, idx);
    e.prompt = null;
    if (e === player) promptItem = null;
  }
  // Put down what is in your hands, loaded as it is, for a friend (or anyone).
  function dropWeapon(e) {
    if (!e || !e.alive || e.down || e.air || mode === 'gun') return;
    var sl = curSlot(e);
    if (!sl || !WEAPONS[sl.key]) return;
    loot.push({
      x: e.x + Math.cos(e.ang) * 20, y: e.y + Math.sin(e.ang) * 20, type: 'gun', key: sl.key,
      spin: rr(0, 6.2832), ammo: sl.ammo, n: 0, seen: true
    });
    e.slots[e.slot] = null;
    e.reloadT = 0;
    var other = e.slot === 0 ? 1 : 0;
    if (e.slots[other]) e.slot = other;
    audioEmit(e.x, e.y, PICK_SND, e.id);
  }
  function swapSlot(n, e) {
    e = e || kbPlayer();
    if (n === undefined) n = e.slot === 0 ? 1 : 0;
    if (!e.slots[n] || n === e.slot) return;
    e.slot = n; e.reloadT = 0;
  }

  // ---------------------------------------------------------------- sim
  function updateBullets(dt) {
    for (var i = bullets.length - 1; i >= 0; i--) {
      var b = bullets[i];
      b.life -= dt;
      if (b.life <= 0) { bullets.splice(i, 1); continue; }
      var steps = 4, dead = false;
      for (var s = 0; s < steps && !dead; s++) {
        b.x += b.vx * dt / steps; b.y += b.vy * dt / steps;
        if (wallAt(b.x, b.y)) {
          var mtx = Math.floor(b.x / TILE), mty = Math.floor(b.y / TILE);
          var hitMat = (mtx >= 0 && mty >= 0 && mtx < MAP_W && mty < MAP_H) ? mat[mty * STRIDE + mtx] : 1;
          // structures ring and spark; rock and scrub just throw dust
          var kind = hitMat === 2 ? 'impact' : 'impact_metal';
          spark(b.x, b.y, 3, kind === 'impact' ? '160,190,220' : '255,226,150', 80);
          if (FX[kind]) {
            if (impacts.length > 40) impacts.shift();
            impacts.push({ x: b.x, y: b.y, ang: Math.random() * 6.2832, t: 0, scale: rr(0.75, 1.15), fx: kind });
          }
          dead = true; break;
        }
        for (var j = 0; j < ents.length; j++) {
          var e = ents[j];
          if (!e.alive || e.air || e.id === b.owner) continue;
          if (ents[b.owner] && e.team === ents[b.owner].team) continue;
          var dx = e.x - b.x, dy = e.y - b.y;
          if (dx * dx + dy * dy < (e.r + 3) * (e.r + 3)) {
            if (onHere(ents[b.owner])) hits++;
            damage(e, b.dmg, b.owner, Math.atan2(b.vy, b.vx));
            dead = true; break;
          }
        }
      }
      if (dead) bullets.splice(i, 1);
    }
  }

  function updateSounds(dt) {
    var ear = DIFF[difficulty].ear;
    for (var i = sounds.length - 1; i >= 0; i--) {
      var s = sounds[i];
      s.r += s.speed * dt;
      if (s.r > s.maxR) { sounds.splice(i, 1); continue; }
      for (var j = 0; j < ents.length; j++) {
        var e = ents[j];
        if (!e.bot || !e.alive || e.id === s.owner || s.heard[e.id]) continue;
        if (ents[s.owner] && ents[s.owner].team === e.team) { s.heard[e.id] = 1; continue; }
        var dx = e.x - s.x, dy = e.y - s.y;
        var d = Math.sqrt(dx * dx + dy * dy);
        if (d > s.maxR * ear) { s.heard[e.id] = 1; continue; }
        if (d <= s.r) {
          s.heard[e.id] = 1;
          // In battle royale, a distant firefight is usually someone else's
          // problem - most bots keep looting instead of all piling in.
          var shrug = mode === 'br' && s.kind === 'shot' && d > 450 && Math.random() < 0.68;
          if (!e.target && !shrug) {
            // sharper ears place the noise more precisely
            var err = 60 * (1.6 - ear);
            e.alertX = s.x + rr(-err, err); e.alertY = s.y + rr(-err, err);
            e.alertT = s.kind === 'shot' ? 7 : 4;
            e.alertShot = s.kind === 'shot';
            e.path = null; e.repathT = 0;
          }
        }
      }
    }
  }

  // Choosing the next circle at the START of the wait phase lets the preview
  // ring show where it will actually be, and lets bots rotate into it early.
  function planNextRing() {
    var P = PHASES[Math.min(zone.phase, PHASES.length - 1)];
    zone.nr = zone.span * P.f;
    var maxOff = Math.max(0, zone.r - zone.nr);
    var a = Math.random() * Math.PI * 2, off = Math.random() * maxOff;
    zone.nx = clamp(zone.cx + Math.cos(a) * off, zone.nr + 60, WORLD_W - zone.nr - 60);
    zone.ny = clamp(zone.cy + Math.sin(a) * off, zone.nr + 60, WORLD_H - zone.nr - 60);
  }

  function updateZone(dt) {
    var P = PHASES[Math.min(zone.phase, PHASES.length - 1)];
    zone.dps = P.dps;
    zone.timer -= dt;
    if (!zone.closing) {
      if (zone.timer <= 0) {
        zone.closing = true;
        zone.timer = P.shrink; zone.dur = P.shrink;
        zone.shrinkFrom = zone.r; zone.shrinkTo = zone.nr;
        zone.fromX = zone.cx; zone.fromY = zone.cy;
        zone.tx = zone.nx; zone.ty = zone.ny;
      }
    } else {
      var k = 1 - clamp(zone.timer / zone.dur, 0, 1);
      zone.r = zone.shrinkFrom + (zone.shrinkTo - zone.shrinkFrom) * k;
      zone.cx = zone.fromX + (zone.tx - zone.fromX) * k;
      zone.cy = zone.fromY + (zone.ty - zone.fromY) * k;
      if (zone.timer <= 0) {
        zone.closing = false;
        zone.r = zone.shrinkTo; zone.cx = zone.tx; zone.cy = zone.ty;
        zone.phase = Math.min(zone.phase + 1, PHASES.length - 1);
        zone.timer = PHASES[zone.phase].wait;
        planNextRing();
      }
    }
    for (var i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e.alive || e.air) continue;
      var dx = e.x - zone.cx, dy = e.y - zone.cy;
      if (Math.sqrt(dx * dx + dy * dy) > zone.r) {
        if (!(godMode && e === player)) e.hp -= zone.dps * dt;
        if (e.hp <= 0) kill(e, -1);
        else if (e.local && Math.random() < dt * 3) dmgMarks.push({ ang: Math.atan2(dy, dx), t: 0.5, who: e.id });
      }
    }
  }

  function update(dt) {
    matchTime += dt;
    var i, e;

    // velocity, for the bots' lead prediction
    for (i = 0; i < ents.length; i++) {
      e = ents[i];
      e.vx = (e.x - e.px) / dt; e.vy = (e.y - e.py) / dt;
      e.px = e.x; e.py = e.y;
      var spd = Math.sqrt(e.vx * e.vx + e.vy * e.vy);
      e.moving = spd > 14;
      if (e.moving) e.animT += dt * (spd > 210 ? 1.5 : 1);   // sprinting strides faster
      if (e.animFire > 0) e.animFire -= dt;
      if (e.meleeT > 0) e.meleeT -= dt;
      if (e.swingT > 0) e.swingT -= dt;
      if (e.throwT > 0) e.throwT -= dt;
    }

    pollPad();
    updateMouseWorld();
    updateDrop(dt);
    for (i = 0; i < locals.length; i++) updateLocal(locals[i], dt);
    if (state !== 'play') return;
    for (i = 0; i < ents.length; i++) {
      e = ents[i];
      if (e.bot && e.alive && !e.down && !e.air && !e.dummy) botThink(e, dt);
    }
    updateBullets(dt);
    updateNades(dt);
    updateSmoke(dt);
    if (teamNadeT[0] > 0) teamNadeT[0] -= dt;
    if (teamNadeT[1] > 0) teamNadeT[1] -= dt;
    if (MODE.ctf && state === 'play') updateFlags(dt);
    if (MODE.sectors && state === 'play') updateSectors(dt);
    if (MODE.zombies && state === 'play') {
      zombClock -= dt;
      zombSpawnT -= dt;
      if (zombSpawnT <= 0) {
        var gone = 1 - clamp(zombClock / MODE.clock, 0, 1);   // 0 at the start, 1 at the end
        zombSpawnT = 13 - 7 * gone;                            // a wave, then a lull
        spawnZombie();
      }
      var living = 0;
      for (i = 0; i < ents.length; i++) if (ents[i].alive && ents[i].team === 0) living++;
      if (living === 0) {
        finish(player.team === 1, player.team === 1
          ? 'Nothing left breathing. The infected take it.'
          : 'The last of the living went down.');
      } else if (zombClock <= 0) {
        finish(player.team === 0, player.team === 0
          ? 'You held out. The living take it.'
          : 'They lasted the clock out.');
      }
    }
    updateSounds(dt);
    if (zone) updateZone(dt);

    for (i = 0; i < ents.length; i++) {
      e = ents[i];
      if (!e.alive || !e.down) continue;
      var medic = null;
      for (var j2 = 0; j2 < ents.length; j2++) {
        var m2 = ents[j2];
        if (m2 === e || !m2.alive || m2.down || m2.air || m2.team !== e.team) continue;
        if (dist(m2, e) < 30) { medic = m2; break; }
      }
      if (medic) {
        e.revT += dt;
        if (e.revT >= 2.6) {
          e.down = false; e.revT = 0; e.downT = 0; e.downedBy = -1; e.bleeding = false;
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

    for (i = 0; i < ents.length; i++) {
      var bl = ents[i];
      if (!bl.alive || !bl.bleeding || bl.down || bl.air) continue;
      if (godMode && bl === player) continue;
      var bd = Math.min(1 * dt, bl.bleedLeft || 0);    // 1 HP a second
      bl.hp -= bd; bl.bleedLeft = (bl.bleedLeft || 0) - bd;
      if (bl.bleedLeft <= 0 && bl.hp > 0) { bl.bleeding = false; continue; }
      if (bl.hp <= 0) { bl.hp = 0; bl.bleeding = false; hitCause = 'bleed'; kill(bl, ents[bl.bleedBy] && ents[bl.bleedBy] !== bl ? bl.bleedBy : -1); hitCause = 'gun'; }
    }
    if (mode === 'tut') tutTick(dt);
    killcamTick(dt);
    if (MODE.respawn) {
      for (i = 0; i < ents.length; i++) {
        e = ents[i];
        if (!e.alive && e.respawnT > 0) {
          e.respawnT -= dt;
          if (e.respawnT <= 0) respawn(e);
        }
      }
    }
    if (mode === 'duel' && state === 'play') {
      if (roundBreak > 0) {
        roundBreak -= dt;
        if (roundBreak <= 0) newRound();
      } else {
        roundClock -= dt;
        if (roundClock <= 0) { feed('round expired \u2014 no score', false); roundBreak = 1.2; }
      }
    }

    for (var p = parts.length - 1; p >= 0; p--) {
      var pt = parts[p];
      pt.life -= dt;
      if (pt.life <= 0) { parts.splice(p, 1); continue; }
      pt.x += pt.vx * dt; pt.y += pt.vy * dt;
      pt.vx *= 0.92; pt.vy *= 0.92;
    }
    goreTick(dt);
    if (FX.blood) {
      for (var dcl = decals.length - 1; dcl >= 0; dcl--) {
        decals[dcl].t += dt;
        if (decals[dcl].t > FX.blood.frames / FX.blood.fps + FX.blood.hold) decals.splice(dcl, 1);
      }
    }
    for (var imp = impacts.length - 1; imp >= 0; imp--) {
      var iSh = FX[impacts[imp].fx];
      impacts[imp].t += dt;
      if (!iSh || impacts[imp].t > iSh.frames / iSh.fps) impacts.splice(imp, 1);
    }
    for (var dth2 = 0; dth2 < deaths.length; dth2++) deaths[dth2].t += dt;   // the pool stays
    for (var f = flashes.length - 1; f >= 0; f--) {
      flashes[f].t -= dt;
      if (flashes[f].t <= 0) flashes.splice(f, 1);
    }
    for (var m = dmgMarks.length - 1; m >= 0; m--) {
      dmgMarks[m].t -= dt;
      if (dmgMarks[m].t <= 0) dmgMarks.splice(m, 1);
    }
    shake *= Math.pow(0.0015, dt);

    var lerp = 1 - Math.pow(0.0001, dt);
    for (var li = 0; li < locals.length; li++) {
      var L = locals[li], lc = L.cam || cam;
      if (L.kc) {
        var kl = 1 - Math.pow(0.015, dt);
        lc.x += (L.kc.k.x - lc.x) * kl; lc.y += (L.kc.k.y - lc.y) * kl;
        continue;
      }
      // The camera is pinned to you; only the look-ahead toward the cursor
      // eases in. A camera that trailed behind let you walk out from under
      // a still cursor and spun you round to face backwards.
      var lx = 0, ly = 0;
      if (!touchMode && L.ctl && L.ctl.kb && (L.ctl.any || !usingPad(L))) {
        lx = clamp(mouse.wx - L.x, -110, 110) * 0.2;
        ly = clamp(mouse.wy - L.y, -110, 110) * 0.2;
      }
      L.leadX = (L.leadX || 0) + (lx - (L.leadX || 0)) * lerp;
      L.leadY = (L.leadY || 0) + (ly - (L.leadY || 0)) * lerp;
      lc.x = L.x + L.leadX;
      lc.y = L.y + L.leadY;
    }
    // The camera just moved under a still cursor: re-read where the cursor
    // is now, so a mouse player faces exactly what is under it this frame.
    updateMouseWorld();
    for (var la = 0; la < locals.length; la++) {
      var LA = locals[la];
      if (!LA.alive || LA.down || !LA.ctl || !LA.ctl.kb || mouse.sx === undefined || usingPad(LA)) continue;
      if (performance.now() - (LA.stickAimAt || -1e9) < 1500) continue;
      LA.ang = Math.atan2(mouse.wy - LA.y, mouse.wx - LA.x);
    }

    syncHud();
  }

  function syncHud() {
    var hp = Math.max(0, Math.round(player.hp));
    elHpN.textContent = hp;
    elHpFill.style.width = hp + '%';
    elHpFill.className = hp <= 35 ? 'low' : '';
    elMedsN.textContent = player.meds;
    elMedsBox.className = 'meds' + (player.meds ? '' : ' none');
    var mk = $('medsKey'), nk = $('nadesKey'), sk2 = $('smokesKey');
    if (mk) mk.textContent = promptKey('F', 'Y');
    if (nk) nk.textContent = promptKey('G', 'D-PAD \u25c0');
    if (sk2) sk2.textContent = promptKey('H', 'D-PAD \u25b6');
    var nb2 = $('nadesN'), nbx = $('nadesBox');
    if (nb2) nb2.textContent = player.nades;
    if (nbx) nbx.className = 'meds' + (player.nades ? '' : ' none');
    var sb2 = $('smokesN'), sbx = $('smokesBox');
    if (sb2) sb2.textContent = player.smokes;
    if (sbx) sbx.className = 'meds' + (player.smokes ? '' : ' none');

    elAliveL.textContent = MODE.label;
    if (mode === 'br') {
      elAlive.textContent = ('0' + alive).slice(-2);
      if (zone.closing) { elZone.textContent = 'ZONE CLOSING \u00b7 ' + fmtTime(zone.timer); elZone.className = 'zone-line hot'; }
      else { elZone.textContent = 'ZONE HOLDS \u00b7 ' + fmtTime(zone.timer); elZone.className = 'zone-line'; }
    } else if (mode === 'zomb') {
      var alive0 = 0, alive1 = 0;
      for (var zq = 0; zq < ents.length; zq++) {
        if (!ents[zq].alive) continue;
        if (ents[zq].team === 0) alive0++; else alive1++;
      }
      elAliveL.textContent = 'LIVING';
      elAlive.textContent = ('0' + alive0).slice(-2);
      elZone.className = 'zone-line' + (zombClock < 30 ? ' hot' : '');
      elZone.textContent = (player.team === 1 ? 'INFECTED \u00b7 ' : 'SURVIVE \u00b7 ')
        + fmtTime(zombClock) + ' \u00b7 ' + alive1 + ' ON THEIR FEET';
    } else if (mode === 'sect') {
      elAlive.textContent = score[player.team] + ' \u2013 ' + score[1 - player.team];
      elZone.className = 'zone-line';
      var bits = [];
      for (var sh = 0; sh < sectors.length; sh++) {
        var so = sectors[sh].owner;
        bits.push(sectors[sh].name + ' ' + (so < 0 ? '\u2013' : (so === player.team ? 'YOU' : 'THEM')));
      }
      elZone.textContent = bits.join(' \u00b7 ') + ' \u00b7 TO ' + MODE.target;
    } else if (mode === 'ctf') {
      elAlive.textContent = score[player.team] + ' \u2013 ' + score[1 - player.team];
      elZone.className = 'zone-line';
      if (flags.length === 2) {
        elZone.textContent = 'YOURS ' + flagState(flags[player.team]) +
                             ' \u00b7 THEIRS ' + flagState(flags[1 - player.team]) +
                             ' \u00b7 FIRST TO ' + MODE.target;
      } else elZone.textContent = 'FIRST TO ' + MODE.target;
    } else if (mode === 'team' || mode === 'war') {
      elAlive.textContent = score[player.team] + ' \u2013 ' + score[1 - player.team];
      elZone.className = 'zone-line';
      var mates = 0, opp = 0;
      for (var q = 0; q < ents.length; q++) {
        if (!ents[q].alive) continue;
        if (ents[q].team === player.team) mates++; else opp++;
      }
      elZone.textContent = player.alive
        ? 'FIRST TO ' + MODE.target + ' \u00b7 ' + mates + ' v ' + opp + ' UP'
        : 'RESPAWNING \u00b7 ' + Math.ceil(player.respawnT);
    } else if (mode === 'tut') {
      elAlive.textContent = Math.min(tut.i + 1, TUT.length) + '/' + TUT.length;
      elZone.className = 'zone-line';
      elZone.textContent = 'ESC TO LEAVE';
    } else if (mode === 'duel') {
      elAlive.textContent = score[player.team] + ' \u2013 ' + score[1 - player.team];
      elZone.className = 'zone-line';
      elZone.textContent = roundBreak > 0
        ? 'NEXT ROUND\u2026'
        : 'ROUND ' + round + ' \u00b7 FIRST TO ' + MODE.target + ' \u00b7 ' + fmtTime(roundClock);
    } else {
      elAlive.textContent = Math.min(player.level + 1, LADDER.length) + '/' + LADDER.length;
      var lead = ents[0];
      for (var i = 1; i < ents.length; i++) if (ents[i].level > lead.level) lead = ents[i];
      elZone.className = 'zone-line';
      elZone.textContent = player.alive
        ? 'LEADER ' + lead.name + ' \u00b7 ' + Math.min(lead.level + 1, LADDER.length) + '/' + LADDER.length
        : 'RESPAWNING \u00b7 ' + Math.ceil(player.respawnT);
    }

    var w = curW(player), slot = curSlot(player);
    elWName.textContent = w ? w.name : 'UNARMED';
    elAmmoN.textContent = w ? ('0' + slot.ammo).slice(-2) : '00';
    elResN.textContent = player.reserve >= 9000 ? '/ \u221e' : '/ ' + player.reserve;
    elWep.className = 'wep' + (w && slot.ammo === 0 ? ' dry' : '');
    for (var k = 0; k < 2; k++) {
      var s = player.slots[k];
      var nm = s ? WEAPONS[s.key].name : '\u2014';
      elSlot[k].textContent = usingPad(player) ? (k === 0 ? 'LB  ' + nm : nm + '  RB') : (k + 1) + '  ' + nm;
      elSlot[k].className = (s && player.slot === k) ? 'on' : '';
    }
    if (player.reloadT > 0 && w) {
      elRelBar.hidden = false;
      elRelFill.style.width = Math.round((1 - player.reloadT / w.reload) * 100) + '%';
    } else if (player.useT > 0) {
      elRelBar.hidden = false;
      elRelFill.style.width = Math.round((1 - player.useT / 1.6) * 100) + '%';
    } else elRelBar.hidden = true;
  }

  // ---------------------------------------------------------------- render
  function setCamTransform() {
    var sk = SET.shake ? shake : 0;
    var sx = sk ? rr(-sk, sk) : 0;
    var sy = sk ? rr(-sk, sk) : 0;
    ctx.setTransform(dpr * zoom, 0, 0, dpr * zoom,
      dpr * (VX + cw / 2 - cam.x * zoom + sx), dpr * (VY + ch / 2 - cam.y * zoom + sy));
  }

  // Drop-in sprites. Anything not supplied keeps the vector art, so a partial
  // set is fine:  EARSHOT.loadSprites({ player: 'player.png', enemy: 'enemy.png',
  //                                     loot_pistol: 'pistol.png', loot_med: 'stim.png' })
  // A sprite sheet: one row per weapon, one column per frame, characters
  // drawn facing right. Rows are named by weapon key so whatever a unit is
  // carrying picks its own row. rowY lets you give explicit row offsets when
  // the sheet has label strips between rows.
  var SHEET = null;
  function chromaKey(img, tol) {
    var c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    var g = c.getContext('2d');
    g.drawImage(img, 0, 0);
    try {
      var d = g.getImageData(0, 0, c.width, c.height), px = d.data;
      var kr = px[0], kg = px[1], kb = px[2];      // top-left pixel is the backdrop
      for (var i = 0; i < px.length; i += 4) {
        if (Math.abs(px[i] - kr) < tol && Math.abs(px[i + 1] - kg) < tol && Math.abs(px[i + 2] - kb) < tol) px[i + 3] = 0;
      }
      g.putImageData(d, 0, 0);
    } catch (err) { /* unreadable pixels \u2014 use the image as it came */ }
    return c;
  }
  function loadSheet(cfg) {
    var img = new Image();
    img.onload = function () {
      var src = cfg.chroma === false ? img : chromaKey(img, cfg.chromaTol || 40);
      var rows = cfg.rows || ['silenced', 'shotgun', 'rifle', 'pistol'];
      var cols = cfg.cols || 12;
      var fw = cfg.frameW || Math.floor(img.width / cols);
      var fh = cfg.frameH || Math.floor(img.height / rows.length);
      SHEET = {
        img: src, cols: cols, fw: fw, fh: fh, rows: rows,
        rowY: cfg.rowY || null,
        walk: cfg.walk || [0, 1, 2, 3, 4, 5, 6, 7],
        idle: cfg.idle || [8],
        fire: cfg.fire || [cols - 2, cols - 1],
        scale: cfg.scale || 3.6,
        fps: cfg.fps || 11
      };
    };
    img.onerror = function () { SHEET = null; };
    img.src = cfg.src;
  }
  function sheetFrame(e) {
    var sl = curSlot(e);
    var row = sl ? SHEET.rows.indexOf(sl.key) : 0;
    if (row < 0) row = 0;
    var col;
    if (e.animFire > 0 && SHEET.fire.length) {
      var k = 1 - Math.max(0, e.animFire) / 0.17;
      col = SHEET.fire[Math.min(SHEET.fire.length - 1, Math.floor(k * SHEET.fire.length))];
    } else if (e.moving) {
      col = SHEET.walk[Math.floor(e.animT * SHEET.fps) % SHEET.walk.length];
    } else col = SHEET.idle[0];
    return { row: row, col: col };
  }

  // ---- asset pack: modular characters, tiles, pickup icons ---------------
  // Characters are built from five loose pieces (torso, legs, head and two
  // arms) plus the weapon in hand. Each combination is composed once into an
  // offscreen canvas and reused, so the per-frame cost is a single drawImage.
  var PACK = null, PACK_IMG = {}, charCache = {}, floorPat = null;
  var PACK_READY = false;

  // Which weapon sprite each gun borrows, and how big it hangs off the hands.
  var WEAP_IDX = { pistol: 2, silenced: 3, shotgun: 4, rifle: 4 };
  var WEAP_MUL = { pistol: 1.0, silenced: 1.05, shotgun: 1.0, rifle: 1.18 };

  // Everything below is in half-scale sheet pixels, tuned against the artwork.
  var CHAR = {
    W: 200, H: 300,        // composing canvas, tall enough for a long barrel
    cx: 100, cy: 195,      // where the body's centre sits on it
    legsY: 26, torsoY: 4, headY: -2,
    armX: 42, armY: -18, armRot: Math.PI,   // arms are drawn hand-down; flip them
    gripY: -62, gunS: 0.70,                 // the grip lands here, at the hands
    draw: 5.6              // whole canvas height = entity radius * this
  };

  function loadPack(cfg) {
    PACK = cfg.data;
    var pending = 0, done = function () { if (--pending === 0) PACK_READY = true; };
    function grab(key, src) {
      pending++;
      var im = new Image();
      im.onload = function () { PACK_IMG[key] = im; done(); };
      im.onerror = done;
      im.src = src;
    }
    grab('skins', cfg.skins);
    grab('weapons', cfg.weapons);
    PACK_IMG.sniper = makeSniper();
    if (cfg.floor) {
      pending++;
      var fi = new Image();
      fi.onload = function () {
        PACK_IMG.floor = fi;
        floorPat = ctx.createPattern(fi, 'repeat');
        if (floorPat && floorPat.setTransform && window.DOMMatrix) {
          try { floorPat.setTransform(new DOMMatrix().scaleSelf(TILE / fi.width)); } catch (err) {}
        }
        done();
      };
      fi.onerror = done;
      fi.src = cfg.floor;
    }
    if (cfg.icons) for (var k in cfg.icons) grab('icon_' + k, cfg.icons[k]);
  }

  // The pack ships three guns, so the sniper gets a stand-in drawn in the same
  // language: flat fills, heavy black outline, muzzle down like the rest.
  function makeSniper() {
    var W = 30, H = 208;
    var c = document.createElement('canvas');
    c.width = W; c.height = H;
    var g = c.getContext('2d');
    g.lineJoin = 'round';
    g.strokeStyle = '#000';
    g.lineWidth = 4;
    function slab(x, y, w, h, fill, r) {
      g.beginPath();
      if (g.roundRect) g.roundRect(x, y, w, h, r || 3);
      else g.rect(x, y, w, h);
      g.fillStyle = fill;
      g.fill();
      g.stroke();
    }
    slab(6, 168, 18, 36, '#8a9099', 4);      // muzzle brake, at the bottom
    slab(11, 96, 8, 80, '#9aa1aa', 3);       // barrel
    slab(9, 92, 12, 26, '#4a4a4a', 3);       // magazine
    slab(5, 30, 20, 70, '#2a2a2a', 5);       // receiver
    slab(7, 4, 16, 34, '#6b5030', 6);        // stock
    slab(3, 44, 24, 16, '#1c1c1c', 5);       // scope body
    slab(9, 38, 12, 8, '#3c4f63', 3);        // scope lens
    return c;
  }

  function weaponArtIdx(i) {
    if (!PACK_IMG.weapons || !PACK.weapons || !PACK.weapons[i]) return null;
    return { img: PACK_IMG.weapons, b: PACK.weapons[i] };
  }

  // Where a weapon's artwork lives: the pack sheet, or our own stand-in.
  function weaponArt(key) {
    if (key === 'rifle' && PACK_IMG.sniper) {
      var sc = PACK_IMG.sniper;
      return { img: sc, b: [0, 0, sc.width, sc.height] };
    }
    if (!PACK_IMG.weapons || !PACK.weapons) return null;
    var wi = WEAP_IDX[key];
    var b = PACK.weapons[wi === undefined ? 2 : wi];
    return b ? { img: PACK_IMG.weapons, b: b } : null;
  }

  function buildChar(skin, weaponKey) {
    var c = document.createElement('canvas');
    c.width = CHAR.W; c.height = CHAR.H;
    var g = c.getContext('2d');
    var parts = PACK.skins[skin % PACK.skins.length];
    var sheet = PACK_IMG.skins;
    if (!sheet || !parts) return c;

    function piece(idx, dx, dy, rot) {
      var b = parts[idx];
      if (!b) return;
      var w = b[2] - b[0], h = b[3] - b[1];
      g.save();
      g.translate(CHAR.cx + dx, CHAR.cy + dy);
      if (rot) g.rotate(rot);
      g.drawImage(sheet, b[0], b[1], w, h, -w / 2, -h / 2, w, h);
      g.restore();
    }

    piece(1, 0, CHAR.legsY, 0);                       // legs, furthest back
    piece(4, -CHAR.armX, CHAR.armY, CHAR.armRot);     // far arm
    piece(0, 0, CHAR.torsoY, 0);                      // torso

    var art = weaponKey ? weaponArt(weaponKey) : null;
    if (art) {
      var wb = art.b;
      var ww = wb[2] - wb[0], wh = wb[3] - wb[1];
      var m = (WEAP_MUL[weaponKey] || 1) * CHAR.gunS;
      // Grip stays at the hands; the sprite is turned 180 so the barrel
      // leads, because the pack draws every weapon pointing down.
      g.save();
      g.translate(CHAR.cx, CHAR.cy + CHAR.gripY - wh * m / 2);
      g.rotate(Math.PI);
      g.drawImage(art.img, wb[0], wb[1], ww, wh, -ww * m / 2, -wh * m / 2, ww * m, wh * m);
      g.restore();
    }

    piece(3, CHAR.armX, CHAR.armY, CHAR.armRot);      // near arm, over the gun
    piece(2, 0, CHAR.headY, 0);                       // head on top
    return c;
  }

  function muzzleOff(e) {
    var w = curW(e), sl = curSlot(e);
    var base = e.r + 6;
    if (!PACK_READY || !w || !sl || !PACK.weapons) return base;
    var art = weaponArt(sl.key);
    if (!art) return base;
    var h = (art.b[3] - art.b[1]) * (WEAP_MUL[sl.key] || 1) * CHAR.gunS;
    var px = -CHAR.gripY + h;                        // canvas pixels forward
    return px / CHAR.H * (e.r * CHAR.draw);
  }

  function charFor(e) {
    var sl = curSlot(e);
    var key = e.skin + '|' + (sl ? sl.key : 'none');
    var cv = charCache[key];
    if (!cv) { cv = buildChar(e.skin, sl ? sl.key : null); charCache[key] = cv; }
    return cv;
  }

  // Draw a fighter limb by limb, posed for this instant.
  function drawPacked(e) {
    var parts = PACK.skins[e.skin % PACK.skins.length];
    var sheet = PACK_IMG.skins;
    if (!parts || !sheet) return false;

    var stride = e.moving ? Math.sin(e.animT * 8.5) : Math.sin(matchTime * 1.7 + e.id) * 0.18;
    var kick = e.animFire > 0 ? (e.animFire / 0.17) * 7 : 0;   // recoil, pushed back
    // Throw: the arm drops back, then whips forward past neutral. Pure
    // translation - rotating it swung the hand across the body and read as
    // the arm going backwards. Forward is -Y in this space.
    // a jab: quick out and back, translation only
    var jab = e.swingT > 0 ? Math.sin((1 - e.swingT / 0.18) * Math.PI) * 32 : 0;
    var reach = 0;
    if (e.throwT > 0) {
      var tp = 1 - e.throwT / 0.34;
      if (tp < 0.35) reach = -13 * (tp / 0.35);
      else {
        var tb = (tp - 0.35) / 0.65;
        reach = -13 * (1 - tb) + 42 * Math.sin(tb * Math.PI * 0.85);
      }
    }
    var k = (e.r * CHAR.draw) / CHAR.H;

    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.rotate(e.ang + Math.PI / 2);          // the kit is drawn facing up
    ctx.scale(k, k);
    ctx.translate(-CHAR.W / 2, -CHAR.H / 2);  // into composing-canvas space

    function limb(idx, dx, dy, rot) {
      var b = parts[idx];
      if (!b) return;
      var w = b[2] - b[0], h = b[3] - b[1];
      ctx.save();
      ctx.translate(CHAR.cx + dx, CHAR.cy + dy);
      if (rot) ctx.rotate(rot);
      ctx.drawImage(sheet, b[0], b[1], w, h, -w / 2, -h / 2, w, h);
      ctx.restore();
    }

    limb(1, stride * 4, CHAR.legsY, stride * 0.11);                                  // legs rock
    limb(4, -CHAR.armX + stride * 2 - reach * 0.12, CHAR.armY - stride * 4 + kick + reach * 0.18 + jab * 0.25, CHAR.armRot + stride * 0.09);
    limb(0, stride * 2 + reach * 0.10, CHAR.torsoY - jab * 0.12, stride * 0.03);     // torso leans into it

    var sl = curSlot(e);
    var art = sl ? weaponArt(sl.key) : null;
    if (art) {
      var wb = art.b, ww = wb[2] - wb[0], wh = wb[3] - wb[1];
      var m = (WEAP_MUL[sl.key] || 1) * CHAR.gunS;
      ctx.save();
      ctx.translate(CHAR.cx, CHAR.cy + CHAR.gripY + kick - wh * m / 2);
      ctx.rotate(Math.PI);
      ctx.drawImage(art.img, wb[0], wb[1], ww, wh, -ww * m / 2, -wh * m / 2, ww * m, wh * m);
      ctx.restore();
    }

    limb(3, CHAR.armX + stride * 2 + reach * 0.16 - jab * 0.30, CHAR.armY + stride * 4 + kick - reach - jab, CHAR.armRot - stride * 0.09);
    limb(2, stride * 1.5, CHAR.headY, 0);                                            // head last
    ctx.restore();
    return true;
  }

  var SPRITES = {};
  function loadSprites(map) {
    Object.keys(map).forEach(function (k) {
      var img = new Image();
      img.onload = function () { SPRITES[k] = img; };
      img.src = map[k];
    });
  }
  window.EARSHOT = {
    loadSprites: loadSprites, loadSheet: loadSheet, loadFx: loadFx,
    loadPack: loadPack, sprites: SPRITES,
    // testing only: make the player unkillable so a sim runs bot-vs-bot
    god: function (on) { godMode = !!on; return godMode; },
    aimErr: function (on) { aimErrOn = !!on; return aimErrOn; },
    guestStep: function (seconds) {
      var n = Math.round((seconds || 1) * 60);
      for (var i = 0; i < n && netGuest && state === 'play'; i++) guestTick(1 / 60);
      return window.EARSHOT.net();
    },
    queueTest: function () { goPublicHost(); },
    botInfo: function (id) {
      var e = ents[id]; if (!e) return null;
      return { x: Math.round(e.x), y: Math.round(e.y), alive: e.alive, down: e.down, air: e.air, hp: Math.round(e.hp),
               path: e.path ? e.path.length : null, pathI: e.pathI, repathT: +(e.repathT || 0).toFixed(2), stuckT: +(e.stuckT || 0).toFixed(2),
               target: e.target ? e.target.id : null, tile: [Math.floor(e.x / TILE), Math.floor(e.y / TILE)], wallHere: wallAt(e.x, e.y) };
    },
    zoneInfo: function () { return zone ? { cx: Math.round(zone.cx), cy: Math.round(zone.cy), r: Math.round(zone.r), closing: zone.closing, phase: zone.phase } : null; },
    // test: have entity `from` land a hit of `amount` on you
    hurt: function (from, amount, victim) {
      var k = ents[from], v = victim === undefined ? player : ents[victim];
      if (!k || !v) return false;
      damage(v, amount, from, Math.atan2(v.y - k.y, v.x - k.x));
      return { alive: v.alive, killcam: !!v.kc };
    },
    // poster art: draw one of the game's characters onto any canvas
    posterChar: function (c2, o) {
      if (!PACK_READY) return false;
      var keep = ctx;
      ctx = c2;
      try {
        drawPacked({ x: o.x, y: o.y, ang: o.ang, skin: o.skin, r: o.r || 8.5, id: o.id || 1,
                     slots: [o.gun ? { key: o.gun, ammo: 1 } : null, null], slot: 0,
                     moving: !!o.moving, animT: o.animT || 0, animFire: o.fire || 0,
                     swingT: 0, throwT: 0, team: 0, alive: true });
      } finally { ctx = keep; }
      return true;
    },
    posterFloor: function () { return PACK_IMG.floor || null; },
    // screenshot tool (marketing images): freeze, look through someone's eyes
    // with a wider light, and hide the markers
    photo: function (id, reach) {
      var e = ents[id];
      if (!e) return false;
      state = 'paused';
      player = e; cam.x = e.x; cam.y = e.y;
      VIEW_R = reach || VIEW_R;
      noOverlay = true;
      return true;
    },
    uiStep: function (dt) { uiPad(dt || 0.05); if (netRole === 'host') netHostTick(dt || 0.05); return document.activeElement ? (document.activeElement.id || document.activeElement.textContent.trim().slice(0, 24)) : null; },
    tutInfo: function () {
      return { step: tut.i, item: tut.item && loot.indexOf(tut.item) >= 0 ? [Math.round(tut.item.x), Math.round(tut.item.y)] : null };
    },
    padInfo: function () { return { active: padActive(), padLast: padLast, kbmLast: kbmLast, rest: padRest, now: performance.now() }; },
    aimInfo: function () {
      return { sx: mouse.sx, sy: mouse.sy, wx: mouse.wx, wy: mouse.wy, camX: cam.x, camY: cam.y,
               pcam: player && player.cam === cam, px: player && player.x, py: player && player.y, ang: player && player.ang,
               leadX: player && player.leadX, zoom: zoom, pzoom: player && player.zoom, cw: cw, ch: ch, vw: player && player.viewW, velY: player && player.vy,
               padOn: padActive(), touch: touchMode, down: mouse.down };
    },
    net: function () {
      return { role: netRole, guest: netGuest, open: !!(netConn && netConn.open), guests: netGuests.map(function (g) { return g.name + (g.ent ? '@' + g.ent.id : ''); }), sent: netStat.sent, recv: netStat.recv,
               err: netStat.err, queue: netQueue.length, hasPlayer: !!player, ents: ents.length, state: state,
               kbSent: Math.round(netStat.bytes / 1024), kbRecv: Math.round(netStat.rbytes / 1024) };
    },
    locals: function () {
      return locals.map(function (L) {
        return { name: L.name, x: Math.round(L.x), y: Math.round(L.y), ang: +L.ang.toFixed(2), team: L.team,
                 alive: L.alive, hp: Math.round(L.hp), ctl: L.ctl, w: curW(L) ? curW(L).name : null };
      });
    },
    // advance the simulation without drawing, for testing behaviour
    step: function (seconds, dt) {
      dt = dt || 1 / 60;
      var n = Math.min(40000, Math.round((seconds || 1) / dt));
      for (var i = 0; i < n; i++) {
        if (state !== 'play') break;
        update(dt);
        if (netRole === 'host') netHostTick(dt);
      }
      return window.EARSHOT.debug();
    },
    // every bot's gun, magazine and spare rounds, for diagnosing supply
    bots: function () {
      return ents.filter(function (e) { return e.bot; }).map(function (e) {
        var sl = curSlot(e);
        var t = e.target, td = t ? dist(e, t) : 0;
        return { id: e.id, n: e.name, x: Math.round(e.x), y: Math.round(e.y), alive: e.alive, team: e.team, gun: sl ? sl.key : null,
                 mag: sl ? sl.ammo : 0, reserve: e.reserve, reloading: e.reloadT > 0,
                 hasTarget: !!t, react: +e.reactT.toFixed(2), lost: +e.lostT.toFixed(2),
                 dist: Math.round(td), inSight: t ? sightClear(e.x, e.y, t.x, t.y) : false,
                 fireT: +e.fireT.toFixed(2), healing: e.useT > 0, down: e.down };
      });
    },
    // a read-only peek at the simulation, for diagnosing behaviour
    debug: function () {
      var live = 0, withTarget = 0, armed = 0, minEnemy = 1e9, i, j;
      for (i = 0; i < ents.length; i++) {
        var e = ents[i];
        if (!e.alive) continue;
        live++;
        if (e.target) withTarget++;
        if (curW(e)) armed++;
        for (j = 0; j < ents.length; j++) {
          var o = ents[j];
          if (o === e || !o.alive || !foes(e, o)) continue;
          var d = dist(e, o);
          if (d < minEnemy) minEnemy = d;
        }
      }
      return {
        mode: mode, live: live, armed: armed, withTarget: withTarget, botFrags: botFrags,
        botShots: botShots, botHits: botHits, botHitsOnYou: botHitsOnYou, targetSwaps: targetSwaps, killCauses: killCauses,
        minEnemyDist: Math.round(minEnemy), bullets: bullets.length,
        sounds: sounds.length, shotsByPlayer: shots,
        loot: loot.length, lootFirst: loot[0] || null, decals: decals.length, corpses: corpses.length,
        sight: DIFF[difficulty].sight, mapW: MAP_W
      };
    }
  };

  function drawLootIcon(it, lit) {
    ctx.globalAlpha = lit ? 1 : 0.26;
    if (PACK_READY) {
      if (it.type === 'gun') {
        var ga = weaponArt(it.key);
        if (ga) {
          var gb = ga.b;
          var gw = gb[2] - gb[0], gh = gb[3] - gb[1];
          var dh = 20, dw = dh * (gw / gh);
          ctx.save();
          ctx.translate(it.x, it.y);
          ctx.rotate(it.spin || 0);
          ctx.drawImage(ga.img, gb[0], gb[1], gw, gh, -dw / 2, -dh / 2, dw, dh);
          ctx.restore();
          ctx.globalAlpha = 1;
          return;
        }
      }
      if (it.type === 'nade' || it.type === 'smoke') {
        var na = weaponArtIdx(it.type === 'smoke' ? 0 : 1);
        if (na) {
          var nb = na.b, nw = nb[2] - nb[0], nh = nb[3] - nb[1];
          var nhh = 15, nww = nhh * (nw / nh);
          ctx.drawImage(na.img, nb[0], nb[1], nw, nh, it.x - nww / 2, it.y - nhh / 2, nww, nhh);
          ctx.globalAlpha = 1;
          return;
        }
      }
      var ico = PACK_IMG[it.type === 'ammo' ? 'icon_ammo' : 'icon_med'];
      if (ico) {
        ctx.drawImage(ico, it.x - 7, it.y - 7, 14, 14);
        ctx.globalAlpha = 1;
        return;
      }
    }
    var lspr = SPRITES['loot_' + (it.type === 'gun' ? it.key : it.type)];
    if (lspr) {
      var lh = 16, lw = lh * (lspr.width / lspr.height);
      ctx.drawImage(lspr, it.x - lw / 2, it.y - lh / 2, lw, lh);
      ctx.globalAlpha = 1;
      return;
    }
    if (it.type === 'gun') {
      ctx.fillStyle = WEAPONS[it.key].tint;
      ctx.fillRect(it.x - 7, it.y - 2.4, 14, 4.8);
      ctx.fillRect(it.x - 2, it.y - 5, 4, 10);
    } else if (it.type === 'ammo') {
      ctx.fillStyle = '#c7a35a';
      ctx.fillRect(it.x - 4, it.y - 4, 8, 8);
    } else {
      ctx.fillStyle = '#ff4d8d';
      ctx.fillRect(it.x - 5, it.y - 1.8, 10, 3.6);
      ctx.fillRect(it.x - 1.8, it.y - 5, 3.6, 10);
    }
    ctx.globalAlpha = 1;
  }

  function render() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#04060a';
    ctx.fillRect(0, 0, cw, ch);
    if (state === 'menu' || state === 'over') { renderAmbient(); return; }
    if (!player) return;

    if (!splitOn) {
      VX = 0; VY = 0; VW = cw; VH = ch;
      player.viewX = 0; player.viewY = 0; player.viewW = cw; player.viewH = ch; player.zoom = zoom;
      if (player.kc) {
        // see the world as the one who got you saw it
        var me = player, kc0 = player.kc;
        player = kc0.k; noOverlay = true;
        try { renderScene(); } finally { player = me; noOverlay = false; }
        renderKillcam(kc0);
        return;
      }
      renderScene();
      return;
    }

    // Each local player gets a slice: side by side on a wide screen, stacked
    // on a tall one. Everything below draws as if its slice were the screen.
    var fullW = cw, fullH = ch, z0 = zoom, p0 = player, cam0 = cam, pr0 = promptItem;
    var side = fullW >= fullH;
    for (var pi = 0; pi < locals.length; pi++) {
      var L = locals[pi];
      if (side) { VX = Math.round(pi * fullW / 2); VY = 0; VW = Math.round(fullW / 2); VH = fullH; }
      else { VX = 0; VY = Math.round(pi * fullH / 2); VW = fullW; VH = Math.round(fullH / 2); }
      // (viewX..: vx/vy on an entity are its velocity - never reuse those)
      L.viewX = VX; L.viewY = VY; L.viewW = VW; L.viewH = VH;
      L.zoom = Math.max(0.5, Math.min(2.4, Math.min(VW, VH) / (VIEW_BASE * 2 + 60)));
      cw = VW; ch = VH; zoom = L.zoom; player = L; cam = L.cam; promptItem = L.prompt;
      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.beginPath(); ctx.rect(VX, VY, VW, VH); ctx.clip();
      if (L.kc) {
        // this player's own kill cam, in their half
        var kcS = L.kc;
        player = kcS.k; noOverlay = true;
        try { renderScene(); } finally { player = L; noOverlay = false; }
        renderKillcam(kcS);
      } else renderScene();
      drawSplitHud(L);
      ctx.restore();
    }
    cw = fullW; ch = fullH; zoom = z0; player = p0; cam = cam0; promptItem = pr0;
    VX = 0; VY = 0; VW = cw; VH = ch;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#0d0f12';
    if (side) ctx.fillRect(Math.round(cw / 2) - 2, 0, 4, ch);
    else ctx.fillRect(0, Math.round(ch / 2) - 2, cw, 4);
    ctx.fillStyle = 'rgba(242,189,29,.55)';
    if (side) ctx.fillRect(Math.round(cw / 2) - 0.5, 0, 1, ch);
    else ctx.fillRect(0, Math.round(ch / 2) - 0.5, cw, 1);
  }

  // Your own numbers, drawn into your own slice of a split screen.
  function drawSplitHud(L) {
    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
    ctx.save();
    ctx.textBaseline = 'alphabetic';
    var pad2 = 14, by = VH - pad2;
    // who is who, top right
    ctx.font = '400 15px "Russo One", "Chakra Petch", sans-serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#0d0f12';
    ctx.fillText(L.name, VW / 2 + 2, by - 12 + 2);
    ctx.fillStyle = L === locals[0] ? '#f2bd1d' : '#7ce7d8';
    ctx.fillText(L.name, VW / 2, by - 12);
    ctx.font = '500 9px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(198,212,227,.6)';
    ctx.fillText(usingPad(L) ? 'CONTROLLER' : 'KEYBOARD', VW / 2, by + 2);

    if (!L.alive) {
      ctx.textAlign = 'center';
      ctx.font = '400 22px "Russo One", "Chakra Petch", sans-serif';
      ctx.fillStyle = '#f1e7d0';
      var msg = L.respawnT > 0 ? 'RESPAWNING ' + Math.ceil(L.respawnT) : 'OUT';
      if (!L.kc) ctx.fillText(msg, VW / 2, VH / 2);          // the kill cam says it instead
      ctx.restore();
      return;
    }

    // health, bottom left
    var hp = Math.max(0, Math.round(L.hp)), bw = Math.min(170, VW * 0.34);
    ctx.fillStyle = 'rgba(44,61,82,.7)';
    ctx.fillRect(pad2, by - 34, bw, 5);
    ctx.fillStyle = hp <= 35 ? '#ff4d8d' : '#7ce7d8';
    ctx.fillRect(pad2, by - 34, bw * hp / 100, 5);
    ctx.textAlign = 'left';
    ctx.font = '700 20px "Chakra Petch", sans-serif';
    ctx.fillStyle = '#c6d4e3';
    ctx.fillText(String(hp), pad2, by - 10);
    ctx.font = '500 9px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(198,212,227,.6)';
    // kit, with this player's own buttons for each
    var onPad = usingPad(L);
    var kit = (onPad ? 'Y' : 'F') + ' STIM ' + L.meds + '   ' +
              (onPad ? '\u25c0' : 'G') + ' FRAG ' + L.nades + '   ' +
              (onPad ? '\u25b6' : 'H') + ' SMOKE ' + L.smokes;
    ctx.fillText(kit, pad2, by + 2);

    // weapon, bottom right
    var w = curW(L), sl = curSlot(L);
    // both guns: two chips, the one in hand lit, labelled with how to swap
    ctx.font = '600 9px "IBM Plex Mono", monospace';
    ctx.textAlign = 'center';
    var chipX = VW - pad2;
    for (var ci = 1; ci >= 0; ci--) {
      var cs = L.slots[ci], cname = cs ? WEAPONS[cs.key].name : '\u2014';
      var clabel = onPad ? (ci === 0 ? 'LB ' + cname : cname + ' RB') : (ci + 1) + ' ' + cname;
      var cwid = ctx.measureText(clabel).width + 14, on = cs && L.slot === ci;
      chipX -= cwid;
      ctx.fillStyle = 'rgba(10,15,22,.7)';
      ctx.fillRect(chipX, by - 48, cwid, 16);
      ctx.strokeStyle = on ? '#7ce7d8' : 'rgba(44,61,82,.9)'; ctx.lineWidth = 1;
      ctx.strokeRect(chipX + 0.5, by - 47.5, cwid - 1, 15);
      ctx.fillStyle = on ? '#7ce7d8' : 'rgba(198,212,227,.6)';
      ctx.fillText(clabel, chipX + cwid / 2, by - 39.5);
      chipX -= 4;
    }
    ctx.textAlign = 'right';
    ctx.font = '500 9px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(198,212,227,.6)';
    ctx.fillText(w ? w.name : 'UNARMED', VW - pad2, by - 26);
    ctx.font = '700 24px "Chakra Petch", sans-serif';
    ctx.fillStyle = w && sl.ammo <= 0 ? '#ff4d8d' : '#c6d4e3';
    var res = L.reserve >= 9000 ? '\u221e' : String(L.reserve);
    var ammoTxt = w ? String(sl.ammo) : '--';
    ctx.fillText(ammoTxt, VW - pad2 - 40, by - 6);
    ctx.font = '500 11px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(198,212,227,.6)';
    ctx.fillText('/ ' + res, VW - pad2, by - 6);
    if (w && (L.reloadT > 0 || L.useT > 0)) {
      var k = L.reloadT > 0 ? 1 - L.reloadT / w.reload : 1 - L.useT / 1.6;
      ctx.fillStyle = 'rgba(44,61,82,.7)';
      ctx.fillRect(VW - pad2 - 78, by + 1, 78, 3);
      ctx.fillStyle = '#ffc95e';
      ctx.fillRect(VW - pad2 - 78, by + 1, 78 * clamp(k, 0, 1), 3);
    }
    ctx.restore();
  }

  function renderScene() {
    var halfW = cw / (2 * zoom), halfH = ch / (2 * zoom);
    var vx0 = cam.x - halfW, vx1 = cam.x + halfW, vy0 = cam.y - halfH, vy1 = cam.y + halfH;
    var t0 = Math.max(0, Math.floor(vx0 / TILE) - 1), t1 = Math.min(MAP_W - 1, Math.ceil(vx1 / TILE) + 1);
    var r0 = Math.max(0, Math.floor(vy0 / TILE) - 1), r1 = Math.min(MAP_H - 1, Math.ceil(vy1 / TILE) + 1);
    var i, ty, tx;

    computeVisibility(player.x, player.y, VIEW_R);
    exploreTick++;
    if (exploreTick % 3 === 0) markExplored(player.x, player.y);

    setCamTransform();

    // The world map keeps its dirt; everywhere else takes the pack's tiles.
    var grassy = (mapKind === 'world' && mode !== 'duel');
    var packed = PACK_READY && PACK && !grassy;
    if (packed) {
      tilePass(r0, r1, t0, t1, true, false, 0, '#0b1016');
      tilePass(r0, r1, t0, t1, true, true, 0, '#141d27');
    } else if (grassy) {
      tilePass(r0, r1, t0, t1, true, false, 0, groundDim);
      tilePass(r0, r1, t0, t1, true, true, 1, '#221e18');
      tilePass(r0, r1, t0, t1, true, true, 2, '#121806');
    } else {
      tilePass(r0, r1, t0, t1, true, false, 0, '#080d13');
      tilePass(r0, r1, t0, t1, true, true, 0, '#0d141d');
    }

    for (i = 0; i < loot.length; i++) if (loot[i].seen) drawLootIcon(loot[i], false);

    // --- lit region. Push each hit past the surface it struck so the wall
    //     tile itself renders instead of the clip ending on its bare face.
    ctx.save();
    var poly = new Path2D();
    for (i = 0; i < visPts.length; i += 2) {
      var ox = visPts[i] - player.x, oy = visPts[i + 1] - player.y;
      var od = Math.sqrt(ox * ox + oy * oy) || 1;
      var push = od < VIEW_R - 2 ? TILE * 0.95 : 0;
      if (i === 0) poly.moveTo(visPts[i] + ox / od * push, visPts[i + 1] + oy / od * push);
      else poly.lineTo(visPts[i] + ox / od * push, visPts[i + 1] + oy / od * push);
    }
    poly.closePath();
    ctx.clip(poly);
    var cone = new Path2D(), cR = VIEW_R + TILE * 3;
    cone.moveTo(player.x, player.y);
    cone.arc(player.x, player.y, cR, player.ang - FOV_HALF, player.ang + FOV_HALF);
    cone.closePath();
    cone.moveTo(player.x + NEAR_SEE, player.y);
    cone.arc(player.x, player.y, NEAR_SEE, 0, 6.2832);
    ctx.clip(cone);

    if (packed) {
      tilePass(r0, r1, t0, t1, false, false, 0, floorPat || '#24313f');
      tilePass(r0, r1, t0, t1, false, true, 0, PACK.navy);
    } else if (grassy) {
      tilePass(r0, r1, t0, t1, false, false, 0, groundLit);
      tilePass(r0, r1, t0, t1, false, true, 1, '#6a6053');
      tilePass(r0, r1, t0, t1, false, true, 2, '#4a5c28');
    } else {
      tilePass(r0, r1, t0, t1, false, false, 0, '#121c27');
      tilePass(r0, r1, t0, t1, false, true, 0, '#31465f');
    }

    ctx.beginPath();
    for (i = 0; i < nearSegs.length; i++) {
      ctx.moveTo(nearSegs[i].ax, nearSegs[i].ay);
      ctx.lineTo(nearSegs[i].bx, nearSegs[i].by);
    }
    ctx.strokeStyle = packed ? PACK.gold : (grassy ? 'rgba(206,190,162,.6)' : 'rgba(158,196,228,.85)');
    ctx.lineWidth = (packed ? 2.4 : 1.6) / zoom;
    ctx.stroke();

    drawSplats();
    if (FX.death) {
      var dSh = FX.death, dSplit = dSh.split || dSh.frames;
      var spurtEnd = dSplit / dSh.fps;
      var smD = ctx.imageSmoothingEnabled;
      ctx.imageSmoothingEnabled = false;
      for (i = 0; i < deaths.length; i++) {
        var dth = deaths[i], dfi;
        if (dth.t < spurtEnd) dfi = Math.min(dSplit - 1, Math.floor(dth.t * dSh.fps));
        else dfi = Math.min(dSh.frames - 1, dSplit + Math.floor((dth.t - spurtEnd) * (dSh.poolFps || 9)));
        ctx.save();
        ctx.translate(dth.x, dth.y);
        ctx.rotate(dth.ang);
        ctx.scale(0.5 * dth.scale, 0.5 * dth.scale);
        ctx.translate(-dSh.fw / 2, -dSh.fh / 2);
        fxDraw(dSh, dfi, 1);
        ctx.restore();
      }
      ctx.imageSmoothingEnabled = smD;
    }

    if (FX.blood) {
      var bEnd = FX.blood.frames / FX.blood.fps;
      var sm0 = ctx.imageSmoothingEnabled;
      ctx.imageSmoothingEnabled = false;
      for (i = 0; i < decals.length; i++) {
        var dc = decals[i], bfi, bal;
        if (dc.t < bEnd) { bfi = Math.min(FX.blood.frames - 1, Math.floor(dc.t * FX.blood.fps)); bal = 1; }
        else { bfi = FX.blood.frames - 1; bal = Math.max(0, 1 - (dc.t - bEnd) / FX.blood.hold); }
        if (bal <= 0.02) continue;
        ctx.save();
        ctx.translate(dc.x, dc.y);
        ctx.rotate(dc.ang);
        var bs = 0.42 * dc.scale;
        ctx.scale(bs, bs);
        ctx.translate(-FX.blood.fw * 0.36, -FX.blood.fh * 0.5);
        fxDraw(FX.blood, bfi, bal);
        ctx.restore();
      }
      ctx.imageSmoothingEnabled = sm0;
    }

    for (i = 0; i < sectors.length; i++) {
      var sc2 = sectors[i];
      var tint2 = sc2.owner < 0 ? '198,212,227' : TEAM_TINT[sc2.owner === player.team ? 0 : 1];
      ctx.fillStyle = 'rgba(' + tint2 + ',.055)';
      ctx.beginPath(); ctx.arc(sc2.x, sc2.y, sc2.r, 0, 6.2832); ctx.fill();
      ctx.strokeStyle = 'rgba(' + tint2 + ',.5)';
      ctx.lineWidth = 2.2 / zoom;
      ctx.beginPath(); ctx.arc(sc2.x, sc2.y, sc2.r, 0, 6.2832); ctx.stroke();
      if (sc2.prog > 0 && sc2.cap >= 0) {
        ctx.strokeStyle = 'rgba(' + TEAM_TINT[sc2.cap === player.team ? 0 : 1] + ',.95)';
        ctx.lineWidth = 4 / zoom;
        ctx.beginPath();
        ctx.arc(sc2.x, sc2.y, sc2.r, -Math.PI / 2, -Math.PI / 2 + 6.2832 * sc2.prog);
        ctx.stroke();
      }
      ctx.fillStyle = 'rgba(' + tint2 + ',.75)';
      ctx.font = 'bold ' + (34 / zoom).toFixed(1) + 'px "Chakra Petch", sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(sc2.name, sc2.x, sc2.y);
      ctx.textAlign = 'left';
    }

    for (i = 0; i < flags.length; i++) {
      var fl2 = flags[i];
      var ft = TEAM_TINT[fl2.team === player.team ? 0 : 1];
      ctx.strokeStyle = 'rgba(' + ft + ',.30)';       // the stand is a known landmark
      ctx.lineWidth = 2 / zoom;
      ctx.beginPath(); ctx.arc(fl2.hx, fl2.hy, 30, 0, 6.2832); ctx.stroke();
      if (fl2.carrier) continue;                      // drawn on the carrier instead
      ctx.strokeStyle = 'rgba(' + ft + ',.95)';
      ctx.lineWidth = 2.2 / zoom;
      ctx.beginPath(); ctx.moveTo(fl2.x, fl2.y + 9); ctx.lineTo(fl2.x, fl2.y - 13); ctx.stroke();
      ctx.fillStyle = 'rgba(' + ft + ',.9)';
      ctx.beginPath();
      ctx.moveTo(fl2.x, fl2.y - 13); ctx.lineTo(fl2.x + 14, fl2.y - 8); ctx.lineTo(fl2.x, fl2.y - 3);
      ctx.closePath(); ctx.fill();
    }

    for (i = 0; i < nades.length; i++) {
      var gn = nades[i];
      var ga2 = PACK_READY ? weaponArtIdx(gn.kind === 'smoke' ? 0 : 1) : null;
      ctx.save();
      ctx.translate(gn.x, gn.y);
      ctx.rotate(gn.spin);
      if (ga2) {
        var gb2 = ga2.b, gw2 = gb2[2] - gb2[0], gh2 = gb2[3] - gb2[1];
        var dh2 = 13, dw2 = dh2 * (gw2 / gh2);
        ctx.drawImage(ga2.img, gb2[0], gb2[1], gw2, gh2, -dw2 / 2, -dh2 / 2, dw2, dh2);
      } else {
        ctx.fillStyle = '#5c6b32';
        ctx.beginPath(); ctx.arc(0, 0, 5, 0, 6.2832); ctx.fill();
      }
      ctx.restore();
      if (gn.fuse < 0.55 && Math.floor(gn.fuse * 12) % 2 === 0) {
        ctx.fillStyle = 'rgba(255,90,60,.9)';
        ctx.beginPath(); ctx.arc(gn.x, gn.y, 3, 0, 6.2832); ctx.fill();
      }
    }

    for (i = 0; i < corpses.length; i++) {
      ctx.fillStyle = 'rgba(255,77,141,.30)';
      ctx.beginPath(); ctx.arc(corpses[i].x, corpses[i].y, 7, 0, 6.2832); ctx.fill();
    }
    for (i = 0; i < loot.length; i++) {
      var it = loot[i];
      if (!visibleToPlayer(it.x, it.y)) continue;
      it.seen = true;
      drawLootIcon(it, true);
      if (it === promptItem) {
        ctx.strokeStyle = 'rgba(124,231,216,.75)';
        ctx.lineWidth = 1.4 / zoom;
        ctx.beginPath(); ctx.arc(it.x, it.y, 14, 0, 6.2832); ctx.stroke();
      }
    }
    for (i = 0; i < ents.length; i++) {
      var en = ents[i];
      if (!en.alive || en.hidden || en === player || en.air === 'plane') continue;
      if (!visibleToPlayer(en.x, en.y)) continue;
      drawUnit(en, en.team === player.team ? '#8ff0e4' : '#ff7a4d');
    }

    var g = ctx.createRadialGradient(player.x, player.y, VIEW_R * 0.18, player.x, player.y, VIEW_R);
    g.addColorStop(0, 'rgba(4,6,10,0)');
    g.addColorStop(0.62, 'rgba(4,6,10,.28)');
    g.addColorStop(1, 'rgba(4,6,10,.93)');
    ctx.fillStyle = g;
    ctx.fillRect(player.x - VIEW_R, player.y - VIEW_R, VIEW_R * 2, VIEW_R * 2);

    if (impacts.length) {
      var smI = ctx.imageSmoothingEnabled;
      ctx.imageSmoothingEnabled = false;
      for (i = 0; i < impacts.length; i++) {
        var ip = impacts[i], ipSh = FX[ip.fx];
        if (!ipSh) continue;
        var ifi = Math.min(ipSh.frames - 1, Math.floor(ip.t * ipSh.fps));
        ctx.save();
        ctx.translate(ip.x, ip.y);
        ctx.rotate(ip.ang);
        ctx.scale(0.5 * ip.scale, 0.5 * ip.scale);
        ctx.translate(-ipSh.fw / 2, -ipSh.fh / 2);
        fxDraw(ipSh, ifi, 1);
        ctx.restore();
      }
      ctx.imageSmoothingEnabled = smI;
    }
    for (i = 0; i < parts.length; i++) {
      var pp = parts[i];
      ctx.fillStyle = 'rgba(' + pp.color + ',' + (pp.life / pp.max).toFixed(3) + ')';
      ctx.fillRect(pp.x - pp.sz / 2, pp.y - pp.sz / 2, pp.sz, pp.sz);
    }
    drawDrops();
    ctx.restore();

    // --- light. In normal play it reaches exactly as far as you can see, so
    //     nothing leaks out of the dark. In blackout, gunfire is the one thing
    //     that finds people for you.
    var reach = blackout ? FLASH_REACH : VIEW_R;
    ctx.lineCap = 'round';
    for (i = 0; i < bullets.length; i++) {
      var b = bullets[i];
      if (!litVisible(b.x, b.y, reach)) continue;
      // every round draws the same yellow streak with a hot core
      var tailX = b.x - b.vx * 0.019, tailY = b.y - b.vy * 0.019;
      ctx.strokeStyle = 'rgba(255,198,52,.55)';
      ctx.lineWidth = 3.6 / zoom;
      ctx.beginPath(); ctx.moveTo(b.x, b.y); ctx.lineTo(tailX, tailY); ctx.stroke();
      ctx.strokeStyle = 'rgba(255,247,196,.95)';
      ctx.lineWidth = 1.3 / zoom;
      ctx.beginPath(); ctx.moveTo(b.x, b.y); ctx.lineTo(tailX, tailY); ctx.stroke();
    }
    var smF = ctx.imageSmoothingEnabled;
    ctx.imageSmoothingEnabled = false;
    for (i = 0; i < flashes.length; i++) {
      var fl = flashes[i];
      if (!litVisible(fl.x, fl.y, reach)) continue;
      var fa = fl.t / fl.max;
      if (blackout) {
        var fg = ctx.createRadialGradient(fl.x, fl.y, 0, fl.x, fl.y, 120);
        fg.addColorStop(0, 'rgba(255,238,196,' + (0.42 * fa).toFixed(3) + ')');
        fg.addColorStop(1, 'rgba(255,238,196,0)');
        ctx.fillStyle = fg;
        ctx.fillRect(fl.x - 120, fl.y - 120, 240, 240);
      }
      if (FX.flash) {
        var ffi = Math.min(FX.flash.frames - 1, Math.floor((1 - fa) * FX.flash.frames));
        ctx.save();
        ctx.translate(fl.x, fl.y);
        ctx.rotate(fl.ang);
        var fs = 0.28 * (fl.scale || 1);
        ctx.scale(fs, fs);
        ctx.translate(0, -FX.flash.fh / 2);      // barrel sits at the left edge
        fxDraw(FX.flash, ffi, 1);
        ctx.restore();
      } else {
        ctx.globalAlpha = 0.9 * fa;
        ctx.fillStyle = fl.tint;
        ctx.beginPath(); ctx.arc(fl.x, fl.y, 4 + 7 * fa, 0, 6.2832); ctx.fill();
        ctx.globalAlpha = 1;
      }
    }
    ctx.imageSmoothingEnabled = smF;

    // --- sound made visible. Only in blackout, where it is the point.
    ctx.lineCap = 'round';
    for (i = 0; blackout && i < sounds.length; i++) {
      var s = sounds[i];
      if (s.x + s.r < vx0 || s.x - s.r > vx1 || s.y + s.r < vy0 || s.y - s.r > vy1) continue;
      var fade = 1 - s.r / s.maxR;
      var own = s.owner === player.id;
      var a = fade * fade * (own ? 0.28 : 0.85);
      if (a <= 0.01) continue;
      ctx.strokeStyle = 'rgba(' + s.color + ',' + a.toFixed(3) + ')';
      ctx.lineWidth = (s.w * (own ? 0.7 : 1)) / zoom * 1.6;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 6.2832); ctx.stroke();
    }

    if (smokes.length) {
      ctx.save();
      ctx.clip(poly);
      for (i = 0; i < smokes.length; i++) {
        var sm2 = smokes[i];
        if (sm2.alpha <= 0.01) continue;
        var sg = ctx.createRadialGradient(sm2.x, sm2.y, sm2.r * 0.25, sm2.x, sm2.y, sm2.r);
        sg.addColorStop(0, 'rgba(176,182,190,' + (0.97 * sm2.alpha).toFixed(3) + ')');
        sg.addColorStop(0.72, 'rgba(150,157,166,' + (0.92 * sm2.alpha).toFixed(3) + ')');
        sg.addColorStop(1, 'rgba(126,133,142,0)');
        ctx.fillStyle = sg;
        ctx.beginPath(); ctx.arc(sm2.x, sm2.y, sm2.r, 0, 6.2832); ctx.fill();
      }
      ctx.restore();
    }

    if (zone) {
      ctx.save();
      ctx.beginPath();
      ctx.rect(vx0 - 200, vy0 - 200, (vx1 - vx0) + 400, (vy1 - vy0) + 400);
      ctx.arc(zone.cx, zone.cy, zone.r, 0, 6.2832);
      ctx.fillStyle = 'rgba(255,77,141,.055)';
      ctx.fill('evenodd');
      ctx.restore();
      ctx.strokeStyle = 'rgba(255,77,141,.6)';
      ctx.lineWidth = 2.2 / zoom;
      ctx.beginPath(); ctx.arc(zone.cx, zone.cy, zone.r, 0, 6.2832); ctx.stroke();
      if (!zone.closing) {
        ctx.strokeStyle = 'rgba(198,212,227,.22)';
        ctx.lineWidth = 1.4 / zoom;
        ctx.setLineDash([9 / zoom, 9 / zoom]);
        ctx.beginPath(); ctx.arc(zone.nx, zone.ny, zone.nr, 0, 6.2832); ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    if (player.alive && player.air !== 'plane') drawUnit(player, curW(player) ? '#8ff0e4' : '#5d7288');
    if (plane && plane.t < plane.dur + 2) drawPlane();

    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
    renderTutorial();
    renderDropHint();
    renderHostHold();
    renderAllies();
    renderObjectives();
    if (SET.minimap && !splitVs()) drawMinimap();
    renderReticle();
    renderDowned();
    renderPrompt();
    renderDamage();
    if (touchMode && !splitOn) renderSticks();
  }

  function drawUnit(e, color) {
    if (e.air === 'chute') { drawChute(e); return; }
    var spr = SPRITES[e === player ? 'player' : 'enemy'];
    if (PACK_READY && e.down) {
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
      var tint = TEAM_TINT[e.team === player.team ? 0 : 1];
      ctx.fillStyle = 'rgba(' + tint + ',' + (e === player ? '.40' : '.36') + ')';
      ctx.beginPath(); ctx.ellipse(e.x, e.y, e.r * 1.35, e.r * 1.35, 0, 0, 6.2832); ctx.fill();
      drawPacked(e);
      if (e.swingT > 0) {
        var sw2 = 1 - e.swingT / 0.18;
        ctx.strokeStyle = 'rgba(214,228,242,' + (0.75 * (1 - sw2)).toFixed(3) + ')';
        ctx.lineWidth = 3 / zoom;
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.r + 24, e.ang - 1.0 + sw2 * 2.0, e.ang - 0.7 + sw2 * 2.0);
        ctx.stroke();
      }
      for (var cf = 0; cf < flags.length; cf++) {
        if (flags[cf].carrier !== e) continue;
        var cft = TEAM_TINT[flags[cf].team === player.team ? 0 : 1];
        ctx.strokeStyle = 'rgba(' + cft + ',.95)';
        ctx.lineWidth = 2 / zoom;
        ctx.beginPath(); ctx.moveTo(e.x, e.y - 6); ctx.lineTo(e.x, e.y - 24); ctx.stroke();
        ctx.fillStyle = 'rgba(' + cft + ',.9)';
        ctx.beginPath();
        ctx.moveTo(e.x, e.y - 24); ctx.lineTo(e.x + 13, e.y - 19); ctx.lineTo(e.x, e.y - 14);
        ctx.closePath(); ctx.fill();
      }
      if (e !== player) {
        var hw = 22, hp0 = clamp(e.hp / 100, 0, 1);
        ctx.fillStyle = 'rgba(10,15,22,.8)';
        ctx.fillRect(e.x - hw / 2, e.y - e.r - 13, hw, 2.6);
        ctx.fillStyle = 'rgba(' + tint + ',.9)';
        ctx.fillRect(e.x - hw / 2, e.y - e.r - 13, hw * hp0, 2.6);
      }
      return;
    }
    if (SHEET) {
      // a soft disc under the feet is what separates you from them, since
      // both sides are drawn from the same sheet
      ctx.fillStyle = e === player ? 'rgba(124,231,216,.30)' : 'rgba(255,122,77,.34)';
      ctx.beginPath(); ctx.ellipse(e.x, e.y + e.r * 0.5, e.r * 1.25, e.r * 0.68, 0, 0, 6.2832); ctx.fill();
    }
    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.rotate(e.ang);
    if (SHEET) {
      var fr = sheetFrame(e);
      var sy = SHEET.rowY ? SHEET.rowY[fr.row] : fr.row * SHEET.fh;
      var sh2 = e.r * SHEET.scale, sw2 = sh2 * (SHEET.fw / SHEET.fh);
      var sm = ctx.imageSmoothingEnabled;
      ctx.imageSmoothingEnabled = false;            // keep pixel art crisp
      ctx.drawImage(SHEET.img, fr.col * SHEET.fw, sy, SHEET.fw, SHEET.fh, -sw2 / 2, -sh2 / 2, sw2, sh2);
      ctx.imageSmoothingEnabled = sm;
    } else if (spr) {
      var sh = e.r * 3.4, sw = sh * (spr.width / spr.height);
      ctx.drawImage(spr, -sw / 2, -sh / 2, sw, sh);
    } else {
      if (curW(e)) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.2 / zoom;
        ctx.beginPath();
        ctx.moveTo(0, 0); ctx.lineTo(e.r + 9, 0);
        ctx.stroke();
      }
      ctx.fillStyle = color;
      ctx.beginPath(); ctx.arc(0, 0, e.r, 0, 6.2832); ctx.fill();
    }
    ctx.restore();
    if (e !== player) {
      var w = 22, hp = clamp(e.hp / 100, 0, 1);
      ctx.fillStyle = 'rgba(10,15,22,.8)';
      ctx.fillRect(e.x - w / 2, e.y - e.r - 9, w, 2.6);
      ctx.fillStyle = 'rgba(255,122,77,.9)';
      ctx.fillRect(e.x - w / 2, e.y - e.r - 9, w * hp, 2.6);
    }
  }

  function renderDowned() {
    if (!player.alive || !player.down) return;
    var label = player.revT > 0
      ? 'BEING PICKED UP  ' + Math.ceil(2.6 - player.revT) + 's'
      : 'DOWNED  \u00b7  ' + Math.ceil(player.downT) + 's  \u00b7  ' + promptKey('X', 'B') + ' TO GIVE UP';
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

  // On a pad there is no mouse to show where you are pointing, so put a dot
  // out in front - at half a screen, or on the first wall in the way.
  var cursorHidden = null;
  function renderReticle() {
    if (noOverlay) return;
    var on = usingPad(player);
    var hideC = splitOn ? usingPad(kbPlayer()) : on;
    if (cursorHidden !== hideC) {
      cursorHidden = hideC;
      canvas.style.cursor = hideC ? 'none' : 'crosshair';
    }
    if (!on || !player.alive || player.down) return;
    var maxD = Math.min(cw, ch) * 0.5 / zoom;
    var cx3 = Math.cos(player.ang), cy3 = Math.sin(player.ang);
    var d = maxD, step = TILE * 0.35;
    for (var t = step; t < maxD; t += step) {
      if (wallAt(player.x + cx3 * t, player.y + cy3 * t)) { d = t; break; }
    }
    var sx3 = (player.x + cx3 * d - cam.x) * zoom + cw / 2;
    var sy3 = (player.y + cy3 * d - cam.y) * zoom + ch / 2;
    var ox3 = (player.x + cx3 * (player.r + 10) - cam.x) * zoom + cw / 2;
    var oy3 = (player.y + cy3 * (player.r + 10) - cam.y) * zoom + ch / 2;
    ctx.save();
    ctx.strokeStyle = 'rgba(124,231,216,.45)';
    ctx.lineWidth = 1.6;
    ctx.setLineDash([2, 7]);
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(ox3, oy3); ctx.lineTo(sx3, sy3); ctx.stroke();
    ctx.restore();
    ctx.fillStyle = 'rgba(124,231,216,.9)';
    ctx.beginPath(); ctx.arc(sx3, sy3, 2.6, 0, 6.2832); ctx.fill();
    ctx.strokeStyle = 'rgba(124,231,216,.32)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(sx3, sy3, 7.5, 0, 6.2832); ctx.stroke();
  }

  function renderPrompt() {
    if (noOverlay) return;
    if (!promptItem || !player.alive) return;
    var w = WEAPONS[promptItem.key];
    var label = w.name + '  \u00b7  ' + w.snd.maxR + ' u';
    ctx.font = '600 11px "IBM Plex Mono", monospace';
    var tw = ctx.measureText(label).width;
    var boxW = tw + 54, boxH = 26;
    var bx = cw / 2 - boxW / 2, by = ch * 0.68;
    ctx.fillStyle = 'rgba(10,15,22,.85)';
    ctx.fillRect(bx, by, boxW, boxH);
    ctx.strokeStyle = 'rgba(124,231,216,.5)';
    ctx.lineWidth = 1;
    ctx.strokeRect(bx + .5, by + .5, boxW - 1, boxH - 1);
    ctx.fillStyle = '#7ce7d8';
    ctx.textBaseline = 'middle';
    ctx.fillText(promptKey('E', 'X'), bx + 14, by + boxH / 2 + 1);
    ctx.fillStyle = '#c6d4e3';
    ctx.fillText(label, bx + 36, by + boxH / 2 + 1);
  }

  // Squadmates are the one thing the dark does not hide - you would be on
  // comms with them. Enemies stay unmarked.
  var noOverlay = false;            // screenshot tool: world only, no markers
  function pill(txt, x, y, tint) {
    var w = ctx.measureText(txt).width + 12;
    ctx.fillStyle = 'rgba(13,15,18,.82)';
    ctx.fillRect(x - w / 2, y - 8, w, 16);
    ctx.strokeStyle = tint; ctx.lineWidth = 1.5;
    ctx.strokeRect(x - w / 2 + 0.5, y - 7.5, w - 1, 15);
    ctx.fillStyle = tint;
    ctx.fillText(txt, x, y + 0.5);
  }
  function renderAllies() {
    if (noOverlay || !player.alive) return;
    var mates = [];
    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (a === player || !a.alive || a.hidden || a.air === 'plane' || a.team !== player.team) continue;
      mates.push(a);
    }
    if (!mates.length) return;
    // real players first, then the nearest bots
    mates.sort(function (x, y) {
      return ((x.bot ? 1 : 0) - (y.bot ? 1 : 0)) || (dist(x, player) - dist(y, player));
    });
    var shownBots = 0;
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    for (var m = 0; m < mates.length; m++) {
      var t = mates[m];
      if (t.bot && ++shownBots > 8) continue;
      var human = !t.bot;
      var tint = t.down ? '#ff4d8d' : (human ? '#f2bd1d' : '#7ce7d8');
      var sx = (t.x - cam.x) * zoom + cw / 2;
      var sy = (t.y - cam.y) * zoom + ch / 2;
      var pad = 30;
      var off = sx < pad || sx > cw - pad || sy < pad || sy > ch - pad;
      var ang = Math.atan2(t.y - player.y, t.x - player.x);
      var d = Math.round(dist(t, player));
      sx = clamp(sx, pad, cw - pad);
      sy = clamp(sy, pad, ch - pad);
      ctx.fillStyle = tint;
      ctx.strokeStyle = '#0d0f12';
      var pulse = 1 + Math.sin(performance.now() / 260 + m) * 0.12;
      if (off) {
        // off screen: a big arrow on the edge, their name and how far
        ctx.save();
        ctx.translate(sx, sy);
        ctx.rotate(ang);
        ctx.shadowColor = tint; ctx.shadowBlur = 10;
        ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(-10, -12); ctx.lineTo(13, 0); ctx.lineTo(-10, 12); ctx.closePath();
        ctx.stroke(); ctx.fill();
        ctx.restore();
        ctx.font = '700 10px "IBM Plex Mono", monospace';
        var lbl = (human ? t.name + '  ' : '') + d + 'u';
        pill(lbl, sx, sy + 24, tint);
      } else {
        // on screen: a ring at their feet, a bold marker and a name tag
        var rr2 = (t.r + 9) * zoom * pulse;
        ctx.lineWidth = 5; ctx.strokeStyle = '#0d0f12';
        ctx.beginPath(); ctx.arc(sx, sy, rr2, 0, 6.2832); ctx.stroke();
        ctx.lineWidth = 2.5; ctx.strokeStyle = tint;
        ctx.beginPath(); ctx.arc(sx, sy, rr2, 0, 6.2832); ctx.stroke();
        var my = sy - rr2 - 10;
        ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 4;
        ctx.shadowColor = tint; ctx.shadowBlur = 8;
        ctx.beginPath(); ctx.moveTo(sx - 11, my - 12); ctx.lineTo(sx + 11, my - 12); ctx.lineTo(sx, my + 2); ctx.closePath();
        ctx.stroke(); ctx.fill();
        ctx.shadowBlur = 0;
        ctx.font = (human ? '700 11px' : '700 10px') + ' "IBM Plex Mono", monospace';
        pill(t.down ? t.name + ' DOWN' : t.name, sx, my - 24, tint);
      }
    }
    ctx.textAlign = 'left';
    ctx.restore();
  }

  // Objectives are map knowledge, so they are marked wherever they are -
  // pinned to the screen edge with a bearing and range when they are off it.
  function marker(wx, wy, label, tint, hollow) {
    var sx = (wx - cam.x) * zoom + cw / 2;
    var sy = (wy - cam.y) * zoom + ch / 2;
    var pad = 30;
    var off = sx < pad || sx > cw - pad || sy < pad || sy > ch - pad;
    sx = clamp(sx, pad, cw - pad);
    sy = clamp(sy, pad, ch - pad);
    ctx.save();
    ctx.globalAlpha = off ? 0.92 : 0.6;
    ctx.strokeStyle = 'rgba(' + tint + ',.9)';
    ctx.fillStyle = 'rgba(' + tint + ',' + (hollow ? '.18' : '.75') + ')';
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(sx, sy - 9); ctx.lineTo(sx + 9, sy); ctx.lineTo(sx, sy + 9); ctx.lineTo(sx - 9, sy);
    ctx.closePath();
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = hollow ? 'rgba(' + tint + ',.95)' : '#04060a';
    ctx.font = '700 9px "Chakra Petch", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, sx, sy + 1);
    if (off) {
      ctx.fillStyle = 'rgba(' + tint + ',.8)';
      ctx.font = '600 8.5px "IBM Plex Mono", monospace';
      var d = Math.round(Math.sqrt((wx - player.x) * (wx - player.x) + (wy - player.y) * (wy - player.y)));
      ctx.fillText(d + 'u', sx, sy + 19);
    }
    ctx.textAlign = 'left';
    ctx.globalAlpha = 1;
    ctx.restore();
  }

  function renderObjectives() {
    if (!player.alive) return;
    var i;
    for (i = 0; i < sectors.length; i++) {
      var sc = sectors[i];
      var tint = sc.owner < 0 ? '198,212,227' : TEAM_TINT[sc.owner === player.team ? 0 : 1];
      marker(sc.x, sc.y, sc.name, tint, sc.owner < 0);
    }
    for (i = 0; i < flags.length; i++) {
      var f = flags[i];
      var ft = TEAM_TINT[f.team === player.team ? 0 : 1];
      marker(f.hx, f.hy, 'H', ft, true);                       // the stand
      var known = f.home || (f.carrier && f.carrier.team === player.team) || visibleToPlayer(f.x, f.y);
      if (known && !f.home) marker(f.x, f.y, 'F', ft, false);  // and the flag itself
    }
  }

  // The drop plane, top down: a chunky transport in the pack's colours.
  function drawPlane() {
    var a = Math.atan2(plane.dy, plane.dx);
    function body(ox, oy, fill, line) {
      ctx.save();
      ctx.translate(plane.x + ox, plane.y + oy);
      ctx.rotate(a);
      ctx.lineJoin = 'round';
      ctx.lineWidth = line ? 3.5 : 0;
      ctx.strokeStyle = '#0d0f12';
      ctx.fillStyle = fill;
      // wings
      ctx.beginPath();
      ctx.moveTo(8, 0); ctx.lineTo(-14, -78); ctx.lineTo(-34, -78); ctx.lineTo(-26, 0);
      ctx.lineTo(-34, 78); ctx.lineTo(-14, 78); ctx.closePath();
      ctx.fill(); if (line) ctx.stroke();
      // tail
      ctx.beginPath();
      ctx.moveTo(-60, 0); ctx.lineTo(-76, -28); ctx.lineTo(-86, -28); ctx.lineTo(-82, 0);
      ctx.lineTo(-86, 28); ctx.lineTo(-76, 28); ctx.closePath();
      ctx.fill(); if (line) ctx.stroke();
      // fuselage
      ctx.beginPath();
      ctx.moveTo(62, 0); ctx.quadraticCurveTo(58, -14, 30, -14); ctx.lineTo(-80, -9);
      ctx.lineTo(-80, 9); ctx.lineTo(30, 14); ctx.quadraticCurveTo(58, 14, 62, 0);
      ctx.fill(); if (line) ctx.stroke();
      if (line) {
        ctx.fillStyle = '#f2bd1d';
        ctx.fillRect(-40, -3, 60, 6);                     // gold stripe
        ctx.fillStyle = '#9fd3e8';
        ctx.beginPath(); ctx.ellipse(46, 0, 7, 9, 0, 0, 6.2832); ctx.fill(); ctx.stroke();
        // engines
        ctx.fillStyle = '#1d2d3b';
        ctx.fillRect(-12, -52, 22, 11); ctx.strokeRect(-12, -52, 22, 11);
        ctx.fillRect(-12, 41, 22, 11); ctx.strokeRect(-12, 41, 22, 11);
      }
      ctx.restore();
    }
    body(46, 58, 'rgba(0,0,0,.28)', false);                // shadow on the ground
    body(0, 0, '#2e4559', true);
  }

  function drawChute(e) {
    var k = clamp(e.airT / CHUTE_TIME, 0, 1);              // 0 just out, 1 on the ground
    var hgt = (1 - k) * 34;
    // shadow shrinks toward you as you come down
    ctx.fillStyle = 'rgba(0,0,0,.3)';
    ctx.beginPath(); ctx.ellipse(e.x + hgt * 0.8, e.y + hgt, 10, 7, 0, 0, 6.2832); ctx.fill();
    var R = 24 + (1 - k) * 8;
    var tint = e.team === player.team ? '#f2bd1d' : '#e0643a';
    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.rotate(e.ang);
    ctx.lineWidth = 2.5; ctx.strokeStyle = '#0d0f12';
    for (var i = 0; i < 6; i++) {                          // panels
      ctx.fillStyle = i % 2 ? tint : '#f1e7d0';
      ctx.beginPath(); ctx.moveTo(0, 0);
      ctx.arc(0, 0, R, i * Math.PI / 3, (i + 1) * Math.PI / 3);
      ctx.closePath(); ctx.fill(); ctx.stroke();
    }
    ctx.fillStyle = '#0d0f12';
    ctx.beginPath(); ctx.arc(0, 0, 4, 0, 6.2832); ctx.fill();
    ctx.restore();
  }

  function renderHostHold() {
    if (!netGuest || !netHostHeld) return;
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '400 20px "Russo One", "Chakra Petch", sans-serif';
    ctx.fillStyle = '#f2bd1d';
    ctx.fillText('HOST PAUSED', cw / 2, ch * 0.3);
    ctx.restore();
  }

  // Capture the flag: tell the carrier exactly what has to happen next.
  function renderFlagHint() {
    if (!MODE.ctf || !player.alive || !flags.length) return;
    var carrying = null;
    for (var i = 0; i < flags.length; i++) if (flags[i].carrier === player) carrying = flags[i];
    var own = flags[player.team];
    if (!carrying && (!own || own.home)) return;
    var txt, sub2;
    if (carrying) {
      if (own.home && !own.carrier) { txt = 'RUN IT HOME'; sub2 = 'Get to your flag stand to score'; }
      else { txt = 'YOUR FLAG IS TAKEN'; sub2 = 'It has to be back on your stand before you can score - hold on, or get it back'; }
    } else {
      txt = own.carrier ? 'THEY HAVE YOUR FLAG' : 'YOUR FLAG IS DOWN';
      sub2 = own.carrier ? 'Kill the carrier to drop it' : 'Touch it to send it home';
    }
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '400 16px "Russo One", "Chakra Petch", sans-serif';
    var tw = ctx.measureText(txt).width + 36, bx = cw / 2 - tw / 2, by = ch * 0.2;
    var warn = carrying && !(own.home && !own.carrier);
    ctx.fillStyle = warn || !carrying ? '#ff4d8d' : '#f2bd1d';
    ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 3;
    ctx.fillRect(bx, by, tw, 32); ctx.strokeRect(bx, by, tw, 32);
    ctx.fillStyle = '#0d0f12';
    ctx.fillText(txt, cw / 2, by + 17);
    ctx.font = '500 10px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#f1e7d0';
    ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 3;
    ctx.strokeText(sub2, cw / 2, by + 46); ctx.fillText(sub2, cw / 2, by + 46);
    ctx.restore();
  }

  function renderKillcam(kc) {
    var k = kc.k;
    ctx.setTransform(dpr, 0, 0, dpr, dpr * VX, dpr * VY);
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
    var line = kc.gun + '  \u00b7  ' + kc.d + 'u AWAY  \u00b7  ' + kc.hp + ' HP LEFT';
    ctx.lineWidth = 4; ctx.strokeText(line, cw / 2, ty + 36);
    ctx.fillStyle = '#f1e7d0'; ctx.fillText(line, cw / 2, ty + 36);
    // what happens next
    var nxt = kc.after ? 'RESULTS IN ' + Math.max(1, Math.ceil(kc.dur - kc.t))
            : (kc.victim.respawnT > 0 ? 'RESPAWN IN ' + Math.ceil(kc.victim.respawnT) : '');
    if (nxt) {
      ctx.font = '500 11px "IBM Plex Mono", monospace';
      ctx.fillStyle = 'rgba(241,231,208,.7)';
      ctx.fillText(nxt, cw / 2, ch - bar - 22);
    }
    ctx.restore();
  }

  function renderDropHint() {
    renderFlagHint();
    if (!player.alive || !player.air) return;
    var txt, sub2 = null;
    if (player.air === 'plane') {
      var left = Math.max(0, plane.dur * 0.93 - plane.t);
      if (jumpOpen()) {
        txt = promptKey('SPACE', 'A') + '  JUMP';
        sub2 = 'THE PLANE DROPS EVERYONE IN ' + Math.ceil(left) + 's';
      } else {
        txt = 'DOOR OPENS IN ' + Math.max(1, Math.ceil(JUMP_AFTER - plane.t));
        sub2 = 'Pick your spot on the map';
      }
    } else {
      txt = 'STEER YOUR LANDING';
      sub2 = promptKey('WASD', 'LEFT STICK');
    }
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '400 18px "Russo One", "Chakra Petch", sans-serif';
    var tw = ctx.measureText(txt).width + 40, bx = cw / 2 - tw / 2, by = ch * 0.7;
    ctx.fillStyle = '#f2bd1d'; ctx.strokeStyle = '#0d0f12'; ctx.lineWidth = 3;
    ctx.fillRect(bx, by, tw, 36); ctx.strokeRect(bx, by, tw, 36);
    ctx.fillStyle = '#0d0f12';
    ctx.fillText(txt, cw / 2, by + 19);
    ctx.font = '500 10px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#f1e7d0';
    ctx.fillText(sub2, cw / 2, by + 52);
    ctx.restore();
  }

  // ---- minimap: only ground you have actually seen ------------------------
  var mini = null, miniAge = 0, miniReveal = false;
  function drawMinimap() {
    if (!mini) mini = document.createElement('canvas');
    var rev = false;
    for (var lq = 0; lq < locals.length; lq++) if (locals[lq].air) rev = true;
    if (rev !== miniReveal) { miniReveal = rev; miniAge = 0; }
    if (mini.width !== MAP_W || mini.height !== MAP_H) {
      mini.width = MAP_W; mini.height = MAP_H; miniAge = 0;
    }
    if (miniAge <= 0) {
      miniAge = 20;                       // a repaint every 20 frames is plenty
      var g = mini.getContext('2d');
      var img = g.createImageData(MAP_W, MAP_H);
      var d = img.data;
      for (var y = 0; y < MAP_H; y++) for (var x = 0; x < MAP_W; x++) {
        var o4 = (y * MAP_W + x) * 4, gi = y * STRIDE + x;
        if (!explored[gi] && !miniReveal) { d[o4 + 3] = 0; continue; }
        var wall = grid[gi] === 1;
        d[o4] = wall ? 62 : 20;
        d[o4 + 1] = wall ? 82 : 30;
        d[o4 + 2] = wall ? 106 : 42;
        d[o4 + 3] = wall ? 240 : 190;
      }
      g.putImageData(img, 0, 0);
    }
    miniAge--;

    var S = Math.round(Math.min(148, Math.min(cw, ch) * 0.30));
    // bottom left, above your health and kit
    var bx = 16, by = Math.max(60, ch - S - (splitOn ? 78 : 158));
    var span = MAP_W * TILE;
    function mx(wx) { return bx + (wx / span) * S; }
    function my(wy) { return by + (wy / (MAP_H * TILE)) * S; }

    ctx.save();
    ctx.fillStyle = 'rgba(8,12,18,.78)';
    ctx.fillRect(bx, by, S, S);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(mini, bx, by, S, S);
    ctx.imageSmoothingEnabled = true;

    if (plane && miniReveal) {
      ctx.strokeStyle = 'rgba(242,189,29,.8)';
      ctx.lineWidth = 1.2;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(mx(plane.x0), my(plane.y0));
      ctx.lineTo(mx(plane.x0 + plane.dx * plane.len), my(plane.y0 + plane.dy * plane.len));
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#f2bd1d';
      ctx.beginPath(); ctx.arc(mx(plane.x), my(plane.y), 3.2, 0, 6.2832); ctx.fill();
    }
    if (zone) {
      ctx.strokeStyle = 'rgba(255,77,141,.75)';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.arc(mx(zone.cx), my(zone.cy), zone.r / span * S, 0, 6.2832);
      ctx.stroke();
      if (!zone.closing && zone.nr) {
        ctx.strokeStyle = 'rgba(210,222,236,.4)';
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(mx(zone.nx), my(zone.ny), zone.nr / span * S, 0, 6.2832);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
    for (var sq2 = 0; sq2 < sectors.length; sq2++) {
      var ms = sectors[sq2];
      var mst = ms.owner < 0 ? '198,212,227' : (ms.owner === player.team ? '124,231,216' : '255,122,77');
      ctx.strokeStyle = 'rgba(' + mst + ',.85)';
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(mx(ms.x), my(ms.y), 4.5, 0, 6.2832); ctx.stroke();
    }
    for (var fi = 0; fi < flags.length; fi++) {
      var mf = flags[fi];
      var mt = mf.team === player.team ? '124,231,216' : '255,122,77';
      ctx.strokeStyle = 'rgba(' + mt + ',.6)';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(mx(mf.hx), my(mf.hy), 4, 0, 6.2832); ctx.stroke();
      var known = mf.home || (mf.carrier && mf.carrier.team === player.team) || visibleToPlayer(mf.x, mf.y);
      if (known) {
        ctx.fillStyle = 'rgba(' + mt + ',.95)';
        ctx.fillRect(mx(mf.x) - 2, my(mf.y) - 3, 4, 6);
      }
    }
    for (var i = 0; i < ents.length; i++) {
      var a = ents[i];
      if (!a.alive || a === player || a.team !== player.team) continue;
      ctx.fillStyle = '#7ce7d8';
      ctx.beginPath(); ctx.arc(mx(a.x), my(a.y), 2.4, 0, 6.2832); ctx.fill();
    }
    if (player.alive) {
      ctx.fillStyle = '#eaf4ff';
      ctx.beginPath(); ctx.arc(mx(player.x), my(player.y), 2.8, 0, 6.2832); ctx.fill();
      ctx.strokeStyle = '#eaf4ff';
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(mx(player.x), my(player.y));
      ctx.lineTo(mx(player.x) + Math.cos(player.ang) * 8, my(player.y) + Math.sin(player.ang) * 8);
      ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(146,170,196,.35)';
    ctx.lineWidth = 1;
    ctx.strokeRect(bx + .5, by + .5, S - 1, S - 1);
    ctx.restore();
  }

  function renderDamage() {
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
      var bt = 'BLEEDING ' + Math.ceil(player.bleedLeft || 0) + ' HP  \u00b7  ' + promptKey('F', 'Y') + ' TO USE A STIM' + (player.meds ? '' : ' (NONE - FIND ONE)');
      ctx.lineWidth = 4; ctx.strokeStyle = '#0d0f12'; ctx.strokeText(bt, cw / 2, ch * 0.78);
      ctx.fillStyle = '#ff5a68'; ctx.fillText(bt, cw / 2, ch * 0.78);
      ctx.restore();
    }
    for (var i = 0; i < dmgMarks.length; i++) {
      var m = dmgMarks[i];
      if (m.who !== undefined && m.who !== player.id) continue;
      var a = clamp(m.t / 1.1, 0, 1) * 0.6;
      var rad = Math.min(cw, ch) * 0.42;
      ctx.save();
      ctx.translate(cw / 2, ch / 2);
      ctx.rotate(m.ang + Math.PI);
      ctx.strokeStyle = 'rgba(255,77,141,' + a.toFixed(3) + ')';
      ctx.lineWidth = 7;
      ctx.beginPath(); ctx.arc(0, 0, rad, -0.34, 0.34); ctx.stroke();
      ctx.restore();
    }
    var hurt = 1 - clamp(player.hp / 100, 0, 1);
    if (hurt > 0.05) {
      var vg = ctx.createRadialGradient(cw / 2, ch / 2, Math.min(cw, ch) * 0.28, cw / 2, ch / 2, Math.max(cw, ch) * 0.62);
      vg.addColorStop(0, 'rgba(255,40,90,0)');
      vg.addColorStop(1, 'rgba(255,40,90,' + (hurt * 0.3).toFixed(3) + ')');
      ctx.fillStyle = vg;
      ctx.fillRect(0, 0, cw, ch);
    }
  }

  function renderSticks() {
    ['move', 'aim'].forEach(function (k) {
      var s = sticks[k];
      if (!s) return;
      ctx.strokeStyle = 'rgba(198,212,227,.22)';
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(s.ox, s.oy, 46, 0, 6.2832); ctx.stroke();
      var dx = s.x - s.ox, dy = s.y - s.oy;
      var d = Math.sqrt(dx * dx + dy * dy) || 1;
      var cl = Math.min(d, 46);
      ctx.fillStyle = k === 'aim' ? 'rgba(255,77,141,.5)' : 'rgba(124,231,216,.5)';
      ctx.beginPath(); ctx.arc(s.ox + dx / d * cl, s.oy + dy / d * cl, 17, 0, 6.2832); ctx.fill();
    });
  }

  // ---------------------------------------------------------------- menu bg
  var amb = { rings: [], t: 0 };
  var AMB_KINDS = [
    WEAPONS.pistol.snd, WEAPONS.shotgun.snd,
    WEAPONS.rifle.snd, WEAPONS.silenced.snd, MOVE_SND.walk, MOVE_SND.sprint
  ];
  function renderAmbient() {
    // the world's own ground, slowly drifting, pushed well back
    amb.drift = (amb.drift || 0) + 1 / 60;
    if (floorPat) {
      ctx.save();
      ctx.translate(-(amb.drift * 9) % (TILE * 8), -(amb.drift * 5) % (TILE * 8));
      ctx.fillStyle = floorPat;
      ctx.fillRect(0, 0, cw + TILE * 8, ch + TILE * 8);
      ctx.restore();
      ctx.fillStyle = 'rgba(16,13,9,.5)';
    } else {
      ctx.fillStyle = '#17140f';
    }
    ctx.fillRect(0, 0, cw, ch);
    amb.t -= 1 / 60;
    if (amb.t <= 0) {
      amb.t = rr(0.35, 1.1);
      var def = AMB_KINDS[rnd(AMB_KINDS.length)];
      amb.rings.push({ x: rr(-0.15, 1.15) * cw, y: rr(-0.15, 1.15) * ch, r: 0, max: def.maxR * 0.3, def: def });
      if (amb.rings.length > 26) amb.rings.shift();
    }
    ctx.lineCap = 'round';
    for (var i = amb.rings.length - 1; i >= 0; i--) {
      var g = amb.rings[i];
      g.r += g.def.speed / 400;
      if (g.r > g.max) { amb.rings.splice(i, 1); continue; }
      var fade = 1 - g.r / g.max;
      ctx.strokeStyle = 'rgba(242,189,29,' + (fade * fade * 0.4).toFixed(3) + ')';
      ctx.lineWidth = g.def.w * 1.4;
      ctx.beginPath(); ctx.arc(g.x, g.y, g.r, 0, 6.2832); ctx.stroke();
    }
  }

  // ---------------------------------------------------------------- input
  // ---- controller ---------------------------------------------------------
  function getPad(i) {
    var l = navigator.getGamepads ? navigator.getGamepads() : null;
    return (i >= 0 && l && l[i] && l[i].connected) ? l[i] : null;
  }
  function axOf(g, i) {
    if (!g || !g.axes || g.axes.length <= i) return 0;
    var v = g.axes[i], dz = SET.dead / 100;
    if (v > -dz && v < dz) return 0;
    return (v - (v > 0 ? dz : -dz)) / (1 - dz);
  }
  function downOf(g, i) { return !!(g && g.buttons && g.buttons[i] && g.buttons[i].pressed); }
  function hitOf(g, prev, i) {
    var now = downOf(g, i), was = prev[i];
    prev[i] = now;
    return now && !was;
  }
  // Is this player on a pad right now? Drives the button labels and the aim dot.
  function usingPad(e) {
    var c = e && e.ctl;
    if (!c || c.any) return padActive();
    if (c.pad < 0) return false;
    if (!c.kb) return true;
    return (e.padLast || -1e9) > kbmLast;
  }

  var pad = null, padPrev = {}, padSeen = false, padLast = -1e9;
  var padRest = {}, kbmLast = -1e9;
  function padBusy(g) {
    var rest = padRest[g.index];
    if (!rest) { rest = padRest[g.index] = g.axes.slice(); return false; }
    for (var j = 0; j < g.buttons.length; j++) if (g.buttons[j] && g.buttons[j].pressed) return true;
    for (j = 0; j < g.axes.length; j++) if (Math.abs(g.axes[j] - (rest[j] || 0)) > Math.max(0.2, SET.dead / 100)) return true;
    return false;
  }
  function pollPad() {
    var list = navigator.getGamepads ? navigator.getGamepads() : null;
    pad = null;
    if (!list) return;
    for (var i = 0; i < list.length; i++) {
      if (list[i] && list[i].connected) { pad = list[i]; padSeen = true; break; }
    }
    if (!pad) return;
    // note when the stick or a button was last touched, so the prompts can
    // switch between keyboard and controller on their own
    if (padBusy(pad)) padLast = performance.now();
  }
  function padActive() {
    return !!pad && padLast > kbmLast;
  }
  // Prompts read as whatever you are actually holding.
  function promptKey(keyLabel, padLabel) { return usingPad(player) ? padLabel : keyLabel; }
  function padAxis(i) {
    if (!pad || !pad.axes || pad.axes.length <= i) return 0;
    var v = pad.axes[i];
    var dz = SET.dead / 100;
    if (v > -dz && v < dz) return 0;
    // rescale so the stick starts moving right at the edge of the deadzone
    return (v - (v > 0 ? dz : -dz)) / (1 - dz);
  }
  function padDown(i) { return !!(pad && pad.buttons && pad.buttons[i] && pad.buttons[i].pressed); }
  function padHit(i) {                       // pressed this frame only
    var now = padDown(i), was = padPrev[i];
    padPrev[i] = now;
    return now && !was;
  }

  // Nudge the aim toward whoever is closest to where you are already pointing.
  // ---- driving the screens with a pad ------------------------------------
  // ---- driving every screen with a pad ---------------------------------
  // Up/down/left/right move to whatever is actually in that direction on
  // screen - down goes to the next row, not the next button along.
  var uiScr = null, uiRepeat = 0;
  function uiScreen() {
    var ids = ['osk', 'account', 'chat', 'friends', 'online', 'paused', 'over', 'settings', 'shop', 'menu'];
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
      var sc;
      if (dy) {
        // must sit clearly in the next row, above or below; the nearest row
        // always wins, then whatever in it lines up best
        if (dy > 0 ? q.top < r.bottom - 4 : q.bottom > r.top + 4) continue;
        var gap = Math.max(0, dy > 0 ? q.top - r.bottom : r.top - q.bottom);
        sc = Math.round(gap / 6) * 10000 + Math.abs(qx - cx);
      } else {
        if (dx > 0 ? qx <= cx + 2 : qx >= cx - 2) continue;
        if (Math.abs(qy - cy) > Math.max(r.height, q.height)) continue;    // same row only
        sc = Math.abs(qx - cx) + Math.abs(qy - cy) * 2;
      }
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
    else if (!$('chat').hidden) $('chatBack').click();
    else if (!$('friends').hidden) $('friendsBack').click();
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
    [['SHIFT', 'abc'], [' ', 'SPACE'], ['BACK', '\u232b DELETE'], ['DONE', 'DONE']].forEach(function (p) {
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
    $('oskText').textContent = (t && t.type === 'password' ? v.replace(/./g, '\u2022') : v) || ' ';
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
      uiScr = uiScreen();            // stay on the box you were typing in
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

  function screenToWorld(sx, sy) {
    mouse.sx = sx; mouse.sy = sy;
    updateMouseWorld();
  }
  // The cursor has to be re-projected every frame, not only when it moves:
  // the camera slides underneath a still mouse.
  function updateMouseWorld() {
    if (mouse.sx === undefined || !player) return;
    var L = kbPlayer(), c = L.cam || cam;
    var vx = L.viewW ? L.viewX : 0, vy = L.viewH ? L.viewY : 0, vw = L.viewW || cw, vh = L.viewH || ch, z = L.zoom || zoom;
    mouse.wx = (mouse.sx - vx - vw / 2) / z + c.x;
    mouse.wy = (mouse.sy - vy - vh / 2) / z + c.y;
  }
  canvas.addEventListener('pointerdown', function (ev) {
    if (ev.pointerType !== 'touch') kbmLast = performance.now();
    var r = canvas.getBoundingClientRect();
    if (ev.pointerType === 'touch') {
      touchMode = true;
      var side = (ev.clientX - r.left) < cw / 2 ? 'move' : 'aim';
      if (!sticks[side]) sticks[side] = { id: ev.pointerId, ox: ev.clientX - r.left, oy: ev.clientY - r.top, x: ev.clientX - r.left, y: ev.clientY - r.top };
    } else {
      initAudio();
      mouse.down = true;
    }
    ev.preventDefault();
  });
  canvas.addEventListener('pointermove', function (ev) {
    if (ev.pointerType !== 'touch' && (Math.abs(ev.movementX || 0) + Math.abs(ev.movementY || 0)) > 2) kbmLast = performance.now();
    var r = canvas.getBoundingClientRect();
    var px = ev.clientX - r.left, py = ev.clientY - r.top;
    if (ev.pointerType === 'touch') {
      ['move', 'aim'].forEach(function (k) {
        if (sticks[k] && sticks[k].id === ev.pointerId) { sticks[k].x = px; sticks[k].y = py; }
      });
    } else { mouse.sx = px; mouse.sy = py; screenToWorld(px, py); }
  });
  function releasePointer(ev) {
    if (ev.pointerType === 'touch') {
      ['move', 'aim'].forEach(function (k) { if (sticks[k] && sticks[k].id === ev.pointerId) sticks[k] = null; });
    } else mouse.down = false;
  }
  canvas.addEventListener('pointerup', releasePointer);
  canvas.addEventListener('pointercancel', releasePointer);
  canvas.addEventListener('contextmenu', function (e) { e.preventDefault(); });

  window.addEventListener('keydown', function (e) {
    kbmLast = performance.now();
    var k = e.key.toLowerCase();
    keys[k] = true;
    // number keys by position, so Shift (sprint) held down does not turn
    // 1 and 2 into ! and @
    if (e.code === 'Digit1' || e.code === 'Numpad1') k = '1';
    else if (e.code === 'Digit2' || e.code === 'Numpad2') k = '2';
    if (netRole && (state === 'play') && (k === 't' || k === 'enter') && $('igChat').hidden) { e.preventDefault(); openIgChat(); return; }
    if (netGuest && state === 'play') {
      var GB = { 'e': PAD.pickup, ' ': PAD.jump, 'v': PAD.melee, 'x': PAD.giveup, 'r': PAD.reload, 'f': PAD.stim,
                 'h': PAD.smoke, 'g': PAD.frag, 'q': PAD.swapL, '1': PAD.swapL, '2': PAD.swapL, 'z': PAD.drop };
      if (k === 'escape') { if (settingsOpenFromPause()) $('setBack').click(); else if (netGuestPaused) resume(); else pause(); }
      else if (GB[k] !== undefined && !netGuestPaused && !e.repeat) guestHits |= 1 << GB[k];
      if (['w', 'a', 's', 'd', ' '].indexOf(k) >= 0) e.preventDefault();
      return;
    }
    if (state === 'play') {
      var kp = kbPlayer();
      if (kp.air === 'plane' && (k === 'e' || k === ' ')) kp.jumpReq = true;
      if (kp.air) { if (k === 'escape') pause(); return; }
      if (k === 'r') startReload(kp);
      else if (k === 'e') playerPickup(kp);
      else if (k === 'q') swapSlot(undefined, kp);
      else if (k === '1') swapSlot(0, kp);
      else if (k === '2') swapSlot(1, kp);
      else if (k === 'f') useMed(kp);
      else if (k === 'g') throwNade(kp, 'frag');
      else if (k === 'h') throwNade(kp, 'smoke');
      else if (k === 'v') melee(kp);
      else if (k === 'z') dropWeapon(kp);
      else if (k === 'x' && kp.down) { kp.hp = 0; kill(kp, -1); }
      else if (k === 'escape') pause();
    } else if (k === 'escape' && state === 'paused') { if (settingsOpenFromPause()) $('setBack').click(); else resume(); }
    if (['w', 'a', 's', 'd', ' '].indexOf(k) >= 0) e.preventDefault();
  });
  window.addEventListener('keyup', function (e) { keys[e.key.toLowerCase()] = false; });
  window.addEventListener('blur', function () {
    keys = {}; mouse.down = false;
    if (state === 'play' && !netRole) pause();      // a friend online keeps playing
  });

  var MODE_LABEL = { tut: 'Tutorial', br: 'Battle royale', duel: '1v1', gun: 'Gun game', team: 'Teams 5v5', war: 'War 10v10', ctf: 'Capture the flag', sect: 'Sector capture', zomb: 'Infection' };
  function pause() {
    cgGame('gameplayStop');
    if (netGuest) {                                   // the host's match keeps going
      netGuestPaused = true;
      $('pauseSub').textContent = 'ONLINE \u00b7 the match keeps running';
      elPaused.hidden = false;
      return;
    }
    if (state !== 'play') return;
    state = 'paused';
    $('pauseSub').textContent = MODE_LABEL[mode]
      + (mode === 'br' ? ' \u00b7 ' + mapKind.toUpperCase() : '')
      + (blackout ? ' \u00b7 blackout' : '');
    elPaused.hidden = false;
  }
  function resume() {
    cgGame('gameplayStart');
    if (netGuest) { netGuestPaused = false; elPaused.hidden = true; return; }
    if (state !== 'paused') return;
    state = 'play';
    elPaused.hidden = true;
    last = performance.now();
  }
  function leaveMatch() {
    if (netGuest) { netClose('You left the match.'); return; }
    if (netRole === 'host') hostEndMatch('The host left the match.');
    goHome();
  }
  $('resumeBtn').addEventListener('click', resume);
  $('leaveBtn').addEventListener('click', leaveMatch);

  function pressRow(row, attr, value) {
    Array.prototype.forEach.call(row.querySelectorAll('button'), function (b) {
      b.setAttribute('aria-pressed', b.getAttribute(attr) === value ? 'true' : 'false');
    });
  }
  var MODE_TEAMMATES = { team: 1, war: 1, ctf: 1, sect: 1, zomb: 1 };
  function syncMenu() {
    $('mapPick').hidden = (mode === 'duel');
    $('squadPick').hidden = !!MODES[mode].teams;
    if (mode === 'tut') return;                   // the menu is not showing during the tutorial
    var t = mode === 'br' ? MODE_TEXT['br_' + mapKind] : MODE_TEXT[mode];
    if (mode !== 'br' && mode !== 'duel') {
      t += mapKind === 'world'
        ? '  \u2014  WORLD: open ground and scattered buildings, with long sightlines between them.'
        : '  \u2014  CQB: a dense warren of rooms and corridors.';
    }
    if (squad > 1 && mode !== 'team') t += '  \u2014  DUOS: you drop with a partner, you cannot hurt each other, and neither of you reacts to the other\'s noise.';
    if (netRole === 'host' && netGuests.length) t += '  \u2014  PARTY: ' + netGuests.length + (netGuests.length > 1 ? ' friends' : ' friend') + ' will drop in with you.' + (squad < 2 && !MODE_TEAMMATES[mode] ? ' Solo: rivals. DUOS: partners.' : '');
    if (netRole === 'guest') t = 'ONLINE: connected. The host picks the mode and starts the match.';
    if (splitWant && !netRole) {
      var np = padIndices().length;
      t += np >= 2 ? '  \u2014  SPLIT SCREEN: one controller each.'
         : np === 1 ? '  \u2014  SPLIT SCREEN: P1 on keyboard and mouse, P2 on the controller.'
         : '  \u2014  SPLIT SCREEN: plug in a controller for player 2 and press a button on it.';
      if (squad < 2 && !MODE_TEAMMATES[mode]) t += ' In solo you two are rivals; pick DUOS to team up.';
    }
    if (blackout) t += '  \u2014  BLACKOUT: your eyes reach barely past your own feet. Sound tells you roughly where someone is; the flash of their gun is the only thing that tells you exactly.';
    $('modeDesc').textContent = t;
    if (netRole === 'guest') { $('startBtn').textContent = 'WAITING FOR HOST'; return; }
    $('startBtn').textContent = mode === 'br' ? 'DROP IN'
      : (mode === 'duel' ? 'FIGHT' : (mode === 'gun' ? 'START LADDER' : 'DEPLOY'));
  }
  $('squadRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    squad = parseInt(b.getAttribute('data-s'), 10);
    pressRow(this, 'data-s', String(squad));
    syncMenu();
  });
  $('playersRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    splitWant = b.getAttribute('data-n') === '2';
    pressRow(this, 'data-n', splitWant ? '2' : '1');
    syncMenu();
  });
  $('lightRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    blackout = b.getAttribute('data-l') === 'black';
    pressRow(this, 'data-l', blackout ? 'black' : 'normal');
    syncMenu();
  });
  function partyPickRow(rowId, menuRowId, attr, apply) {
    $(rowId).addEventListener('click', function (ev) {
      var b = ev.target.closest('button');
      if (!b) return;
      apply(b.getAttribute(attr));
      $(menuRowId).querySelector('[' + attr + '="' + b.getAttribute(attr) + '"]').click();   // keep the menu in step
      partyRender();
      partyBroadcast();
    });
  }
  partyPickRow('partyModeRow', 'modeRow', 'data-m', function (v) { mode = v; });
  partyPickRow('partyMapRow', 'mapRow', 'data-p', function (v) { mapKind = v; });
  partyPickRow('partySquadRow', 'squadRow', 'data-s', function (v) { squad = parseInt(v, 10); });
  partyPickRow('partyDiffRow', 'diffRow', 'data-d', function (v) { difficulty = parseInt(v, 10); });
  partyPickRow('partyBotsRow', 'botsRow', 'data-b', function (v) { botFill = parseFloat(v); });
  $('partyStart').addEventListener('click', function () { startMatch(); });
  $('pchatSend').addEventListener('click', function () { sendPartyChat($('pchatInput').value); $('pchatInput').value = ''; });
  $('pchatInput').addEventListener('keydown', function (ev) {
    ev.stopPropagation();
    if (ev.key === 'Enter') { sendPartyChat(this.value); this.value = ''; }
  });
  // in a match: T (or Enter) to say something to the party
  $('igChatInput').addEventListener('keydown', function (ev) {
    ev.stopPropagation();
    if (ev.key === 'Enter') { sendPartyChat(this.value); this.value = ''; closeIgChat(); }
    else if (ev.key === 'Escape') closeIgChat();
  });
  function openIgChat() {
    if (cgNoChat()) return; keys = {}; mouse.down = false; $('igChat').hidden = false; $('igChatInput').focus(); }
  function closeIgChat() { $('igChat').hidden = true; $('igChatInput').blur(); }
  $('modeRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    mode = b.getAttribute('data-m');
    pressRow(this, 'data-m', mode);
    syncMenu();
  });
  $('mapRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    mapKind = b.getAttribute('data-p');
    pressRow(this, 'data-p', mapKind);
    syncMenu();
  });
  $('botsRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    botFill = parseFloat(b.getAttribute('data-b'));
    pressRow(this, 'data-b', b.getAttribute('data-b'));
  });
  $('diffRow').addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    difficulty = parseInt(b.getAttribute('data-d'), 10);
    pressRow(this, 'data-d', String(difficulty));
  });
  function refreshCoins() {
    var a = $('menuCoins'), b = $('coinsN');
    if (a) a.textContent = WALLET.coins;
    if (b) b.textContent = WALLET.coins;
  }

  // The shop previews each skin by composing it exactly as the game would.
  function buildShop() {
    var grid = $('shopGrid');
    if (!grid) return;
    grid.innerHTML = '';
    for (var i = 0; i < 16; i++) (function (idx) {
      var card = document.createElement('div');
      card.tabIndex = 0;
      card.className = 'skincard' + (WALLET.skin === idx ? ' on' : '') + (skinOwned(idx) ? '' : ' locked');
      var pv = document.createElement('canvas');
      pv.width = 104; pv.height = 156;
      if (PACK_READY) {
        var src = buildChar(idx, 'rifle');
        pv.getContext('2d').drawImage(src, 0, 0, src.width, src.height, 0, 0, 104, 156);
      }
      card.appendChild(pv);
      var lab = document.createElement('span');
      lab.textContent = skinOwned(idx)
        ? (WALLET.skin === idx ? 'WEARING' : 'SELECT')
        : skinPrice(idx) + ' CR';
      card.appendChild(lab);
      card.addEventListener('click', function () {
        if (skinOwned(idx)) {
          WALLET.skin = idx;
        } else if (WALLET.coins >= skinPrice(idx)) {
          WALLET.coins -= skinPrice(idx);
          WALLET.owned.push(idx);
          WALLET.skin = idx;
        } else {
          lab.textContent = 'NEED ' + (skinPrice(idx) - WALLET.coins);
          return;
        }
        saveWallet();
        refreshCoins();
        buildShop();
      });
      grid.appendChild(card);
    })(i);
  }

  function goHome() {
    cgGame('gameplayStop');
    for (var kq = 0; kq < locals.length; kq++) locals[kq].kc = null;
    netGuest = false; netGuestPaused = false;
    if (tutRestore) { mode = tutRestore.mode; mapKind = tutRestore.mapKind; blackout = tutRestore.blackout; squad = tutRestore.squad; tutRestore = null; MODE = MODES[mode]; }
    setTimeout(syncMenu, 0);
    $('againBtn').hidden = false;
    state = 'menu';
    keys = {}; mouse.down = false;
    elOver.hidden = true; elHud.hidden = true; elPaused.hidden = true;
    $('shop').hidden = true;
    $('settings').hidden = true;
    elMenu.hidden = false;
    refreshCoins();
  }

  function syncSettings() {
    $('setVol').value = SET.vol; $('setVolV').textContent = SET.vol;
    $('setMusic').value = SET.music; $('setMusicV').textContent = SET.music;
    $('setDead').value = SET.dead; $('setDeadV').textContent = SET.dead;
    [['setShake', 'shake'], ['setMap', 'minimap'], ['setBlood', 'blood']].forEach(function (pair) {
      var b = $(pair[0]);
      b.textContent = SET[pair[1]] ? 'ON' : 'OFF';
      b.className = 'tgl' + (SET[pair[1]] ? ' on' : '');
    });
    pollPad();
    $('padTag').textContent = pad ? ('controller: ' + String(pad.id).slice(0, 38))
                                  : (padSeen ? 'controller disconnected' : 'no controller detected');
  }
  $('setMusic').addEventListener('input', function () {
    SET.music = parseInt(this.value, 10); $('setMusicV').textContent = SET.music; saveSettings();
  });
  $('setVol').addEventListener('input', function () {
    SET.vol = parseInt(this.value, 10); $('setVolV').textContent = SET.vol; saveSettings();
  });
  $('setDead').addEventListener('input', function () {
    SET.dead = parseInt(this.value, 10); $('setDeadV').textContent = SET.dead; saveSettings();
  });
  [['setShake', 'shake'], ['setMap', 'minimap'], ['setBlood', 'blood']].forEach(function (pair) {
    $(pair[0]).addEventListener('click', function () {
      SET[pair[1]] = !SET[pair[1]];
      saveSettings();
      syncSettings();
    });
  });
  // Settings open from the menu or from the pause screen, and go back there.
  var setFrom = 'menu';
  $('setBtn').addEventListener('click', function () {
    syncSettings();
    setFrom = 'menu';
    elMenu.hidden = true;
    $('settings').hidden = false;
  });
  $('pauseSetBtn').addEventListener('click', function () {
    syncSettings();
    setFrom = 'pause';
    elPaused.hidden = true;
    $('settings').hidden = false;
  });
  $('setBack').addEventListener('click', function () {
    $('settings').hidden = true;
    if (setFrom === 'pause' && (state === 'paused' || netGuestPaused)) elPaused.hidden = false;
    else if (setFrom === 'pause') { /* the match moved on (ended) - nothing to go back to */ }
    else elMenu.hidden = false;
  });
  function settingsOpenFromPause() { return setFrom === 'pause' && !$('settings').hidden; }
  window.addEventListener('gamepadconnected', function () { padSeen = true; syncSettings(); syncMenu(); });

  $('shopBtn').addEventListener('click', function () {
    buildShop(); refreshCoins();
    elMenu.hidden = true;
    $('shop').hidden = false;
  });
  $('shopBack').addEventListener('click', function () {
    $('shop').hidden = true;
    elMenu.hidden = false;
  });

  $('tutBtn').addEventListener('click', function () {
    if (netRole === 'guest') { openOnline(); return; }
    var was = { mode: mode, mapKind: mapKind, blackout: blackout, squad: squad };
    mode = 'tut'; mapKind = 'cqb'; blackout = false; squad = 1;
    startMatch();
    // the menu keeps what you had picked
    mode = 'tut'; tutRestore = was;
  });
  var tutRestore = null;
  $('startBtn').addEventListener('click', function () {
    if (netRole === 'guest') { openOnline(); return; }         // the host starts
    startMatch();
  });
  $('againBtn').addEventListener('click', function () { elOver.hidden = true; startMatch(); });
  $('homeBtn').addEventListener('click', function () {
    if (netRole === 'host' && netPublic) hostEndMatch('The host left.');
    goHome();
  });

  // ---------------------------------------------------------------- online
  var PEER_JS = 'https://cdn.jsdelivr.net/npm/peerjs@1.5.4/dist/peerjs.min.js';
  var netEv = [], netDefs = [], netSendT = 0, netSigs = {}, guestHits = 0, netInT = 0;
  var netQueue = [], guestYou = -1, netLastIn = '', quickFail = null, guestStickAt = -1e9, guestTrig = false;
  var netStat = { sent: 0, recv: 0, err: '', bytes: 0, rbytes: 0 };
  var WKEYS = Object.keys(WEAPONS);

  function netStatus(txt) { var el = $('netStatus'); if (el) el.textContent = txt; }
  // The host stops playing: friends go back to the party, strangers are let go.
  function hostEndMatch(why) {
    for (var i = netGuests.length - 1; i >= 0; i--) {
      var g = netGuests[i];
      if (g.party) netSendTo(g, { t: 'end', why: why });
      else { netSendTo(g, { t: 'end', why: why, bye: true }); try { g.conn.close(); } catch (err) {} netGuests.splice(i, 1); }
      g.ent = null;
    }
    netPublic = false;
    lobbyDrop();
    partyBroadcast(); partyRender();
  }
  function netHostLive() {
    if (netRole !== 'host' || !(state === 'play' || state === 'paused' || state === 'ending')) return false;
    for (var i = 0; i < netGuests.length; i++) if (netGuests[i].ent) return true;
    return false;
  }
  function netStr(obj) {
    return JSON.stringify(obj, function (k, v) {
      return (typeof v === 'number' && v % 1) ? Math.round(v * 100) / 100 : v;
    });
  }
  // guest -> host (the guest has a single connection)
  function netSend(obj) {
    if (!netConn || !netConn.open) return;
    try { netConn.send(netStr(obj)); netStat.sent++; } catch (err) { netStat.err = String(err && err.message || err); }
  }
  function netSendTo(g, objOrStr) {
    if (!g.conn || !g.conn.open) return;
    var pay = typeof objOrStr === 'string' ? objOrStr : netStr(objOrStr);
    try { g.conn.send(pay); netStat.sent++; netStat.bytes += pay.length; }
    catch (err) { netStat.err = String(err && err.message || err); }
  }
  function netSendAll(obj) { var str = netStr(obj); for (var i = 0; i < netGuests.length; i++) netSendTo(netGuests[i], str); }
  function netDefId(def) {
    if (def.__nid === undefined) { def.__nid = netDefs.length; netDefs.push(def); }
    return def.__nid;
  }

  function loadPeer(cb) {
    if (window.Peer) { cb(); return; }
    var sc = document.createElement('script');
    sc.src = PEER_JS;
    sc.onload = cb;
    sc.onerror = function () { netStatus('Could not load the connection library. Check your internet.'); };
    document.head.appendChild(sc);
  }
  function roomCode() {
    var A = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789', c = '';
    for (var i = 0; i < 5; i++) c += A.charAt(rnd(A.length));
    return c;
  }
  function netClose(why) {
    var wasGuest = netRole === 'guest';
    if (netRole === 'host') netSendAll({ t: 'end', why: 'The host closed the party.', bye: true });
    for (var i = 0; i < netGuests.length; i++) { try { netGuests[i].conn.close(); } catch (err) {} }
    netGuests = [];
    lobbyDrop();
    try { if (netConn) netConn.close(); } catch (err) {}
    try { if (netPeer) netPeer.destroy(); } catch (err) {}
    if (netRole) { cgCall(function (c) { c.game.leftRoom(); c.game.hideInviteButton(); }); if ($('cgInviteBtn')) $('cgInviteBtn').hidden = true; }
    netConn = null; netPeer = null; netRole = null; netPublic = false; netCode = '';
    pchat = []; if ($('pchatLog')) $('pchatLog').innerHTML = '';
    if (typeof queueOn !== 'undefined') queueOn = false;
    $('netCodeBox').hidden = true;
    if (wasGuest && (netGuest || state !== 'menu')) { goHome(); openOnline(); }
    netStatus(why || 'Disconnected.');
    partyRender();
    syncMenu();
  }

  // Open a room. `then` runs once the room code is live.
  function hostGame(then) {
    if (netRole === 'host' && netPeer && netCode) { if (typeof then === 'function') then(); return; }
    netClose('');
    netStatus('Starting...');
    loadPeer(function () {
      var code = roomCode();
      netPeer = new window.Peer('deadangle-' + code);
      netPeer.on('open', function () {
        netRole = 'host'; netCode = code;
        $('netCode').textContent = code;
        $('netCodeBox').hidden = false;
        netStatus(CG_MODE ? 'Party open. Share the invite link or this code.'
                          : 'Party open. Friends join with this code, or invite them from your friends list.');
        partyRender();
        cgRoom();
        syncMenu();
        if (typeof then === 'function') then();
      });
      netPeer.on('connection', function (conn) {
        var g = { conn: conn, name: 'PLAYER', skin: 0, uid: '', party: true, ent: null, sigs: {},
                  in: { ax: [0, 0], aim: null, down: 0, hits: 0 } };
        conn.on('data', function (raw) { hostReceive(g, raw); });
        conn.on('close', function () { hostLostGuest(g); });
        conn.on('error', function () { hostLostGuest(g); });
      });
      netPeer.on('error', function (err) {
        if (err && err.type === 'unavailable-id') { netRole = null; hostGame(then); return; }
        netStatus('Connection problem: ' + (err && err.type ? err.type : 'unknown') + '.');
      });
    });
  }
  function hostLostGuest(g) {
    var i = netGuests.indexOf(g);
    if (i < 0) return;
    netGuests.splice(i, 1);
    var L = g.ent;
    if (L) {
      // a bot takes the body back so the match can carry on
      L.local = false; L.bot = true; L.ctl = null; L.skip = L.skip || {};
      L.path = null; L.target = null;
      var li = locals.indexOf(L);
      if (li >= 0) locals.splice(li, 1);
      if (state === 'play' || state === 'paused') feed('<b>' + g.name + '</b> left - a bot takes over', false);
      g.ent = null;
    }
    partyBroadcast();
    partyRender();
    lobbyTouch();
    syncMenu();
  }
  function humansIn() { return 1 + netGuests.length; }
  function hostReceive(g, raw) {
    g.last = performance.now();
    var m; try { m = JSON.parse(raw); } catch (err) { return; }
    if (m.t === 'in') {
      g.in.ax = m.ax || [0, 0]; g.in.aim = m.aim; g.in.down = m.down | 0;
      g.in.hits |= m.hits | 0;
    } else if (m.t === 'pchat') {
      partySay(g.name, m.text);
    } else if (m.t === 'hi') {
      g.name = String(m.name || 'PLAYER').replace(/[^A-Za-z0-9_.]/g, '').slice(0, 20) || 'PLAYER';
      g.skin = clamp(m.skin | 0, 0, 15); g.uid = String(m.uid || ''); g.party = !m.pub;
      if (humansIn() >= NET_MAX || (m.pub && !netPublic)) {
        netSendTo(g, { t: 'full' });
        setTimeout(function () { try { g.conn.close(); } catch (err) {} }, 300);
        return;
      }
      netGuests.push(g);
      feed('<b>' + g.name + '</b> joined', true);
      if (queueOn) { queueSay = 0; lobbyT = 0.2; }
      if (state === 'play' || state === 'paused') {
        if (admitGuest(g, false)) netSendTo(g, startMsg(g));
        else netSendTo(g, { t: 'wait', why: 'Match in progress - you will be in the next one.' });
      }
      partyBroadcast();
      partyRender();
      lobbyTouch();
      syncMenu();
    }
  }

  // Put a guest into the match by taking over a bot. Friends go to the host's
  // side where they can; in battle royale only a body still on the plane will do.
  function admitGuest(g, atStart) {
    if (g.ent) return true;
    var hum = {}, i;
    for (i = 0; i < locals.length; i++) hum[locals[i].team] = (hum[locals[i].team] || 0) + 1;
    var best = null, bestScore = -1e9;
    for (i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e.bot || isZombie(e)) continue;
      if (mode === 'br' && !atStart && e.air !== 'plane') continue;
      if (mode === 'br' && !e.alive) continue;
      var sc2 = -(hum[e.team] || 0) * 10 + (e.alive ? 2 : 0) + Math.random();
      if (g.party && e.team === player.team) sc2 += 50;
      if (sc2 > bestScore) { bestScore = sc2; best = e; }
    }
    if (!best) return false;
    best.bot = false; best.local = true; best.ctl = { net: g };
    best.cam = { x: best.x, y: best.y };
    best.name = g.name; best.target = null; best.path = null;
    if (!MODE.teams && !MODE.zombies) { best.skin = g.skin; charCache = {}; }
    locals.push(best);
    g.ent = best; g.sigs = {};
    g.in = { ax: [0, 0], aim: null, down: 0, hits: 0 };
    if (!atStart) feed('<b>' + g.name + '</b> dropped in', true);
    return true;
  }

  function packRegion(src) {
    var out = '', row = [];
    for (var y = 0; y < MAP_H; y++) {
      row.length = 0;
      for (var x = 0; x < MAP_W; x++) row.push(src[y * STRIDE + x]);
      out += String.fromCharCode.apply(null, row);
    }
    return btoa(out);
  }
  function unpackRegion(b64, dst) {
    var str = atob(b64), k = 0;
    for (var y = 0; y < MAP_H; y++) for (var x = 0; x < MAP_W; x++) dst[y * STRIDE + x] = str.charCodeAt(k++);
  }
  var mapPack = null;
  function startMsg(g) {
    if (!mapPack || mapPack.token !== matchToken) mapPack = { token: matchToken, grid: packRegion(grid), mat: packRegion(mat) };
    g.sigs = {}; g.defsSent = 0;
    return { t: 'start', mode: mode, mapKind: mapKind, blackout: blackout, squad: squad, difficulty: difficulty,
             w: MAP_W, h: MAP_H, grid: mapPack.grid, mat: mapPack.mat, you: g.ent.id };
  }
  function netSendOver(g, won, msg, place) {
    var big = mode === 'br' ? '#' + place : (won ? 'WIN' : 'LOSS');
    netSendTo(g, { t: 'over', won: won, big: big, small: mode === 'br' ? 'OF ' + fieldN : '', msg: msg,
                   kills: g.ent.kills || 0, time: matchTime });
  }

  var NET_SEE = 1500;                       // how far a guest is told about
  function nearGuest(g, x, y) {
    var ge = g.ent;
    if (!ge) return true;
    var dx = x - ge.x, dy = y - ge.y;
    return dx * dx + dy * dy < NET_SEE * NET_SEE;
  }
  function packEnt(e) {
    var s0 = e.slots[0], s1 = e.slots[1];
    var bits = (e.alive ? 1 : 0) | (e.down ? 2 : 0) | (e.moving ? 4 : 0) |
               (e.air === 'plane' ? 8 : 0) | (e.air === 'chute' ? 16 : 0) | (e.bot ? 32 : 0) | (e.bleeding ? 64 : 0);
    return [e.id, Math.round(e.x), Math.round(e.y), e.ang, e.team, e.skin, bits, e.animT || 0, e.animFire || 0, e.swingT || 0,
            e.throwT || 0, e.meleeT || 0, Math.round(e.hp), e.revT || 0, e.downT || 0, e.respawnT || 0,
            e.level || 0, e.airT || 0, e.name, e.slot,
            s0 ? WKEYS.indexOf(s0.key) : -1, s0 ? s0.ammo : 0, s1 ? WKEYS.indexOf(s1.key) : -1, s1 ? s1.ammo : 0,
            e.reserve, e.meds, e.nades, e.smokes, e.reloadT || 0, e.useT || 0, e.kills || 0];
  }
  function sigOf(list) {
    var h = list.length;
    for (var i = Math.max(0, list.length - 3); i < list.length; i++) h = (h * 31 + (list[i].x | 0) * 7 + (list[i].y | 0)) | 0;
    return h;
  }
  var LTYPE = ['gun', 'ammo', 'med', 'nade', 'smoke'];
  function packLoot(it) {
    return [it.x | 0, it.y | 0, LTYPE.indexOf(it.type), it.key ? WKEYS.indexOf(it.key) : -1,
            it.ammo | 0, it.n | 0, (it.spin * 100) | 0, it.seen ? 1 : 0];
  }
  function unpackLoot(a) {
    return { x: a[0], y: a[1], type: LTYPE[a[2]], key: a[3] >= 0 ? WKEYS[a[3]] : null,
             ammo: a[4], n: a[5], spin: a[6] / 100, seen: !!a[7] };
  }
  function packMark(m) {
    return [m.x | 0, m.y | 0, +(m.ang || 0).toFixed(2), +(m.scale || 1).toFixed(2), +(m.t || 0).toFixed(2)];
  }
  function unpackMark(a) {
    return { x: a[0], y: a[1], ang: a[2], scale: a[3], t: a[4] };
  }
  function nearOnly(g, arr) {
    var out = [];
    for (var i = 0; i < arr.length; i++) if (nearGuest(g, arr[i].x, arr[i].y)) out.push(arr[i]);
    return out;
  }
  function listSig(arr) {
    var h = arr.length;
    for (var i = 0; i < arr.length; i++) h = (h * 31 + (arr[i].x | 0) + (arr[i].y | 0) * 7 + (arr[i].ammo | 0)) | 0;
    return h;
  }
  function lootSig() {
    var h = loot.length;
    for (var i = 0; i < loot.length; i++) h = (h * 31 + (loot[i].x | 0) + (loot[i].y | 0) * 7 + (loot[i].ammo | 0)) | 0;
    return h;
  }

  function netHostTick(dt) {
    lobbyTick(dt);
    if (queueOn) queueTick(dt);
    // a guest who has gone quiet for a long while has gone; the browser can
    // take ages to report a closed tab on its own
    var nowT = performance.now();
    for (var qi = netGuests.length - 1; qi >= 0; qi--) {
      var qg = netGuests[qi];
      if (qg.last && nowT - qg.last > 20000) { try { qg.conn.close(); } catch (err) {} hostLostGuest(qg); }
    }
    if (!netHostLive()) { netEv.length = 0; return; }
    netSendT -= dt;
    if (netSendT > 0) return;
    netSendT = 1 / 20;
    // everything everyone sees, serialised once
    var shared = netStr({
      t: 's', hold: state === 'paused',
      fl: flags.map(function (f) {
        return { team: f.team, hx: f.hx, hy: f.hy, x: f.x, y: f.y, home: f.home, ping: f.ping, carrier: f.carrier ? f.carrier.id : -1 };
      }),
      se: sectors, z: zone, p: plane,

      h: [alive, score[0], score[1], round, roundClock, roundBreak, zombClock, matchTime, fieldN],
      ev: netEv
    });

    for (var gi = 0; gi < netGuests.length; gi++) {
      var g = netGuests[gi];
      if (!g.ent) continue;
      // what this one person still needs: their own hit marks, and any lists
      // that changed since we last sent them
      // only what is near this guest: 48 people at 20 a second was a flood
      var x = { dm: dmgMarks.filter(function (m) { return m.who === g.ent.id; }) };
      x.e = [];
      for (var ei = 0; ei < ents.length; ei++) {
        var en = ents[ei];
        var ownSide = en === g.ent || en.team === g.ent.team;
        if (!ownSide && (en.air === 'plane' || !nearGuest(g, en.x, en.y))) continue;
        x.e.push(packEnt(en));
      }
      x.b = [];
      for (var bi = 0; bi < bullets.length; bi++) {
        var bu = bullets[bi];
        if (nearGuest(g, bu.x, bu.y)) x.b.push([Math.round(bu.x), Math.round(bu.y), Math.round(bu.vx), Math.round(bu.vy), bu.owner]);
      }
      x.f = flashes.filter(function (q) { return nearGuest(g, q.x, q.y); });
      x.im = impacts.filter(function (q) { return nearGuest(g, q.x, q.y); });
      x.sm = smokes.filter(function (q) { return nearGuest(g, q.x, q.y); });
      if (blackout) x.so = sounds.filter(function (q) { return nearGuest(g, q.x, q.y); }).map(function (q) {
        return { x: Math.round(q.x), y: Math.round(q.y), r: Math.round(q.r), maxR: q.maxR, speed: q.speed, color: q.color, w: q.w, kind: q.kind, owner: q.owner };
      });
      x.n = nades.filter(function (q) { return nearGuest(g, q.x, q.y); }).map(function (gn) {
        return { x: Math.round(gn.x), y: Math.round(gn.y), spin: gn.spin, kind: gn.kind, fuse: gn.fuse, owner: gn.owner };
      });
      // The floor near this guest, four times a second instead of twenty, and
      // not at all while they are still in the plane - a guest crossing the
      // map re-enters this set constantly, and resending it was most of the
      // traffic in a full battle royale.
      g.clut = (g.clut || 0) + 1;
      if (!g.ent.air && g.clut % 5 === 0) {
        var near = nearOnly(g, loot), sg = listSig(near);
        if (g.sigs.lo !== sg) { g.sigs.lo = sg; x.lo = near.map(packLoot); }
        near = nearOnly(g, decals); sg = listSig(near);
        if (g.sigs.dc !== sg) { g.sigs.dc = sg; x.dc = near.map(packMark); }
        near = nearOnly(g, deaths); sg = listSig(near);
        if (g.sigs.de !== sg) { g.sigs.de = sg; x.de = near.map(packMark); }
        near = nearOnly(g, corpses); sg = listSig(near);
        if (g.sigs.co !== sg) { g.sigs.co = sg; x.co = near.map(packMark); }
      }
      if ((g.defsSent || 0) < netDefs.length) {
        x.defs = {};
        for (var k = g.defsSent || 0; k < netDefs.length; k++) {
          var d = netDefs[k];
          x.defs[k] = { maxR: d.maxR, speed: d.speed, color: d.color, w: d.w, aud: d.aud, sample: d.sample, sampleGain: d.sampleGain, rate: d.rate };
        }
        g.defsSent = netDefs.length;
      }
      netSendTo(g, shared.slice(0, -1) + ',"x":' + netStr(x) + '}');
    }
    netEv = [];
  }

  // who is in the party, for everyone's screen
  function partyNames() {
    var n = [acctName || 'HOST'];
    for (var i = 0; i < netGuests.length; i++) if (netGuests[i].party) n.push(netGuests[i].name);
    return n;
  }
  function partyBroadcast() {
    cgRoom();
    if (netRole === 'host') netSendAll({ t: 'party', names: partyNames(), code: netCode,
      pick: MODE_LABEL[mode] + (mode !== 'duel' ? ' \u00b7 ' + mapKind.toUpperCase() : '') + (MODES[mode].teams ? '' : (squad > 1 ? ' \u00b7 DUOS' : ' \u00b7 SOLO')) +
        ' \u00b7 ' + ['CALM', 'STANDARD', 'RUTHLESS'][difficulty] + ' BOTS' + (botFill < 1 ? (botFill < 0.5 ? ' (FEW)' : ' (HALF)') : '') });
  }
  var partyList = [];
  function partyRender() {
    var el = $('partyList');
    if (!el) return;
    var names = netRole === 'host' ? partyNames() : (netRole === 'guest' ? partyList : []);
    el.innerHTML = '';
    names.forEach(function (nm, i) {
      var d = document.createElement('div');
      d.className = 'prow';
      d.textContent = (i === 0 ? '\u2605 ' : '') + nm;
      el.appendChild(d);
    });
    el.hidden = !names.length;
    pchatVisible();
    // the host picks the match right here once anyone has joined
    var pp = $('partyPick');
    if (pp) {
      pp.hidden = !(netRole === 'host' && netGuests.length > 0);
      pressRow($('partyModeRow'), 'data-m', mode);
      pressRow($('partyMapRow'), 'data-p', mapKind);
      pressRow($('partySquadRow'), 'data-s', String(squad));
      pressRow($('partyDiffRow'), 'data-d', String(difficulty));
      pressRow($('partyBotsRow'), 'data-b', String(botFill));
      $('partyMapPick').hidden = mode === 'duel';
      $('partySquadPick').hidden = !!MODES[mode].teams;
    }
  }

  // ---- party chat: rides the same connection as the game ----
  var pchat = [];
  function escHtml(t) { return String(t).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function pchatAdd(from, text) {
    if (cgNoChat()) return;
    pchat.push({ from: from, text: text });
    if (pchat.length > 60) pchat.shift();
    var log = $('pchatLog');
    if (log) {
      var d = document.createElement('div');
      d.className = 'cmsg' + (from === (acctName || (netRole === 'host' ? 'HOST' : 'PLAYER')) ? ' me' : '');
      var b = document.createElement('b'); b.textContent = from;
      var sp = document.createElement('span'); sp.textContent = text;
      d.appendChild(b); d.appendChild(sp);
      log.appendChild(d);
      while (log.children.length > 60) log.removeChild(log.firstChild);
      log.scrollTop = log.scrollHeight;
    }
    // in a match it shows in the feed, top right
    if (state === 'play' || state === 'paused') {
      var f = document.createElement('div');
      f.className = 'you';
      f.innerHTML = '<b>' + escHtml(from) + '</b>: ' + escHtml(text);
      elFeed.appendChild(f);
      while (elFeed.children.length > 6) elFeed.removeChild(elFeed.firstChild);
      setTimeout(function () { if (f.parentNode) f.parentNode.removeChild(f); }, 9000);
    }
  }
  function partySay(from, text) {
    text = cleanText(String(text || '').trim()).slice(0, 120);
    if (!text) return;
    pchatAdd(from, text);
    netSendAll({ t: 'pchat', from: from, text: text });
  }
  function sendPartyChat(text) {
    text = String(text || '').trim();
    if (!text || !netRole) return;
    if (netRole === 'host') partySay(acctName || 'HOST', text);
    else netSend({ t: 'pchat', text: text.slice(0, 120) });
  }
  function cleanText(t) { return typeof clean === 'function' ? clean(t) : t; }
  function pchatVisible() {
    var box = $('partyChat');
    if (box) box.hidden = cgNoChat() || !(netRole === 'guest' || (netRole === 'host' && netGuests.length > 0));
  }

  // Public-match hooks; the accounts module fills these in when it loads.
  var lobbyTouch = function () {}, lobbyDrop = function () {}, lobbyTick = function () {};

  // ---- the guest's side ----
  // pub: joining a stranger's public match. onFail: called instead of just
  // reporting, so Quick Play can try the next one.
  function joinGame(code, pub, onFail) {
    code = String(code || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (code.length !== 5) { netStatus('Room codes are 5 letters and numbers.'); return; }
    netClose('');
    netStatus('Connecting...');
    var failed = false;
    function fail(msg) {
      if (failed) return;
      failed = true;
      netClose(msg);
      if (onFail) onFail(msg);
    }
    loadPeer(function () {
      netPeer = new window.Peer();
      netPeer.on('open', function () {
        var conn = netPeer.connect('deadangle-' + code, { reliable: true, serialization: 'raw' });
        netConn = conn;
        var opened = false;
        setTimeout(function () { if (!opened && netConn === conn) fail('No answer from that code. Check it with your friend.'); }, 12000);
        conn.on('open', function () {
          opened = true;
          netRole = 'guest'; netCode = code;
          netSend({ t: 'hi', skin: WALLET.skin, name: acctName || 'PLAYER', uid: acctUid(), pub: !!pub });
          netStatus(pub ? 'Joining a match...' : 'Connected! Waiting for the host to start a match.');
          syncMenu();
          cgRoom();
        });
        conn.on('data', guestReceive);
        conn.on('close', function () { if (netConn === conn) { if (!opened) fail('Could not connect.'); else netClose('The host closed the game.'); } });
        conn.on('error', function () { if (netConn === conn) fail('Lost the connection.'); });
      });
      netPeer.on('error', function (err) {
        fail(err && err.type === 'peer-unavailable' ? 'No game with that code. Check it with your friend.'
                                                    : 'Connection problem: ' + (err && err.type ? err.type : 'unknown') + '.');
      });
    });
  }
  // a guest waiting in a party still says it is there
  setInterval(function () { if (netRole === 'guest') netSend({ t: 'ping' }); }, 4000);
  function acctUid() { return (window.firebase && firebase.auth && firebase.apps.length && firebase.auth().currentUser) ? firebase.auth().currentUser.uid : ''; }

  function guestReceive(raw) {
    netStat.recv++; netStat.rbytes += (raw && raw.length) || 0;
    var m; try { m = JSON.parse(raw); } catch (err) { netStat.err = 'parse: ' + typeof raw; return; }
    if (m.t === 's') {
      if (m.x) { for (var xk in m.x) m[xk] = m.x[xk]; }
      netQueue.push(m); if (netQueue.length > 30) netQueue.splice(0, netQueue.length - 30);
    }
    else if (m.t === 'pchat') pchatAdd(m.from, m.text);
    else if (m.t === 'party') {
      partyList = m.names || []; partyRender();
      if (!netGuest && m.pick) netStatus('In the party. The host picked ' + m.pick + ' - waiting for them to start.');
    }
    else if (m.t === 'wait') netStatus(m.why);
    else if (m.t === 'queue') netStatus(m.msg);
    else if (m.t === 'full') { netClose('That match is full.'); if (quickFail) quickFail(); }
    else if (m.t === 'start') guestStart(m);
    else if (m.t === 'over') guestOver(m);
    else if (m.t === 'end') {
      if (netGuest) { goHome(); openOnline(); }
      if (m.bye) netClose(m.why); else netStatus(m.why || 'The match ended.');
    }
  }

  function guestStart(m) {
    initAudio();
    matchToken++;
    mode = m.mode; MODE = MODES[mode]; mapKind = m.mapKind; blackout = !!m.blackout;
    squad = m.squad; difficulty = m.difficulty;
    VIEW_R = blackout ? VIEW_BLACKOUT : VIEW_BASE;
    MAP_W = m.w; MAP_H = m.h;
    grid.fill(0); mat.fill(0);
    unpackRegion(m.grid, grid); unpackRegion(m.mat, mat);
    finishMap();
    explored.fill(0);
    ents = []; bullets = []; sounds = []; parts = []; flashes = []; corpses = []; loot = [];
    decals = []; impacts = []; deaths = []; nades = []; flags = []; smokes = []; sectors = [];
    drops = []; splats = [];
    dmgMarks = []; shake = 0; promptItem = null; zone = null; plane = null;
    locals = []; splitOn = false; player = null; guestYou = m.you; netQueue = [];
    kills = 0; shots = 0; hits = 0; matchTime = 0; score = [0, 0]; result = null;
    charCache = {};
    elFeed.innerHTML = '';
    ['menu', 'over', 'paused', 'shop', 'settings', 'online', 'friends', 'account', 'chat'].forEach(function (id) { $(id).hidden = true; });
    elHud.hidden = false; elHud.classList.remove('split');
    netGuest = true; netGuestPaused = false;
    state = 'play';
    cgGame('gameplayStart');
  }

  function guestOver(m) {
    if (!netGuest) return;
    cgGame('gameplayStop');
    if (m.won) cgGame('happytime');
    var earned = (m.kills || 0) * 12 + Math.round((m.time || 0) / 6) + (m.won ? 80 : 0);
    WALLET.coins += earned;
    saveWallet();
    state = 'over';
    var tok = matchToken;
    setTimeout(function () {
      if (tok !== matchToken) return;
      $('placeN').textContent = m.big;
      $('placeN').className = m.won ? 'win' : '';
      $('placeL').textContent = m.small || '';
      $('overMsg').textContent = m.msg + '  +' + earned + ' credits.';
      $('stKills').textContent = m.kills || 0;
      $('stTime').textContent = fmtTime(m.time || 0);
      $('stAcc').textContent = '--';
      $('againBtn').hidden = true;                  // the host starts the next one
      elHud.hidden = true; elPaused.hidden = true;
      elOver.hidden = false;
    }, 850);
  }

  function netEnt(a) {
    var id = a[0], e = ents[id];
    if (!e) {
      e = makeEnt({ x: 0, y: 0 }, true, a[18]);
      e.id = id; e.x = a[1]; e.y = a[2];
      ents[id] = e;
    }
    var mine = e.id === guestYou;
    if (Math.abs(a[1] - e.x) + Math.abs(a[2] - e.y) > 90) { e.x = a[1]; e.y = a[2]; }
    e.tx = a[1]; e.ty = a[2];
    // your own body: you steer it here and now; the host's word only nudges
    // it back if the two drift apart
    if (!mine) e.ang = a[3]; e.team = a[4]; e.skin = a[5];
    var bits = a[6];
    e.alive = !!(bits & 1); e.down = !!(bits & 2); e.moving = !!(bits & 4);
    e.air = (bits & 8) ? 'plane' : ((bits & 16) ? 'chute' : null); e.bot = !!(bits & 32); e.bleeding = !!(bits & 64);
    e.animT = a[7]; e.animFire = a[8]; e.swingT = a[9]; e.throwT = a[10]; e.meleeT = a[11];
    e.hp = a[12]; e.revT = a[13]; e.downT = a[14]; e.respawnT = a[15]; e.level = a[16]; e.airT = a[17];
    e.name = a[18]; e.slot = a[19];
    e.slots[0] = a[20] >= 0 ? { key: WKEYS[a[20]], ammo: a[21] } : null;
    e.slots[1] = a[22] >= 0 ? { key: WKEYS[a[22]], ammo: a[23] } : null;
    e.reserve = a[24]; e.meds = a[25]; e.nades = a[26]; e.smokes = a[27];
    e.reloadT = a[28]; e.useT = a[29]; e.kills = a[30];
  }

  function applySnap(m) {
    var i;
    var seen = {};
    for (i = 0; i < m.e.length; i++) { netEnt(m.e[i]); seen[m.e[i][0]] = 1; }
    for (i = 0; i < ents.length; i++) {
      if (!ents[i]) { var st = makeEnt({ x: 0, y: 0 }, true, ''); st.id = i; st.alive = false; ents[i] = st; }
      ents[i].hidden = !seen[i];
    }
    if (!player && ents[guestYou]) {
      player = ents[guestYou];
      player.local = true; player.ctl = { any: true, kb: true }; player.cam = cam;
      cam.x = player.x; cam.y = player.y;
      locals = [player];
    }
    bullets = (m.b || []).map(function (b) { return { x: b[0], y: b[1], vx: b[2], vy: b[3], owner: b[4], life: 1 }; });
    flashes = m.f || []; impacts = m.im || []; smokes = m.sm || []; nades = m.n || [];
    flags = (m.fl || []).map(function (f) { f.carrier = f.carrier >= 0 ? ents[f.carrier] : null; return f; });
    sectors = m.se || []; zone = m.z; plane = m.p;
    if (m.so) sounds = m.so.map(function (q) { q.heard = {}; return q; });
    var h = m.h;
    alive = h[0]; score = [h[1], h[2]]; round = h[3]; roundClock = h[4]; roundBreak = h[5];
    zombClock = h[6]; matchTime = h[7]; fieldN = h[8];
    if (player) kills = player.kills || 0;
    dmgMarks = m.dm || [];
    if (m.lo) loot = m.lo.map(unpackLoot);
    if (m.dc) decals = m.dc.map(unpackMark);
    if (m.de) deaths = m.de.map(unpackMark);
    if (m.co) corpses = m.co.map(unpackMark);
    if (m.defs) for (var k in m.defs) netDefs[k] = m.defs[k];
    netHostHeld = !!m.hold;
    var ev = m.ev || [];
    for (i = 0; i < ev.length; i++) {
      var q = ev[i];
      if (q[0] === 'k') spark(q[1], q[2], q[3], q[4], q[5]);
      else if (q[0] === 'a') { if (netDefs[q[3]]) audioEmit(q[1], q[2], netDefs[q[3]], q[4]); }
      else if (q[0] === 'f') feed(q[1], q[2]);
      else if (q[0] === 'g') bleed(q[1], q[2], q[3], q[4], !!q[5], q[6]);
      else if (q[0] === 'c' && q[1] === guestYou && ents[q[2]]) {
        if (player) player.kc = { k: ents[q[2]], victim: player, t: 0, dur: 3.2, after: null, gun: q[3], hp: q[4], d: q[5] };
      }
    }
  }

  // The guest walks and turns its own player straight away, exactly as the
  // host will a moment later. Without this every step waited on the network.
  function guestPredict(dt) {
    var e = player;
    if (!e || !e.alive || e.down || e.air || netGuestPaused) return;
    var mx = 0, my = 0;
    if (pad) { mx = padAxis(0); my = padAxis(1); }
    if (!mx && !my) {
      if (keys['a']) mx -= 1; if (keys['d']) mx += 1;
      if (keys['w']) my -= 1; if (keys['s']) my += 1;
    }
    var ml = Math.sqrt(mx * mx + my * my);
    if (ml > 1) { mx /= ml; my /= ml; }
    var sprint = (!!keys['shift'] || (pad && padDown(PAD.sprint))) && (mx || my);
    var base = curW(e) ? 168 : 190;
    var sp = sprint ? base * 1.45 : base;
    if (mx || my) { moveEnt(e, mx * sp * dt, my * sp * dt); e.moving = true; e._spd = sp; }
    else { e.moving = false; e._spd = 0; }
    // aim where this player is pointing, now
    if (pad) {
      var rx = pad.axes[2] || 0, ry = pad.axes[3] || 0, dz = SET.dead / 100;
      if (rx * rx + ry * ry >= (dz + 0.1) * (dz + 0.1)) e.ang = Math.atan2(ry, rx);
    }
    if (!padActive() && mouse.sx !== undefined) e.ang = Math.atan2(mouse.wy - e.y, mouse.wx - e.x);
  }

  function guestTick(dt) {
    pollPad();
    while (netQueue.length) applySnap(netQueue.shift());
    if (!player) return;
    var i;
    // glide everyone toward where the host last put them
    var kk = Math.min(1, dt * 16);
    for (i = 0; i < ents.length; i++) {
      var e = ents[i];
      if (!e || e.tx === undefined) continue;
      if (e === player) {
        // gentle correction only, so your own movement never stutters
        var ex = e.tx - e.x, ey = e.ty - e.y, ed = Math.sqrt(ex * ex + ey * ey);
        if (ed > 120) { e.x = e.tx; e.y = e.ty; }
        else if (ed > 3) { e.x += ex * Math.min(1, dt * 2.5); e.y += ey * Math.min(1, dt * 2.5); }
        continue;
      }
      e.x += (e.tx - e.x) * kk; e.y += (e.ty - e.y) * kk;
    }
    guestPredict(dt);
    for (var p = parts.length - 1; p >= 0; p--) {
      var pt = parts[p];
      pt.life -= dt;
      if (pt.life <= 0) { parts.splice(p, 1); continue; }
      pt.x += pt.vx * dt; pt.y += pt.vy * dt; pt.vx *= 0.9; pt.vy *= 0.9;
    }
    for (i = decals.length - 1; i >= 0; i--) decals[i].t += dt;
    goreTick(dt);
    for (i = impacts.length - 1; i >= 0; i--) impacts[i].t += dt;
    for (i = 0; i < deaths.length; i++) deaths[i].t += dt;
    for (i = flashes.length - 1; i >= 0; i--) { flashes[i].t -= dt; if (flashes[i].t <= 0) flashes.splice(i, 1); }
    for (i = 0; i < bullets.length; i++) { bullets[i].x += bullets[i].vx * dt; bullets[i].y += bullets[i].vy * dt; }
    for (i = dmgMarks.length - 1; i >= 0; i--) { dmgMarks[i].t -= dt; if (dmgMarks[i].t <= 0) dmgMarks.splice(i, 1); }

    updateMouseWorld();
    var lerp = 1 - Math.pow(0.0001, dt);
    var glx = 0, gly = 0;
    if (!touchMode && !padActive()) {
      glx = clamp(mouse.wx - player.x, -110, 110) * 0.2;
      gly = clamp(mouse.wy - player.y, -110, 110) * 0.2;
    }
    player.leadX = (player.leadX || 0) + (glx - (player.leadX || 0)) * lerp;
    player.leadY = (player.leadY || 0) + (gly - (player.leadY || 0)) * lerp;
    killcamTick(dt);
    if (player.kc) {
      var gk = 1 - Math.pow(0.015, dt);
      cam.x += (player.kc.k.x - cam.x) * gk; cam.y += (player.kc.k.y - cam.y) * gk;
    } else {
      cam.x = player.x + player.leadX; cam.y = player.y + player.leadY;
    }
    syncHud();

    // controls out, as a virtual pad
    var mx = 0, my = 0, aim = null, down = 0, hitsNow = guestHits;
    guestHits = 0;
    if (!netGuestPaused) {
      if (pad) {
        mx = padAxis(0); my = padAxis(1);
        var rx = pad.axes[2] || 0, ry = pad.axes[3] || 0, rm = Math.sqrt(rx * rx + ry * ry), dz = SET.dead / 100;
        if (rm >= dz) guestStickAt = performance.now();
        if (rm >= dz + 0.1) aim = Math.atan2(ry, rx);
        else if (performance.now() - guestStickAt < 600) aim = player.ang;   // keep it where it was
        var PB = [PAD.reload, PAD.drop, PAD.pickup, PAD.stim, PAD.swapL, PAD.swapR, PAD.melee, PAD.melee2, PAD.frag, PAD.smoke];
        for (i = 0; i < PB.length; i++) if (padHit(PB[i])) hitsNow |= 1 << PB[i];
        if (padHit(PAD.pause)) pause();
        if (padDown(PAD.sprint)) down |= 1 << PAD.sprint;
        if (padDown(7)) down |= 1 << 7;
      }
      if (!mx && !my) {
        if (keys['a']) mx -= 1; if (keys['d']) mx += 1;
        if (keys['w']) my -= 1; if (keys['s']) my += 1;
        var ml = Math.sqrt(mx * mx + my * my);
        if (ml > 1) { mx /= ml; my /= ml; }
      }
      if (aim === null && !padActive()) aim = Math.atan2(mouse.wy - player.y, mouse.wx - player.x);
      if (keys['shift']) down |= 1 << PAD.sprint;
      if (mouse.down) down |= 1 << 7;
      if ((down & (1 << 7)) && !guestTrig) hitsNow |= 1 << 7;
      guestTrig = !!(down & (1 << 7));
    } else if (pad && padHit(9)) resume();
    if (aim === null) aim = player.ang;
    netInT -= dt;
    var pkt = { t: 'in', ax: [mx, my], aim: aim, down: down, hits: hitsNow };
    var key = mx.toFixed(2) + my.toFixed(2) + aim.toFixed(2) + down;
    if (hitsNow || key !== netLastIn || netInT <= 0) {
      netSend(pkt);
      netLastIn = key; netInT = 0.1;
    }
  }

  // ---- the ONLINE screen ----
  function openOnline() {
    elMenu.hidden = true;
    $('online').hidden = false;
    partyRender();
    if (typeof renderFriends === 'function') renderFriends();
    if (!netRole) netStatus('One of you hosts, the other joins with the code. Works best on a normal home connection.');
  }
  $('onlineBtn').addEventListener('click', openOnline);
  $('netHost').addEventListener('click', function () { hostGame(); });
  $('netJoin').addEventListener('click', function () { joinGame($('netJoinCode').value); });
  $('netJoinCode').addEventListener('keydown', function (ev) {
    ev.stopPropagation();
    if (ev.key === 'Enter') joinGame(this.value);
  });
  $('netBack').addEventListener('click', function () { $('online').hidden = true; elMenu.hidden = false; syncMenu(); });
  $('netLeave').addEventListener('click', function () { netClose('Disconnected.'); });

  // ---------------------------------------------------------------- crazygames
  var cgSet = { disableChat: false, muteAudio: false };
  function cgCall(fn) { if (!CG) return; try { fn(CG); } catch (err) {} }
  var cgPlaying = false;
  function cgGame(what) {
    // start/stop only on a real change - repeats are throttled and flagged
    if (what === 'gameplayStart') { if (cgPlaying) return; cgPlaying = true; }
    if (what === 'gameplayStop') { if (!cgPlaying) return; cgPlaying = false; }
    cgCall(function (c) { if (c.game && c.game[what]) c.game[what](); });
  }
  function cgNoChat() { return !!cgSet.disableChat; }
  function cgApply(st) {
    cgSet = st || cgSet;
    muted = !!cgSet.muteAudio;
    pchatVisible();
    if (cgNoChat() && $('igChat') && !$('igChat').hidden) $('igChat').hidden = true;
  }
  // tell CrazyGames which room we are in and whether friends can still come
  function cgRoom() {
    if (!CG) return;
    if (!netRole || !netCode) return;
    var joinable = netRole === 'host' && humansIn() < NET_MAX &&
                   ((state !== 'play' && state !== 'paused') || (typeof lobbyOpen === 'function' && lobbyOpen()));
    cgCall(function (c) {
      c.game.updateRoom({ roomId: netCode, isJoinable: joinable, inviteParams: { room: netCode } });
      // their QA still looks for the (deprecated) invite button: shown while
      // friends can join, hidden once the match is on or the room is full
      if (joinable && state !== 'play' && state !== 'paused') c.game.showInviteButton({ room: netCode });
      else c.game.hideInviteButton();
    });
    $('cgInviteBtn').hidden = !(netRole === 'host' && netCode);
  }
  function cgUser() {
    cgCall(function (c) {
      if (!c.user || !c.user.isUserAccountAvailable) return;
      c.user.getUser().then(function (u) {
        if (u && u.username) acctName = u.username;
        $('acctName').textContent = acctName;
        syncMenu();
      }).catch(function () {});
    });
  }
  // a link friends can open straight into your party
  $('cgInviteBtn').addEventListener('click', function () {
    if (!CG || !netCode) return;
    // their docs say this returns a promise; the SDK itself returns the string - take either
    var got;
    try { got = CG.game.inviteLink({ room: netCode }); } catch (err) { netStatus('Could not make an invite link.'); return; }
    Promise.resolve(got).then(function (link) {
      var done = function () { netStatus('Invite link copied - paste it to your friends.'); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(link).then(done, function () { netStatus(link); });
      else netStatus(link);
    }).catch(function () { netStatus('Could not make an invite link.'); });
  });
  function cgInit() {
    if (!CG_MODE) return;
    // no accounts, friends or friend chat of our own on CrazyGames
    acctName = 'GUEST' + (1000 + rnd(9000));
    $('acctBtn').hidden = true;
    $('friendsBtn').hidden = true;
    $('acctName').textContent = acctName;
    var sdk = window.CrazyGames && window.CrazyGames.SDK;
    if (!sdk) { cgLand(); return; }                        // blocked (ad blocker): play on regardless
    sdk.init().then(function () {
      CG = sdk;
      // bring anything saved before the SDK was ready into their storage
      ['earshot.wallet', 'earshot.settings', 'earshot.tutDone'].forEach(function (k) {
        try { if (CG.data.getItem(k) === null) { var v = localStorage.getItem(k); if (v !== null) CG.data.setItem(k, v); } } catch (err) {}
      });
      loadWallet(); loadSettings(); refreshCoins(); syncTutBtn();
      cgApply(CG.game.settings);
      CG.game.addSettingsChangeListener(cgApply);
      cgUser();
      CG.user.addAuthListener(function () { cgUser(); loadWallet(); refreshCoins(); });
      // someone clicked a friend's invite while already playing
      CG.game.addJoinRoomListener(function (p) {
        if (!p || !p.room) return;
        if (state === 'play' || state === 'paused') leaveMatch();
        openOnline(); joinGame(p.room, false);
      });
      var inv = CG.game.inviteParams;
      if (inv && inv.room) { openOnline(); joinGame(inv.room, false); return; }
      if (CG.game.isInstantMultiplayer) { openOnline(); hostGame(); return; }
      cgLand();
    }).catch(function () { cgLand(); });
  }
  // New players land straight in the action: the tutorial the first time,
  // the menu after that.
  function cgLand() {
    if (storeGet('earshot.tutDone') !== '1' && state === 'menu') $('tutBtn').click();
  }

  // ---------------------------------------------------------------- accounts
  // Firebase is only an address book here: who you are, who your friends are,
  // which public matches are open. The matches themselves still run peer to
  // peer on the host's machine.
  var FB_VER = '10.14.1';
  var FB_CFG = {
    apiKey: 'AIzaSyCTCjH9-4Trrz1BIZa3wZcue6x_89GMUSk',
    authDomain: 'dead-angle-f314f.firebaseapp.com',
    projectId: 'dead-angle-f314f',
    storageBucket: 'dead-angle-f314f.firebasestorage.app',
    messagingSenderId: '382280525012',
    appId: '1:382280525012:web:968327ff5739d7135cc741'
  };
  // usernames become a made-up address - nobody needs a real email to play
  var EMAIL_DOM = '@players.dead-angle.game';
  var fbReady = false, fbLoading = null, fbAuth = null, fbDb = null, fbUser = null;
  var fbFriends = [], fbInvUnsub = null, fbBeatT = null, fbWalletT = null, fbProfileTries = 0;

  function friendStatus(t) { var el = $('friendStatus'); if (el) el.textContent = t; }
  function openFriends() {
    ['menu', 'online'].forEach(function (id) { $(id).hidden = true; });
    $('friends').hidden = false;
    renderAcct();
    renderFriends();
  }
  function acctStatus(t) { var el = $('acctStatus'); if (el) el.textContent = t; }
  function quickStatus(t) { netStatus(t); var el = $('quickStatus'); if (el) { el.textContent = t; el.hidden = !t; } }

  function loadFirebase(cb) {
    if (fbReady) { cb(); return; }
    if (fbLoading) { fbLoading.push(cb); return; }
    fbLoading = [cb];
    var files = ['firebase-app-compat.js', 'firebase-auth-compat.js', 'firebase-firestore-compat.js'], k = 0;
    (function next() {
      if (k >= files.length) {
        try {
          if (!firebase.apps.length) firebase.initializeApp(FB_CFG);
          fbAuth = firebase.auth(); fbDb = firebase.firestore();
          fbAuth.onAuthStateChanged(onAuth);
          fbReady = true;
        } catch (err) { acctStatus('The account service did not start.'); fbLoading = null; return; }
        var q = fbLoading; fbLoading = null;
        q.forEach(function (f) { f(); });
        return;
      }
      var sc = document.createElement('script');
      sc.src = 'https://cdn.jsdelivr.net/npm/firebase@' + FB_VER + '/' + files[k++];
      sc.onload = next;
      sc.onerror = function () { acctStatus('Could not reach the account service.'); fbLoading = null; };
      document.head.appendChild(sc);
    })();
  }

  function errText(err) {
    var c = (err && err.code) || '';
    if (c === 'taken' || c === 'auth/email-already-in-use') return 'That username is taken.';
    if (c === 'auth/invalid-credential' || c === 'auth/wrong-password' || c === 'auth/user-not-found' || c === 'auth/invalid-login-credentials')
      return 'Wrong username or password.';
    if (c === 'auth/too-many-requests') return 'Too many tries - wait a minute.';
    if (c === 'auth/network-request-failed' || c === 'unavailable') return 'No connection to the account service.';
    if (c === 'auth/operation-not-allowed') return 'Username sign-in is not switched on in Firebase yet (Email/Password).';
    if (c === 'permission-denied') return 'The game database is not set up yet (Firestore rules).';
    if (c === 'auth/admin-restricted-operation') return 'Quick Play needs Anonymous sign-in switched on in Firebase.';
    if (c === 'auth/weak-password') return 'Pick a longer password (6+ characters).';
    return (err && err.message) || 'Something went wrong.';
  }
  function readCreds() {
    var nm = $('acctUser').value.trim(), pw = $('acctPass').value;
    if (!/^[A-Za-z0-9_]{3,16}$/.test(nm)) { acctStatus('Usernames are 3-16 letters, numbers or _.'); return null; }
    if (rude(nm)) { acctStatus('Pick a different username.'); return null; }
    if (pw.length < 6) { acctStatus('Passwords need at least 6 characters.'); return null; }
    return { name: nm, lower: nm.toLowerCase(), pass: pw };
  }

  function signUp() {
    var c = readCreds(); if (!c) return;
    acctStatus('Creating your account...');
    loadFirebase(function () {
      fbDb.collection('usernames').doc(c.lower).get().then(function (d) {
        if (d.exists) throw { code: 'taken' };
        return fbAuth.createUserWithEmailAndPassword(c.lower + EMAIL_DOM, c.pass);
      }).then(function (cred) {
        var uid = cred.user.uid;
        return fbDb.collection('usernames').doc(c.lower).set({ uid: uid, name: c.name }).then(function () {
          return fbDb.collection('users').doc(uid).set({
            name: c.name, nameLower: c.lower, friends: [],
            coins: WALLET.coins, owned: WALLET.owned, skin: WALLET.skin,
            lastSeen: Date.now(), party: '', partyHost: false
          });
        }).catch(function (err) {
          // the name got taken in the same moment: undo the half-made account
          return cred.user.delete().then(function () { throw err; }, function () { throw err; });
        });
      }).then(function () {
        acctStatus('Welcome, ' + c.name + '!');
        fbProfileTries = 0; onAuth(fbAuth.currentUser);
        setTimeout(closeAccount, 700);
      }).catch(function (err) { acctStatus(errText(err)); });
    });
  }
  function logIn() {
    var c = readCreds(); if (!c) return;
    acctStatus('Logging in...');
    loadFirebase(function () {
      fbAuth.signInWithEmailAndPassword(c.lower + EMAIL_DOM, c.pass)
        .then(function () { acctStatus(''); closeAccount(); })
        .catch(function (err) { acctStatus(errText(err)); });
    });
  }
  function logOut() {
    if (netRole) netClose('Logged out.');
    if (fbAuth) fbAuth.signOut();
  }

  function onAuth(user) {
    if (CG_MODE) { fbUser = user || null; return; }
    fbUser = user || null;
    if (fbInvUnsub) { fbInvUnsub(); fbInvUnsub = null; }
    if (fbBeatT) { clearInterval(fbBeatT); fbBeatT = null; }
    if (!user) { acctName = ''; fbFriends = []; renderAcct(); renderFriends(); return; }
    fbDb.collection('users').doc(user.uid).get().then(function (d) {
      if (!d.exists) {
        // a brand-new account can arrive here a moment before its profile
        if (fbProfileTries++ < 4) setTimeout(function () { if (fbUser === user) onAuth(user); }, 1200);
        return;
      }
      var p = d.data();
      acctName = p.name || '';
      fbFriends = p.friends || [];
      // the account's coins and skins win; skins owned on this machine are kept
      if (typeof p.coins === 'number') {
        var owned = (p.owned || []).slice();
        WALLET.owned.forEach(function (k) { if (owned.indexOf(k) < 0) owned.push(k); });
        WALLET = { coins: p.coins, owned: owned.length ? owned : WALLET.owned, skin: (p.skin | 0) };
        if (WALLET.owned.indexOf(WALLET.skin) < 0) WALLET.skin = WALLET.owned[0];
        try { localStorage.setItem('earshot.wallet', JSON.stringify(WALLET)); } catch (err) {}
        refreshCoins();
      }
      renderAcct();
      heartbeat();
      fbBeatT = setInterval(heartbeat, 30000);
      listenInvites();
      renderFriends();
      primeFriends();
    }).catch(function (err) { acctStatus(errText(err)); renderAcct(); });
  }

  var cloudWallet = function () {
    if (!fbUser || !fbDb) return;
    clearTimeout(fbWalletT);
    fbWalletT = setTimeout(function () {
      if (!fbUser) return;
      fbDb.collection('users').doc(fbUser.uid).update({ coins: WALLET.coins, owned: WALLET.owned, skin: WALLET.skin }).catch(function () {});
    }, 1500);
  };
  function heartbeat() {
    if (!fbUser) return;
    fbDb.collection('users').doc(fbUser.uid).update({
      lastSeen: Date.now(), party: netRole ? netCode : '', partyHost: netRole === 'host'
    }).catch(function () {});
  }

  function renderAcct() {
    var on = !!(fbUser && acctName);
    $('acctName').textContent = on ? acctName : 'NOT LOGGED IN';
    $('acctBtn').textContent = on ? 'LOG OUT' : 'LOG IN';
    $('friendsBox').hidden = !on;
    $('friendsNeed').hidden = on;
  }
  function openAccount(msg) {
    ['menu', 'online', 'friends'].forEach(function (id) { $(id).hidden = true; });
    $('account').hidden = false;
    acctStatus(msg || '');
    loadFirebase(function () {});
  }
  function closeAccount() { $('account').hidden = true; elMenu.hidden = false; syncMenu(); }

  // ---- friends ----
  function addFriend() {
    var nm = $('friendName').value.trim().toLowerCase();
    if (!fbUser) { openAccount('Log in to add friends.'); return; }
    if (!/^[a-z0-9_]{3,16}$/.test(nm)) { friendStatus('Type their username.'); return; }
    fbDb.collection('usernames').doc(nm).get().then(function (d) {
      if (!d.exists) { friendStatus('Nobody is called ' + nm + '.'); return; }
      var uid = d.data().uid;
      if (uid === fbUser.uid) { friendStatus('That is you!'); return; }
      if (fbFriends.indexOf(uid) >= 0) { friendStatus('Already on your list.'); return; }
      return fbDb.collection('users').doc(fbUser.uid).update({ friends: firebase.firestore.FieldValue.arrayUnion(uid) }).then(function () {
        fbFriends.push(uid);
        $('friendName').value = '';
        friendStatus('Added ' + d.data().name + '.');
        renderFriends();
      });
    }).catch(function (err) { friendStatus(errText(err)); });
  }
  function removeFriend(uid) {
    fbDb.collection('users').doc(fbUser.uid).update({ friends: firebase.firestore.FieldValue.arrayRemove(uid) }).then(function () {
      fbFriends = fbFriends.filter(function (u) { return u !== uid; });
      renderFriends();
    }).catch(function (err) { netStatus(errText(err)); });
  }
  var friendsT = null;
  function renderFriends() {
    var el = $('friendList');
    if (!el) return;
    if (!fbUser || !fbFriends.length) {
      el.innerHTML = fbUser ? '<div class="fempty">No friends yet - add one by username.</div>' : '';
      return;
    }
    Promise.all(fbFriends.map(function (uid) {
      return fbDb.collection('users').doc(uid).get().then(function (d) { var v = d.exists ? d.data() : null; if (v) v.uid = uid; return v; }, function () { return null; });
    })).then(function (list) {
      fbFriendDocs = list.filter(Boolean);
      el.innerHTML = '';
      var now = Date.now();
      list.filter(Boolean).sort(function (a, b) { return (b.lastSeen || 0) - (a.lastSeen || 0); }).forEach(function (f) {
        var online = now - (f.lastSeen || 0) < 75000;
        var row = document.createElement('div');
        row.className = 'frow' + (online ? ' on' : '');
        var nm = document.createElement('span');
        nm.className = 'fname';
        nm.textContent = f.name;
        var st = document.createElement('em');
        st.textContent = online ? (f.party ? (f.partyHost ? 'HOSTING A PARTY' : 'IN A PARTY') : 'ONLINE') : 'OFFLINE';
        row.appendChild(nm); row.appendChild(st);
        // chat, only once you have added each other
        if ((f.friends || []).indexOf(fbUser.uid) >= 0) {
          var cb = document.createElement('button');
          cb.className = 'tgl' + (chatUnread[f.uid] ? ' on' : ''); cb.type = 'button';
          cb.textContent = chatUnread[f.uid] ? 'CHAT \u2022 NEW' : 'CHAT';
          cb.addEventListener('click', function () { openChat(f); });
          row.appendChild(cb);
        } else {
          var hint = document.createElement('em');
          hint.className = 'fhint'; hint.textContent = 'ADD EACH OTHER TO CHAT';
          row.appendChild(hint);
        }
        if (online && f.partyHost && f.party && f.party !== netCode) {
          var jb = document.createElement('button');
          jb.className = 'tgl on'; jb.type = 'button'; jb.textContent = 'JOIN';
          jb.addEventListener('click', function () { $('friends').hidden = true; openOnline(); joinGame(f.party, false); });
          row.appendChild(jb);
        }
        if (online) {
          var ib = document.createElement('button');
          ib.className = 'tgl'; ib.type = 'button'; ib.textContent = 'INVITE';
          ib.addEventListener('click', function () { invite(f); });
          row.appendChild(ib);
        }
        var rb = document.createElement('button');
        rb.className = 'tgl'; rb.type = 'button'; rb.textContent = '\u2715'; rb.title = 'Remove friend';
        rb.addEventListener('click', function () { removeFriend(f.uid); });
        row.appendChild(rb);
        el.appendChild(row);
      });
    });
  }

  // ---- chat ----
  // A plain word filter. It will not catch everything, but it keeps the
  // obvious stuff out of names and messages.
  var RUDE = ['fuck', 'shit', 'bitch', 'cunt', 'dick', 'pussy', 'cock', 'whore', 'slut', 'bastard',
              'asshole', 'nigg', 'fag', 'retard', 'rape', 'nazi', 'kys', 'penis', 'vagina', 'porn', 'sex'];
  function squash(t) {
    return String(t).toLowerCase().replace(/[@4]/g, 'a').replace(/3/g, 'e').replace(/[1!|]/g, 'i')
      .replace(/0/g, 'o').replace(/[5$]/g, 's').replace(/7/g, 't').replace(/[^a-z]/g, '');
  }
  function rude(t) {
    var q = squash(t);
    for (var i = 0; i < RUDE.length; i++) if (q.indexOf(RUDE[i]) >= 0) return true;
    return false;
  }
  function clean(t) {
    return String(t).split(/(\s+)/).map(function (w) { return rude(w) ? w.replace(/[^\s]/g, '*') : w; }).join('');
  }

  var fbFriendDocs = [], chatWith = null, chatUnsub = null, chatUnread = {};
  function pairId(a, b) { return a < b ? a + '_' + b : b + '_' + a; }
  function chatSeen(uid, at) {
    try {
      var m = JSON.parse(localStorage.getItem('earshot.chatSeen') || '{}');
      if (at === undefined) return m[uid] || 0;
      m[uid] = at; localStorage.setItem('earshot.chatSeen', JSON.stringify(m));
    } catch (err) {}
    return 0;
  }
  function openChat(f) {
    if (!fbUser) return;
    chatWith = f;
    ['friends', 'menu'].forEach(function (id) { $(id).hidden = true; });
    $('chat').hidden = false;
    $('chatName').textContent = f.name;
    $('chatLog').innerHTML = '<div class="cmsg sys">Loading...</div>';
    $('chatStatus').textContent = '';
    if (chatUnsub) chatUnsub();
    chatUnsub = fbDb.collection('chats').doc(pairId(fbUser.uid, f.uid)).collection('msgs')
      .orderBy('at', 'desc').limit(60).onSnapshot(function (qs) {
        var msgs = [];
        qs.forEach(function (d) { msgs.push(d.data()); });
        msgs.reverse();
        var log = $('chatLog');
        log.innerHTML = '';
        if (!msgs.length) log.innerHTML = '<div class="cmsg sys">No messages yet. Say hi!</div>';
        msgs.forEach(function (m) {
          var d = document.createElement('div');
          d.className = 'cmsg' + (m.from === fbUser.uid ? ' me' : '');
          var who = document.createElement('b');
          who.textContent = m.from === fbUser.uid ? acctName : f.name;
          var tx = document.createElement('span');
          tx.textContent = clean(m.text || '');
          d.appendChild(who); d.appendChild(tx);
          log.appendChild(d);
        });
        log.scrollTop = log.scrollHeight;
        if (msgs.length) chatSeen(f.uid, msgs[msgs.length - 1].at || Date.now());
        chatUnread[f.uid] = false;
        syncChatBadge();
      }, function (err) { $('chatStatus').textContent = errText(err); });
  }
  function closeChat() {
    if (chatUnsub) { chatUnsub(); chatUnsub = null; }
    chatWith = null;
    $('chat').hidden = true;
    $('friends').hidden = false;
    renderFriends();
  }
  function sendChat() {
    var inp = $('chatInput'), text = inp.value.trim();
    if (!text || !chatWith || !fbUser) return;
    if (text.length > 200) text = text.slice(0, 200);
    inp.value = '';
    fbDb.collection('chats').doc(pairId(fbUser.uid, chatWith.uid)).collection('msgs').add({
      from: fbUser.uid, text: clean(text), at: Date.now()
    }).catch(function (err) {
      $('chatStatus').textContent = err && err.code === 'permission-denied'
        ? 'You can only chat once you have both added each other.' : errText(err);
    });
  }
  // a gentle "new message" mark on the FRIENDS button
  function syncChatBadge() {
    var any = false;
    for (var k in chatUnread) if (chatUnread[k]) any = true;
    var b = $('friendsBtn');
    if (b) b.textContent = any ? 'FRIENDS \u2022 NEW MESSAGE' : 'FRIENDS';
  }
  function checkUnread() {
    if (!fbUser || !fbDb || state === 'play') return;
    var mutual = fbFriendDocs.filter(function (f) { return (f.friends || []).indexOf(fbUser.uid) >= 0; });
    mutual.forEach(function (f) {
      if (chatWith && chatWith.uid === f.uid) return;
      fbDb.collection('chats').doc(pairId(fbUser.uid, f.uid)).collection('msgs').orderBy('at', 'desc').limit(1).get()
        .then(function (qs) {
          var last = null;
          qs.forEach(function (d) { last = d.data(); });
          chatUnread[f.uid] = !!(last && last.from !== fbUser.uid && (last.at || 0) > chatSeen(f.uid));
          syncChatBadge();
        }, function () {});
    });
  }
  setInterval(checkUnread, 30000);
  // after logging in, learn who your friends are so the badge can work
  function primeFriends() {
    if (!fbUser || !fbFriends.length) return;
    Promise.all(fbFriends.map(function (uid) {
      return fbDb.collection('users').doc(uid).get().then(function (d) { var v = d.exists ? d.data() : null; if (v) v.uid = uid; return v; }, function () { return null; });
    })).then(function (list) { fbFriendDocs = list.filter(Boolean); checkUnread(); });
  }

  // ---- invites ----
  function invite(f) {
    if (netRole === 'guest') { netStatus('Only the party leader can invite.'); return; }
    hostGame(function () {
      fbDb.collection('invites').doc(f.uid).collection('items').add({
        from: fbUser.uid, fromName: acctName, code: netCode, at: Date.now()
      }).then(function () { friendStatus('Invite sent to ' + f.name + '. You are hosting - they join your party.'); heartbeat(); })
        .catch(function (err) { netStatus(errText(err)); });
    });
  }
  var shownInvite = null;
  function listenInvites() {
    if (!fbUser) return;
    fbInvUnsub = fbDb.collection('invites').doc(fbUser.uid).collection('items').onSnapshot(function (qs) {
      var now = Date.now(), best = null;
      qs.forEach(function (d) {
        var v = d.data();
        if (now - (v.at || 0) > 180000) { d.ref.delete().catch(function () {}); return; }
        if (!best || v.at > best.v.at) best = { ref: d.ref, v: v };
      });
      if (!best) { $('inviteToast').hidden = true; shownInvite = null; return; }
      shownInvite = best;
      $('inviteText').textContent = best.v.fromName + ' invited you to their party';
      $('inviteToast').hidden = state === 'play';
    }, function () {});
  }
  function answerInvite(yes) {
    var inv = shownInvite;
    $('inviteToast').hidden = true;
    shownInvite = null;
    if (!inv) return;
    inv.ref.delete().catch(function () {});
    if (yes) { if (netGuest || state === 'play') leaveMatch(); openOnline(); joinGame(inv.v.code, false); }
  }

  // ---- quick play ----
  function quickPlay() {
    if (CG_MODE && !fbUser) {
      openOnline();
      quickStatus('Connecting...');
      loadFirebase(function () {
        if (fbAuth.currentUser) { fbUser = fbAuth.currentUser; quickPlay(); return; }
        fbAuth.signInAnonymously().then(function (c) { fbUser = c.user; quickPlay(); })
          .catch(function (err) { quickStatus(errText(err)); });
      });
      return;
    }
    if (!CG_MODE && (!fbUser || !acctName)) { openAccount('Log in to play online.'); return; }
    if (netRole === 'guest') { openOnline(); netStatus('You are in a party - the leader starts the match.'); return; }
    initAudio();
    if (netRole === 'host' && netGuests.length) { goPublicHost(); return; }
    if (netRole) netClose('');
    openOnline();
    quickStatus('Finding a ' + MODE_LABEL[mode].toLowerCase() + ' match...');
    fbDb.collection('lobbies').where('mode', '==', mode).where('open', '==', true).limit(25).get().then(function (qs) {
      var now = Date.now(), list = [];
      qs.forEach(function (d) {
        var L = d.data();
        if (now - (L.updated || 0) < 30000 && L.humans < L.max && L.map === mapKind && L.host !== fbUser.uid) list.push(L);
      });
      list.sort(function (a, b) { return ((b.wait ? 1 : 0) - (a.wait ? 1 : 0)) || (b.humans - a.humans); });
      tryLobby(list, 0);
    }).catch(function () { goPublicHost(); });
  }
  function tryLobby(list, i) {
    if (i >= list.length) { goPublicHost(); return; }
    quickStatus('Joining ' + (list[i].name || 'a match') + '...');
    quickFail = function () { quickFail = null; tryLobby(list, i + 1); };
    joinGame(list[i].code, true, function () { var f = quickFail; quickFail = null; if (f) f(); });
  }
  // nobody to join: open our own public match, which others will find
  // Open a public lobby and hold it: the match starts when it is full, or
  // after 20 seconds with bots in the empty seats.
  var QUEUE_TIME = 20, queueOn = false, queueT = 0, queueSay = 0;
  function queueCap() { return Math.min(NET_MAX, MODES[mode].field); }
  function goPublicHost() {
    hostGame(function () {
      netPublic = true;
      queueOn = true; queueT = QUEUE_TIME; queueSay = 0;
      openOnline();
      lobbyWrite();
    });
  }
  function queueTick(dt) {
    if (!queueOn || netRole !== 'host') { queueOn = false; return; }
    queueT -= dt; queueSay -= dt;
    var n = humansIn(), cap = queueCap();
    if (queueSay <= 0) {
      queueSay = 0.5;
      var msg = 'Waiting for players ' + n + '/' + cap + ' \u00b7 starting in ' + Math.max(0, Math.ceil(queueT)) + 's - bots fill any empty seats';
      quickStatus(msg);
      netSendAll({ t: 'queue', msg: msg });
    }
    if (n >= cap || queueT <= 0) {
      queueOn = false;
      quickStatus('');
      startMatch();
    }
  }
  var lobbyT = 0;
  function lobbyOpen() {
    if (queueOn) return humansIn() < queueCap();
    if (state !== 'play' && state !== 'paused') return false;
    if (humansIn() >= Math.min(NET_MAX, fieldN)) return false;
    if (mode === 'br') return !!plane && plane.t < plane.dur * 0.75;   // only while there are seats on the plane
    return true;
  }
  function lobbyWrite() {
    if (!fbDb || !fbUser || !netCode || !netPublic) return;
    fbDb.collection('lobbies').doc(netCode).set({
      host: fbUser.uid, name: acctName, code: netCode, mode: mode, map: mapKind,
      humans: humansIn(), max: queueCap(), open: lobbyOpen(), wait: queueOn, updated: Date.now()
    }).catch(function () {});
  }
  lobbyTouch = function () { if (netPublic) { lobbyT = 0.2; } };
  lobbyTick = function (dt) {
    if (!netPublic) return;
    lobbyT -= dt;
    if (lobbyT <= 0) { lobbyT = 8; lobbyWrite(); }
  };
  lobbyDrop = function () {
    if (fbDb && fbUser && netCode) fbDb.collection('lobbies').doc(netCode).delete().catch(function () {});
  };
  window.addEventListener('beforeunload', function () { if (netPublic) lobbyDrop(); });

  // ---- wiring ----
  $('acctBtn').addEventListener('click', function () { if (fbUser && acctName) logOut(); else openAccount(''); });
  $('acctLogin').addEventListener('click', logIn);
  $('acctSignup').addEventListener('click', signUp);
  $('acctBack').addEventListener('click', closeAccount);
  $('quickBtn').addEventListener('click', quickPlay);
  $('friendAdd').addEventListener('click', addFriend);
  $('chatSend').addEventListener('click', sendChat);
  $('chatBack').addEventListener('click', closeChat);
  $('chatInput').addEventListener('keydown', function (ev) {
    ev.stopPropagation();
    if (ev.key === 'Enter') sendChat();
  });
  $('friendsBtn').addEventListener('click', openFriends);
  $('friendsBack').addEventListener('click', function () { $('friends').hidden = true; elMenu.hidden = false; syncMenu(); });
  $('friendsNeed').addEventListener('click', function () { openAccount(''); });
  $('inviteJoin').addEventListener('click', function () { answerInvite(true); });
  $('inviteNo').addEventListener('click', function () { answerInvite(false); });
  ['acctUser', 'acctPass', 'friendName'].forEach(function (id) {
    $(id).addEventListener('keydown', function (ev) {
      ev.stopPropagation();
      if (ev.key !== 'Enter') return;
      if (id === 'friendName') addFriend(); else logIn();
    });
  });
  // the friends list keeps itself fresh while you are looking at it
  setInterval(function () { if (!$('friends').hidden && fbUser) renderFriends(); }, 15000);
  if (!CG_MODE) loadFirebase(function () {});

  // ---------------------------------------------------------------- loop
  var last = performance.now();
  function frame(now) {
    var dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (state === 'play') {
      if (netGuest) guestTick(Math.max(dt, 0.0001));
      else update(Math.max(dt, 0.0001));
      if (netGuest && netGuestPaused) uiPad(dt);
    }
    else uiPad(dt);
    if (netRole === 'host') netHostTick(dt);
    musicTick();
    render();
    requestAnimationFrame(frame);
  }

  resize();
  buildTextures();
  loadWallet();
  loadSettings();
  refreshCoins();
  syncMenu();
  syncTutBtn();
  cgInit();
  requestAnimationFrame(frame);
})();
