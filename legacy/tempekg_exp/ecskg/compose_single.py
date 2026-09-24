"""Bao cao DIEU KIEN DON — kiem tra con tautology sot khong, va cho moc de so voi hop thanh."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as M

for K in (2, 3):
    rows = [r for r in M.EV if r['k'] == K]
    base = sum(r['y'] for r in rows)/len(rows)
    print()
    print('='*80)
    print('TANG k=%d (%d event, nen %.1f%%) — DIEU KIEN DON' % (K, len(rows), 100*base))
    print('='*80)
    C = M.gen_conditions(rows)
    out = []
    for cd in C:
        s = M.score(rows, [cd], base)
        if s and s[2] >= 30:
            out.append((s[0]/base, s[1], s[2], cd))
    out.sort(reverse=True)
    print('  %-8s %-8s %-7s %s' % ('lift', 'conf', 'sup', 'dieu kien'))
    for lift, r, n, cd in out[:12]:
        print('  %6.2fx %6.1f%% %7d  %s:%s(%s=%s)' % (lift, 100*r, n, cd[0], cd[1], cd[2], cd[3]))
    print('  ... (%d dieu kien co sup>=30)' % len(out))
