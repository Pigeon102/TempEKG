from pathlib import Path
from collections import Counter
from mine_views import VIEWS, load, mine_view
tr = load(Path('graph/train.jsonl'))
tot = 0
kept = Counter()
for name, fn in VIEWS.items():
    r = mine_view(tr, fn, 25, 1.5, 2, 220)
    for rule, s in r.items():
        if s[2] == 'BEFORE':
            continue
        tot += 1
        for f in (0.0, 0.2, 0.3, 0.4, 0.5):
            if s[0] >= f:
                kept[f] += 1
    print('  view', name, 'done', flush=True)
nb = (len(tr) + 7) // 8
print('rules after refusing BEFORE:', tot)
for f in sorted(kept):
    n = kept[f]
    print('  wlb>=%.1f  %7d rule  -> bytearray %5.1f GB' % (f, n, 2 * n * nb / 1e9))
