# -*- coding: utf-8 -*-
"""Worked example for the seminar: the real 'United States occupation of Nicaragua' valid document.
Prints every edge among began / 1898 / 1912 / 1933 / 1934 with classifier, repaired and gold labels,
and the local energy of each candidate label for the edges the joint repair changes.
Joint repair alone, classifier channel from CONFIRMATION-2, parameters (mean, lambda 1.0, alpha 0.5) =
the configuration chosen by macro-F1 for the triangle step alone. Run from src/ with TAG=_full."""
import io, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(SRC[:SRC.index("def evaluate(docs, obs_of, fin_of):")])
DOC = "f28bce270df5a122c09365002d247e76"
d = [x for x in VA if x["id"] == DOC][0]
cls = lambda dd: [PL.get("%s|%s|%s" % (dd["id"], e[0], e[1]), "BEFORE") for e in dd["edges"]]
C = chan_confusion(TUNE, cls)
LAM, MODE, ALPHA = 1.0, "mean", 0.5
obs = cls(d); fin = repair(d, obs, C, LAM, MODE, ALPHA)
nd = d["nd"]
def name(n):
    v = nd[n]; return v.get("text") if v.get("kind") == "timex" else v.get("trigger")
want = {"began", "1898", "1912", "1933", "1934"}
nodes = {n for n in nd if nd[n].get("kind") in ("event", "timex") and name(n) in want}
print("nodes:", {n: name(n) for n in nodes})
print("\nEDGES among them (stored direction):")
for j, (a, b, r, k) in enumerate(d["edges"]):
    if a in nodes and b in nodes:
        print("  %-6s -> %-6s  type %s  classifier %-12s repaired %-12s gold %-12s" % (name(a), name(b), k, obs[j], fin[j], r))
changed = [j for j, (a, b, r, k) in enumerate(d["edges"]) if obs[j] != fin[j]]
print("\nedges changed in the whole document: %d (of %d); wrong before %d, after %d" % (
    len(changed), len(obs), sum(1 for j, e in enumerate(d["edges"]) if obs[j] != e[2]), sum(1 for j, e in enumerate(d["edges"]) if fin[j] != e[2])))
for j in changed:
    a, b, r, k = d["edges"][j]
    print("  changed: %s -> %s : %s -> %s (gold %s)" % (name(a), name(b), obs[j], fin[j], r))

def local_parts(lab, j, l):
    k = d["edges"][j][3]
    u_prior = -(1 - ALPHA) * math.log(Q[k][l]); u_chan = -C[(k, obs[j], l)]
    ts = d["inc"].get(j, ())
    pm = []
    for tid, pos_ in ts:
        kinds, parts = d["tris"][tid]
        ol = [olab(lab[jj], rev) for jj, rev in parts]; ol[pos_] = olab(l, parts[pos_][1])
        pm.append(tri_pmi(kinds, tuple(ol)))
    s = -sum(pm) / (len(pm) if MODE == "mean" else 1) if pm else 0.0
    return u_chan, u_prior, s, len(pm), u_chan + u_prior + LAM * s

# energies at the start (all other edges at classifier labels) for the edges within the 5 nodes that changed
print("\nLOCAL ENERGY at the start (other edges = classifier labels), lambda %.1f alpha %.1f mean:" % (LAM, ALPHA))
for j in changed:
    a, b, r, k = d["edges"][j]
    if not (a in nodes and b in nodes): continue
    print("  edge %s -> %s (observed %s, gold %s), %d triangles" % (name(a), name(b), obs[j], r, len(d["inc"].get(j, ()))))
    for l in LABS:
        if Q[k][l] < 1e-4: continue
        uc, up, s, nt, tot = local_parts(obs, j, l)
        print("     %-12s  -logC %6.2f  -(1-a)logq %5.2f  mean(-PMI) %6.2f  total %7.2f" % (l, uc, up, s, tot))

# the triangle began-1912-1934: configuration counts and PMI before / after
print("\nTRIANGLES made only of the 5 nodes:")
for tid, (kinds, parts) in enumerate(d["tris"]):
    ns = set()
    for jj, _ in parts: ns.update(d["edges"][jj][:2])
    if ns <= nodes:
        cb = kinds + tuple(olab(obs[jj], rev) for jj, rev in parts)
        ca = kinds + tuple(olab(fin[jj], rev) for jj, rev in parts)
        names = " / ".join("%s-%s" % (name(d["edges"][jj][0]), name(d["edges"][jj][1])) for jj, _ in parts)
        print("  %s | before %s count %d PMI %.2f | after %s count %d PMI %.2f" % (
            names, cb[3:], FREQ.get(cb, 0), tri_pmi(kinds, cb[3:]), ca[3:], FREQ.get(ca, 0), tri_pmi(kinds, ca[3:])))
print("\nchannel P(seen | true) for EV->TIMEX / TIMEX->EV rows used above:")
for k in ("ET", "TE"):
    for l in ("BEFORE", "OVERLAP", "CONTAINS"):
        print("  %s true %-9s : " % (k, l) + "  ".join("%s %.3f" % (p[:4], math.exp(C[(k, p, l)])) for p in LABS))
print("q (label prior) ET:", {l[:4]: round(Q["ET"][l], 4) for l in LABS}, " TE:", {l[:4]: round(Q["TE"][l], 4) for l in LABS})
