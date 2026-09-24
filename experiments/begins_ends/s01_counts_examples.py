# -*- coding: utf-8 -*-
"""Step 1a: gold counts of BEGINS-ON / ENDS-ON per edge type and split; dump every instance with text.

Outputs
  logs/s01_counts.log              counts per (split, edge type, label)
  logs/examples_<LABEL>_<ET>.txt   every instance (train + valid), sentence text with mentions marked
"""
import io, json, random
from collections import Counter, defaultdict
from common import *

SPN = {0: "DISC", 1: "CONF1", 2: "CONF2", 3: "VALID"}
cnt = Counter()
tot = Counter()
docs_with = defaultdict(set)
inst = []  # (split, doc, etype, s, t, rel)
for split in ("train", "valid"):
    for rec in iter_kg(split):
        doc = rec["doc_id"]; nd = rec["nodes"]
        sp = split_of(doc) if split == "train" else 3
        for e in rec["target_edges"]:
            na, nb = nd.get(e["s"]), nd.get(e["t"])
            if not na or not nb:
                continue
            et = etype_of(na, nb)
            tot[(sp, et)] += 1
            cnt[(sp, et, e["rel"])] += 1
            if e["rel"] in RARE:
                inst.append((sp, doc, et, e["s"], e["t"], e["rel"]))
                docs_with[(sp == 3, e["rel"], et)].add(doc)

L = io.open(OUT / "logs" / "s01_counts.log", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a); print(s); L.write(s + "\n")

P("Counts of rare labels per split x edge type (KG target_edges, symmetric duplicates already removed)")
for rel in RARE:
    P("\n%s" % rel)
    P("%-6s" % "split" + "".join("%12s" % et for et in ETYPES) + "%10s" % "total")
    for sp in (0, 1, 2, 3):
        row = [cnt[(sp, et, rel)] for et in ETYPES]
        P("%-6s" % SPN[sp] + "".join("%12d" % x for x in row) + "%10d" % sum(row))
    row = [sum(cnt[(sp, et, rel)] for sp in (0, 1, 2)) for et in ETYPES]
    P("%-6s" % "TRAIN" + "".join("%12d" % x for x in row) + "%10d" % sum(row))
P("\nAll edges per split x edge type")
for sp in (0, 1, 2, 3):
    P("%-6s" % SPN[sp] + "".join("%12d" % tot[(sp, et)] for et in ETYPES) + "%10d" % sum(tot[(sp, et)] for et in ETYPES))
P("\nDistinct documents carrying the label (train / valid)")
for rel in RARE:
    for et in ETYPES:
        P("  %-9s %s  train %4d docs   valid %3d docs" % (rel, et, len(docs_with[(False, rel, et)]), len(docs_with[(True, rel, et)])))

# ---------------------------------------------------------------- text dump
need = defaultdict(list)
for x in inst:
    need[x[1]].append(x)
ment = {}
texts = {}
for split in ("train", "valid"):
    for r in iter_raw(split):
        if r["id"] not in need:
            continue
        m = {}
        for ev in r["events"]:
            m[ev["id"]] = [(mm["sent_id"], mm["offset"][0], mm["offset"][1], mm["trigger_word"]) for mm in ev["mention"]]
        for tx in r["TIMEX"]:
            m[tx["id"]] = [(tx["sent_id"], tx["offset"][0], tx["offset"][1], tx["mention"] + " [" + tx["type"] + "]")]
        ment[r["id"]] = m
        texts[r["id"]] = (r["title"], r["tokens"])


def render(doc, s, t):
    title, toks = texts[doc]; m = ment[doc]
    best = None
    for a in m[s]:
        for b in m[t]:
            d = abs(a[0] - b[0])
            if best is None or d < best[0]:
                best = (d, a, b)
    d, a, b = best
    lines = []
    for sid in sorted({a[0], b[0]}):
        tk = list(toks[sid])
        marks = []
        if a[0] == sid: marks.append((a[1], a[2], "[A ", " A]"))
        if b[0] == sid: marks.append((b[1], b[2], "[B ", " B]"))
        for st, en, o, c in sorted(marks, key=lambda z: -z[0]):
            tk[en - 1] = tk[en - 1] + c
            tk[st] = o + tk[st]
        lines.append("   s%d: %s" % (sid, " ".join(tk)))
    return title, a[3], b[3], d, lines


by = defaultdict(list)
for x in inst:
    by[(x[5], x[2])].append(x)
for (rel, et), xs in sorted(by.items()):
    with io.open(OUT / "logs" / ("examples_%s_%s.txt" % (rel, et)), "w", encoding="utf-8") as f:
        f.write("%s %s: %d instances (train+valid). Head=A (stored s), tail=B (stored t)\n\n" % (rel, et, len(xs)))
        for sp, doc, _, s, t, _ in sorted(xs, key=lambda z: (z[0] != 3, z[1])):
            title, ta, tb, d, lines = render(doc, s, t)
            f.write("[%s] %s | %s  A=%r  B=%r  sent-dist=%d\n" % (SPN[sp], doc[:8], title, ta, tb, d))
            f.write("\n".join(lines) + "\n\n")
P("\nexample files written:", ", ".join("%s_%s(%d)" % (k[0], k[1], len(v)) for k, v in sorted(by.items())))
