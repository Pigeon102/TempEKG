# -*- coding: utf-8 -*-
"""Task 5: noise-aware reasoning on MODEL-PREDICTED edges, not injected noise.

Every C3 number so far was measured on gold graphs with random corruption. That is a
convenient noise model and a dishonest one: random corruption spreads errors uniformly
and independently, while a classifier's errors cluster -- it gets whole event types
wrong, and it fails in the same direction every time (almost everything collapses to
BEFORE). Whether closure can audit a graph it did not build is the one untested risk.

This replaces corrupt() with the real thing: run the 257-rule classifier over valid,
build the graph from its predictions, and ask closure to find the edges it got wrong.

The comparison that matters is against injection at the same error rate. If closure
does much worse here, the injected-noise numbers were measuring the noise model.
"""
import sys, io, json, random
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from pathlib import Path

import vote as V
from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL
from noise_aware import compatible, one_step, score_document, FREQ_ORDER, corrupt

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 300

# ---------------------------------------------------------------- 1. classifier
rules = V.load_rules(ART / "rules_rx_c70.json")
print("%d rule" % len(rules), flush=True)

# load valid with document structure kept, so edges can be regrouped per document
def load_docs(path, limit):
    from mine_compositional import candidate_conditions, pair_features
    from mine_mdd import relational_conditions
    docs = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line)
        nodes = rec["nodes"]; anchors = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]: anchors[(p["a"], p["b"])].add((ra, rb))
        rows = []
        for e in rec["target_edges"]:
            a, b = e["s"], e["t"]
            na, nb = nodes.get(a), nodes.get(b)
            if not na or not nb or na["kind"] != "event" or nb["kind"] != "event": continue
            shared = anchors.get((a, b)) or anchors.get((b, a)) or set()
            f = pair_features(na, nb, shared, bool(shared), frozenset())
            cs = frozenset(list(candidate_conditions(f)) + relational_conditions(na, nb, shared))
            rows.append((a, b, e["rel"], f, cs))
        if rows: docs.append(rows)
    return docs

docs = load_docs(GRAPH / "valid.jsonl", LIMIT)
npair = sum(len(d) for d in docs)
print("%d document, %s cap" % (len(docs), format(npair, ",")), flush=True)

# predict
flat = [(f, cs) for d in docs for (_, _, _, f, cs) in d]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])
pos = 0
pred_docs = []
for d in docs:
    pd = []
    for (a, b, gold, f, cs) in d:
        h = V.firing(rules, idx, f, cs)
        lab = V.combine(rules, h, "max-norm", 5) or V.FALLBACK
        pd.append((a, b, gold, lab))
    pred_docs.append(pd)

gold_all = [g for d in pred_docs for (_, _, g, _) in d]
pred_all = [p for d in pred_docs for (_, _, _, p) in d]
wrong = sum(1 for g, p in zip(gold_all, pred_all) if g != p)
err_rate = wrong / len(gold_all)
m, per, acc = V.macro_f1(pred_all, gold_all)
print("classifier: acc %.2f%%  macro-F1 %.2f%%  -> %s canh sai (%.2f%%)"
      % (100*acc, 100*m, format(wrong, ","), 100*err_rate), flush=True)

# what the errors look like, versus what random corruption looks like
cm = Counter((g, p) for g, p in zip(gold_all, pred_all) if g != p)
print()
print("Nam kieu loi pho bien nhat cua model:")
for (g, p), c in cm.most_common(5):
    print("  %-14s -> %-14s %6s  (%.1f%% so loi)" % (g, p, format(c, ","), 100*c/wrong))

# ---------------------------------------------------------------- 2. audit
def audit(pred_docs, k_frac=3.0):
    ranked = []; n_bad = 0
    for pd in pred_docs:
        edges = [(a, b, lab) for (a, b, _, lab) in pd]
        bad = {(a, b): g for (a, b, g, lab) in pd if g != lab}
        n_bad += len(bad)
        for susp, a, b, carried, proposal in score_document(edges):
            ranked.append((susp, (a, b) in bad, bad.get((a, b)), proposal))
    ranked.sort(key=lambda t: -t[0])
    k = max(1, int(round(k_frac * n_bad))) if k_frac else len(ranked)
    top = ranked[:k]
    fb = sum(1 for _, is_bad, _, _ in top if is_bad)
    rp = sum(1 for _, is_bad, orig, prop in top if is_bad and prop == orig)
    return dict(n_bad=n_bad, ranked=len(ranked), k=len(top),
                p_at_k=fb/len(top) if top else 0.0,
                repair_at_k=rp/fb if fb else 0.0,
                r_all=rp/n_bad if n_bad else 0.0,
                found_all=fb/n_bad if n_bad else 0.0)

print()
print("=" * 90)
print("TASK 5 — audit tren canh MODEL DU DOAN (valid, %d doc)" % len(docs))
print("=" * 90)
r = audit(pred_docs)
print("  canh sai that      %s  (%.2f%% cua %s canh)"
      % (format(r["n_bad"], ","), 100*err_rate, format(npair, ",")))
print("  closure xep hang   %s canh  (%.1f%% -- con lai la abstain)"
      % (format(r["ranked"], ","), 100*r["ranked"]/npair))
print("  lay top-k          %s" % format(r["k"], ","))
print()
print("  P@k          %6.2f%%   trong so canh gan co, bao nhieu that su sai" % (100*r["p_at_k"]))
print("  found_all    %6.2f%%   trong toan bo canh sai, tim duoc bao nhieu" % (100*r["found_all"]))
print("  repair@k     %6.2f%%   trong so tim duoc, sua dung bao nhieu" % (100*r["repair_at_k"]))
print("  R_all        %6.2f%%   trong toan bo canh sai, vua tim VUA sua dung" % (100*r["r_all"]))

# ---------------------------------------------------------------- 3. so sanh
print()
print("=" * 90)
print("DOI CHUNG — nhieu NGAU NHIEN cung ty le (%.2f%%), cung document" % (100*err_rate))
print("=" * 90)
gold_docs = [[(a, b, g) for (a, b, g, _) in pd] for pd in pred_docs]
rng = random.Random(0)
# gold marginal, the same distribution noise_aware.py uses by default
gm = Counter(gold_all); tot = sum(gm.values())
marg = {k: v/tot for k, v in gm.items()}
ranked = []; n_bad = 0
for edges in gold_docs:
    cor, bad = corrupt(edges, err_rate, marg, rng)
    n_bad += len(bad)
    for susp, a, b, carried, proposal in score_document(cor):
        ranked.append((susp, (a, b) in bad, bad.get((a, b)), proposal))
ranked.sort(key=lambda t: -t[0])
k = max(1, int(round(3.0 * n_bad)))
top = ranked[:k]
fb = sum(1 for _, ib, _, _ in top if ib)
rp = sum(1 for _, ib, o, p in top if ib and p == o)
print("  canh hong          %s" % format(n_bad, ","))
print("  P@k          %6.2f%%" % (100*fb/len(top) if top else 0))
print("  found_all    %6.2f%%" % (100*fb/n_bad if n_bad else 0))
print("  repair@k     %6.2f%%" % (100*rp/fb if fb else 0))
print("  R_all        %6.2f%%" % (100*rp/n_bad if n_bad else 0))
print()
print("=" * 90)
print("  %-14s%>12s%>12s" % ("chi so", "model", "ngau nhien") if False else
      "  %-14s%12s%12s" % ("chi so", "model", "ngau nhien"))
print("  " + "-" * 38)
for nm, a_, b_ in (("P@k", r["p_at_k"], fb/len(top) if top else 0),
                   ("found_all", r["found_all"], fb/n_bad if n_bad else 0),
                   ("repair@k", r["repair_at_k"], rp/fb if fb else 0),
                   ("R_all", r["r_all"], rp/n_bad if n_bad else 0)):
    print("  %-14s%11.2f%%%11.2f%%" % (nm, 100*a_, 100*b_))
