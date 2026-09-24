# -*- coding: utf-8 -*-
"""Context-B cross-fit half of bayes_audit.py, run on its own (the fake_data half is in
bayes_audit.py; its log is experiments/logs/bayes_audit.log)."""
import io
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_BA = io.open(HERE/"bayes_audit.py", encoding="utf-8").read()
exec(SRC_BA[:SRC_BA.index("MARG = ")])
MARG = (-1.0, 0.0, 1.0, 2.0, 3.0)

def ho_cond(R, margin):
    """Noise-conditioned rules: key (signature, current label) -> {label: wlb}."""
    def f(d, cur, S):
        out = []
        for i, s in enumerate(S):
            p = cur[i]; keep = 0.0; best = None
            for x in set(s):
                t = R.get((x, p))
                if not t: continue
                keep = max(keep, t[p])
                for r, w in t.items():
                    if r != p and (best is None or w > best[1]): best = (r, w)
            if best and best[1] > keep + margin: out.append((i, best[0]))
        return out
    return f

exec(SRC_BA[SRC_BA.index("# ================================================================ B: cross-fit on valid"):])
