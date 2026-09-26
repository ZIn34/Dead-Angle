# -*- coding: utf-8 -*-
"""Pack chosen clips into a base64 JS file.

Embedding avoids fetching anything at runtime, which keeps the game working
inside the artifact sandbox where outbound requests are blocked.
"""
import os, sys, base64, json, subprocess
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = 'assets/sfx-data.js'

# name -> clip file. Add gun entries here once the reel is labelled.
CLIPS = {
    'frag':  'sfx/nade_01.wav',
    'smoke': 'sfx/nade_00.wav',
}
for a in sys.argv[1:]:
    if '=' in a:
        k, v = a.split('=', 1)
        CLIPS[k] = v

os.makedirs('assets', exist_ok=True)
data, total = {}, 0
for name, path in sorted(CLIPS.items()):
    if not os.path.exists(path):
        print('  !! missing %s' % path)
        continue
    mp3 = 'sfx/_enc_%s.mp3' % name
    subprocess.check_call([FF, '-y', '-i', path, '-ac', '1', '-ar', '44100',
                           '-b:a', '96k', mp3],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    raw = open(mp3, 'rb').read()
    data[name] = base64.b64encode(raw).decode('ascii')
    total += len(raw)
    print('  %-8s %s -> %5.1f KB mp3' % (name, os.path.basename(path), len(raw) / 1024.0))

js = 'window.EARSHOT_SFX = ' + json.dumps(data, separators=(',', ':')) + ';\n'
open(OUT, 'w', encoding='ascii').write(js)
print('%s  %.1f KB audio, %.1f KB file' % (OUT, total / 1024.0, len(js) / 1024.0))
