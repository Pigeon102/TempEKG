# -*- coding: utf-8 -*-
"""Prediction-preserving rule-set compression, shared by every rule set in the pipeline.

Combiner (all rule sets in TempEKG have this form):
    out(x) = rel(argmax_{r in A(x)} key(r))    if A(x) is non-empty
           = fb(x)                              otherwise
A(x) = ACTIVE rules firing on x (confidence above the floor of the rule's label / group),
key(r) = (w(r), -r) (a strict total order), fb(x) = the fallback: BEFORE (EV-EV), the majority
label (TIMEX edges), the incoming label (layered override, Bai 2 auditor).

Let o = out(x) and M(x) = max key of firing active rules whose label differs from o.
  * If A(x) is empty, any subset keeps out(x) = fb(x): deleting rules cannot make one fire.
  * If o = fb(x) and every firing rule has label o, any subset keeps out(x) = fb(x).
  * Otherwise out_K(x) = o is guaranteed when K contains a rule of C(x) = {r in A(x): rel(r) = o,
    key(r) > M(x)}: that rule still fires and beats every other label.            (sufficient)
So "keep every output" is SET COVER over U = {x with a constraint}, sets C(x). Variant B restricts U
to rows whose output is correct: every correct row stays correct.
Greedy (lazy) <= H(d) * OPT; reverse deletion makes K irredundant; a lower bound on OPT is the
size of any family of rows with pairwise disjoint C(x) (greedy packing, smallest C(x) first).
"""
import heapq
from collections import Counter, defaultdict

def output(hits, fb, W, REL, keep=None):
    best = None
    for r in hits:
        if keep is not None and r not in keep: continue
        if best is None or (W[r], -r) > (W[best], -best): best = r
    return REL[best] if best is not None else fb

def constraints(rows, W, REL, correct_only=False):
    """rows: iterable of (hits, fallback, gold). Returns the list of candidate sets C(x)."""
    out = []
    for hits, fb, g in rows:
        if not hits: continue
        o = output(hits, fb, W, REL)
        if correct_only and o != g: continue
        other = [(W[r], -r) for r in hits if REL[r] != o]
        if o == fb and not other: continue
        M = max(other) if other else (-1e9, 0)
        out.append(frozenset(r for r in hits if REL[r] == o and (W[r], -r) > M))
    return out

def cover(elems, W):
    """Greedy set cover + reverse deletion; returns (K, forced, lower bound, max coverage)."""
    if not elems: return set(), 0, 0, 0
    by_rule = defaultdict(list)
    for e, C in enumerate(elems):
        assert C, "empty candidate set"
        for r in C: by_rule[r].append(e)
    forced = {next(iter(C)) for C in elems if len(C) == 1}
    covered = [False]*len(elems); K = set()
    for r in forced:
        K.add(r)
        for e in by_rule[r]: covered[e] = True
    heap = [(-len(es), -W[r], r) for r, es in by_rule.items() if r not in K]; heapq.heapify(heap)
    while heap:
        g, w, r = heapq.heappop(heap)
        gain = sum(1 for e in by_rule[r] if not covered[e])
        if gain == 0: continue
        if gain < -g: heapq.heappush(heap, (-gain, w, r)); continue
        K.add(r)
        for e in by_rule[r]: covered[e] = True
    assert all(covered)
    cc = [0]*len(elems)
    for r in K:
        for e in by_rule[r]: cc[e] += 1
    for r in sorted(K, key=lambda r: (len(by_rule[r]), W[r])):
        if all(cc[e] >= 2 for e in by_rule[r]):
            K.discard(r)
            for e in by_rule[r]: cc[e] -= 1
    used = set(); lb = 0
    for C in sorted(elems, key=len):
        if not (C & used): used |= C; lb += 1
    return K, len(forced), lb, max(len(v) for v in by_rule.values())

def equivalence(rows_all, REL, active):
    """Classes of active rules with the same label and the same firing set over rows_all."""
    ext = defaultdict(list)
    for i, (hits, fb, g) in enumerate(rows_all):
        for r in hits: ext[r].append(i)
    cls = defaultdict(list)
    for r in active: cls[(REL[r], tuple(ext.get(r, ())))].append(r)
    return list(cls.values())

def macro(pred, gold, rels):
    tp, fp, fn = Counter(), Counter(), Counter()
    for p, g in zip(pred, gold):
        if p == g: tp[g] += 1
        else: fp[p] += 1; fn[g] += 1
    per = {}
    for r in rels:
        P = tp[r]/(tp[r] + fp[r]) if tp[r] + fp[r] else 0.0; R = tp[r]/(tp[r] + fn[r]) if tp[r] + fn[r] else 0.0
        per[r] = 2*P*R/(P + R) if P + R else 0.0
    return sum(per.values())/len(rels), sum(tp.values())/max(1, len(gold)), per
