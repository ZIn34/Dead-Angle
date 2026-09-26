# -*- coding: utf-8 -*-
"""Pull the audio out of the screen recording and find each effect in it."""
import os, sys, wave, array, subprocess
import imageio_ffmpeg

SRC = r"C:\Users\micha\Videos\Screen Recordings\Screen Recording 2026-09-17 191213.mp4"
FF = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs('sfx', exist_ok=True)
WAV = 'sfx/_all.wav'

if not os.path.exists(WAV) or '--force' in sys.argv:
    subprocess.check_call([FF, '-y', '-i', SRC, '-vn', '-ac', '1', '-ar', '44100',
                           '-acodec', 'pcm_s16le', WAV],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

w = wave.open(WAV, 'rb')
sr = w.getframerate()
n = w.getnframes()
raw = w.readframes(n)
w.close()
pcm = array.array('h')
pcm.frombytes(raw)
print('audio: %.2f s at %d Hz, %d samples' % (n / float(sr), sr, n))

# envelope in 5 ms blocks
BLK = int(sr * 0.005)
env = []
peak = 1
for i in range(0, len(pcm) - BLK, BLK):
    m = 0
    for j in range(i, i + BLK, 4):        # every 4th sample is plenty
        v = pcm[j]
        if v < 0: v = -v
        if v > m: m = v
    env.append(m)
    if m > peak: peak = m
print('peak amplitude %d' % peak)

thresh = max(peak * 0.06, 220)
GAP = int(0.11 / 0.005)                   # 110 ms of quiet separates effects
segs, start, quiet = [], None, 0
for i, v in enumerate(env):
    if v >= thresh:
        if start is None:
            start = i
        quiet = 0
    elif start is not None:
        quiet += 1
        if quiet >= GAP:
            segs.append((start, i - quiet))
            start = None
            quiet = 0
if start is not None:
    segs.append((start, len(env) - 1))

segs = [(a, b) for a, b in segs if (b - a) * 0.005 > 0.04]
print('found %d effects' % len(segs))
for k, (a, b) in enumerate(segs):
    pk = max(env[a:b + 1]) if b > a else 0
    print('  %2d  start %6.2fs  len %5.0f ms  peak %d'
          % (k, a * 0.005, (b - a) * 0.005 * 1000, pk))
