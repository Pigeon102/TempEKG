# -*- coding: utf-8 -*-
"""Real worked examples for RULESET.md: a valid EV-EV pair, the full-train rules that fire on it,
which of them pass the per-label floors, and the label the combiner emits (gold shown)."""
import io, os, json, pickle
from pathlib import Path
from collections import defaultdict
OUT = Path(__file__).resolve().parent
GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
RAW = {}
for line in io.open(Path(r"C:\Reseach_Quang\MAVEN_ERE")/"valid.jsonl", encoding="utf-8"):
    r = json.loads(line); RAW[r["id"]] = r
R = pickle.load(open(OUT/"rules_confirmed.pkl", "rb"))
if os.environ.get("COMPACT"):   # keep only the 378-rule compact set (variant A); others can never vote
    CA = json.load(io.open(OUT.parent.parent/"src"/"artifacts"/"rules_compact.json", encoding="utf-8"))["variants"]["A: giu moi du doan"]
    KA = {(x["view"], json.dumps(x["sig"]), json.dumps(x["conds"]), x["rel"]) for x in CA}
    R = [dict(x, wlb=(x["wlb"] if (x["view"], json.dumps(x["sig"]), json.dumps(x["conds"]), x["rel"]) in KA else -1.0)) for x in R]
    print("bo gon: %d luat" % sum(1 for x in R if x["wlb"] >= 0))
G = pickle.load(open(OUT/"cache_sp3.pkl", "rb"))
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
TH = {"CONTAINS": 0.5, "SIMULTANEOUS": 0.15, "OVERLAP": 0.1}
idx = defaultdict(list)
for rid, x in enumerate(R): idx[(x["v"], x["s"], x["key"][0])].append((rid, x["key"][1:]))
keys, nodes = [], []
for line in io.open(GRAPH/"valid.jsonl", encoding="utf-8"):
    rec = json.loads(line); nd = rec["nodes"]
    for e in rec["target_edges"]:
        na, nb = nd.get(e["s"]), nd.get(e["t"])
        if not na or not nb or na["kind"] != "event" or nb["kind"] != "event": continue
        keys.append((rec["doc_id"], e["s"], e["t"])); nodes.append((na, nb))
assert len(keys) == len(G["lab"])
def fire(i):
    cs = set(G["conds"][i]); hits = []
    for v in range(8):
        s = G["sig"][v][i]
        for c in cs:
            for rid, rest in idx.get((v, s, c), ()):
                if all(z in cs for z in rest): hits.append(rid)
    return hits
shown = defaultdict(int)
for i in range(len(keys)):
    g = RELS[G["lab"][i]]
    if g not in ("SIMULTANEOUS", "OVERLAP", "CONTAINS") or shown[g] >= 2: continue
    na, nb = nodes[i]
    if na.get("sent_first") != nb.get("sent_first"): continue
    hits = fire(i); act = [R[h] for h in hits if R[h]["rel"] in TH and R[h]["wlb"] >= TH[R[h]["rel"]]]
    if not act: continue
    best = max(act, key=lambda x: x["wlb"])
    if best["rel"] != g or len(act) > 6: continue
    doc, a, b = keys[i]; raw = RAW[doc]
    print("=" * 100)
    print("[%s] %s | gold %s" % (doc, raw["title"], g))
    print("  A = %s (%s)   B = %s (%s)   câu %d" % (na.get("trigger"), na.get("type"), nb.get("trigger"), nb.get("type"), na.get("sent_first")))
    print("  câu: %s" % raw["sentences"][na["sent_first"]])
    print("  %d luật bắn; theo nhãn: %s" % (len(hits), {r: sum(1 for h in hits if R[h]["rel"] == r) for r in RELS[1:]}))
    for x in sorted(act, key=lambda x: -x["wlb"]):
        print("   qua ngưỡng: %-12s view %s=%s  %s  disc %d/%d conf %d/%d wlb %.3f" % (x["rel"], x["view"], x["sig"], x["conds"], x["k"], x["n"], x["ck"], x["cn"], x["wlb"]))
    print("  -> nhãn phát: %s (luật có wlb cao nhất)" % best["rel"])
    shown[g] += 1
    if all(shown[z] >= 2 for z in ("SIMULTANEOUS", "OVERLAP", "CONTAINS")): break
