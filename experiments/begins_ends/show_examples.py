# usage: python show_examples.py FILE SKIP N  -- compact view of an examples file
import re, io, sys
fn, skip, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
blocks = io.open(fn, encoding='utf-8').read().split('\n\n')[1:]
for b in blocks[skip:skip+n]:
    ls = b.strip().split('\n')
    if not ls or not ls[0]: continue
    print(re.sub(r'\| [^|]*?  A=', 'A=', ls[0]))
    for l in ls[1:]:
        l = l.strip(); i = min([x for x in (l.find('[A'), l.find('[B')) if x >= 0] or [0])
        print('     ', l[max(0, i-110):i+150])
