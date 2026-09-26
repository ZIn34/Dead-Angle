# -*- coding: utf-8 -*-
"""Make the sources encoding-proof: escapes inside code, plain ASCII in prose."""
import io, sys

PLAIN = {u'—': '-', u'–': '-', u'·': '.', u'…': '...',
         u'∞': 'inf', u'’': "'", u'“': '"', u'”': '"'}

path = sys.argv[1]
s = io.open(path, encoding='utf-8').read()
out, changed = [], 0
in_block = False
for line in s.split('\n'):
    stripped = line.lstrip()
    is_comment = in_block or stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('/*')
    if '/*' in line and '*/' not in line:
        in_block = True
    if '*/' in line:
        in_block = False
    if any(ord(c) > 127 for c in line):
        changed += 1
        if is_comment:
            line = ''.join(PLAIN.get(c, c if ord(c) < 128 else '?') for c in line)
        else:
            line = ''.join(c if ord(c) < 128 else '\\u%04x' % ord(c) for c in line)
    out.append(line)

io.open(path, 'w', encoding='ascii').write('\n'.join(out))
print('%s: rewrote %d lines, now pure ASCII' % (path, changed))
