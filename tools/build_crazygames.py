# -*- coding: utf-8 -*-
"""Build the CrazyGames upload: dist/crazygames/ and dist/dead-angle-crazygames.zip.

Same game code as the GitHub build. The page just switches on CrazyGames mode
and loads their SDK first. Only files the game actually uses are packed.
Run:  python tools/build_crazygames.py
"""
import io, os, re, shutil, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'dist', 'crazygames')
ZIP = os.path.join(ROOT, 'dist', 'dead-angle-crazygames.zip')

html = io.open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
game = io.open(os.path.join(ROOT, 'game.js'), encoding='utf-8').read()

tag = '<script src="game.js"></script>'
if tag not in html:
    raise SystemExit('could not find the game.js script tag in index.html')
html = html.replace(tag,
    '<script>window.DEAD_ANGLE_PLATFORM = "crazygames";</script>\n'
    '<script src="https://sdk.crazygames.com/crazygames-sdk-v3.js"></script>\n' + tag, 1)

# every asset either file mentions, and nothing else
used = sorted(set(re.findall(r'assets/[A-Za-z0-9_./-]+\.(?:png|js|mp3|json)', html + game)))

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(os.path.join(OUT, 'assets'))
io.open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='').write(html)
shutil.copy2(os.path.join(ROOT, 'game.js'), os.path.join(OUT, 'game.js'))
for rel in used:
    src = os.path.join(ROOT, rel)
    if not os.path.isfile(src):
        raise SystemExit('missing asset: ' + rel)
    shutil.copy2(src, os.path.join(OUT, rel))

if os.path.exists(ZIP):
    os.remove(ZIP)
with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
    for base, dirs, files in os.walk(OUT):
        for f in files:
            full = os.path.join(base, f)
            z.write(full, os.path.relpath(full, OUT).replace('\\', '/'))

total = sum(os.path.getsize(os.path.join(b, f)) for b, d, fs in os.walk(OUT) for f in fs)
print('files:', 2 + len(used), '| unpacked %.1f MB | zip %.1f MB' % (total / 1e6, os.path.getsize(ZIP) / 1e6))
print('zip:', ZIP)
