# -*- coding: utf-8 -*-
"""Pull REAL examples from MAVEN-ERE for the reports (no illustration invented):
  1. BEGINS-ON / ENDS-ON edges with their sentences
  2. a small real document subgraph with all four edge types and an event triangle
  3. a real triangle the classifier got wrong, whose configuration never occurs in gold, and that
     the document-level joint repair fixed (classifier channel, parameters chosen for net errors)
  4. the strongest new full-train EV-EV rules per label
"""
import io, json, pickle, math, random
from pathlib import Path
from collections import Counter, defaultdict
HERE = Path(__file__).resolve().parent
SRC = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(SRC[:SRC.index("def evaluate(docs, obs_of, fin_of):")])
RAW = {}
for split in ("train", "valid"):
    for line in io.open(Path(r"C:\Reseach_Quang\MAVEN_ERE")/f"{split}.jsonl", encoding="utf-8"):
        r = json.loads(line); RAW[r["id"]] = r
def sent(docid, k):
    s = RAW[docid]["sentences"]; return s[k] if 0 <= k < len(s) else ""
def name(d, n):
    v = d["nd"][n]
    return ("TIMEX “%s”" % v.get("text")) if v.get("kind") == "timex" else ("“%s” (%s)" % (v.get("trigger"), v.get("type")))
def sid(d, n): return d["nd"][n].get("sent_first", -1)

print("=" * 100); print("1. VI DU THAT: BEGINS-ON va ENDS-ON"); print("=" * 100)
for lab in ("BEGINS-ON", "ENDS-ON"):
    shown = 0
    for d in VA + TR:
        for (a, b, r, k) in d["edges"]:
            if r != lab or shown >= 5: continue
            if abs(sid(d, a) - sid(d, b)) > 0: continue
            print("[%s] %s | %s  --%s-->  %s" % (lab, RAW[d["id"]]["title"], name(d, a), lab, name(d, b)))
            print("      câu: %s" % sent(d["id"], sid(d, a)))
            shown += 1

print(); print("=" * 100); print("2. DO THI DOCUMENT THAT: du 4 loai canh + tam giac su kien, cau gan nhau"); print("=" * 100)
found = 0
for d in VA:
    E = {(a, b): (r, k) for (a, b, r, k) in d["edges"]}
    K = {n: d["nd"][n].get("kind") for n in d["nd"]}
    evs = [n for n in d["nd"] if K.get(n) == "event"]; txs = [n for n in d["nd"] if K.get(n) == "timex"]
    for t1 in txs:
        for t2 in txs:
            if (t1, t2) not in E: continue
            for e1 in evs:
                if (t1, e1) not in E: continue
                for e3 in evs:
                    if e3 == e1 or (t2, e3) not in E: continue
                    for e2 in evs:
                        if e2 in (e1, e3): continue
                        if (e2, t2) not in E and (e2, t1) not in E: continue
                        tri = [((x, y) if (x, y) in E else (y, x)) for x, y in ((e1, e2), (e2, e3), (e1, e3))]
                        if not all(p in E for p in tri): continue
                        ss = {sid(d, n) for n in (t1, t2, e1, e2, e3)}
                        if max(ss) - min(ss) > 2: continue
                        if found < 3:
                            print("\n[%s] %s" % (d["id"], RAW[d["id"]]["title"]))
                            for n in (t1, t2, e1, e2, e3): print("   node %-40s câu %d" % (name(d, n), sid(d, n)))
                            for p in [(t1, t2), (t1, e1), (t2, e3), ((e2, t2) if (e2, t2) in E else (e2, t1))] + tri:
                                print("   %s --%s--> %s" % (name(d, p[0]), E[p][0], name(d, p[1])))
                            for k_ in sorted(ss): print("   câu %d: %s" % (k_, sent(d["id"], k_)))
                        found += 1
                        break
                    if found >= 3: break
                if found >= 3: break
            if found >= 3: break
        if found >= 3: break
    if found >= 3: break

print(); print("=" * 100); print("3. TAM GIAC THAT: classifier sai, cau hinh chua tung gap trong gold, sua chung da sua dung"); print("=" * 100)
cls = lambda d: [PL.get("%s|%s|%s" % (d["id"], e[0], e[1]), "BEFORE") for e in d["edges"]]
C = chan_confusion(TUNE, cls)
shown = 0
for d in VA:
    obs = cls(d); fin = repair(d, obs, C, 0.2, "mean", 0.0)
    for kinds, parts in d["tris"]:
        before = kinds + tuple(olab(obs[j], rev) for j, rev in parts)
        after = kinds + tuple(olab(fin[j], rev) for j, rev in parts)
        gold = kinds + tuple(olab(d["edges"][j][2], rev) for j, rev in parts)
        changed = [j for j, _ in parts if obs[j] != fin[j]]
        if FREQ.get(before, 0) == 0 and after == gold and len(changed) == 1 and FREQ.get(after, 0) > 0:
            j = changed[0]; a, b, g, k = d["edges"][j]
            nodes = set()
            for jj, _ in parts: nodes.update(d["edges"][jj][:2])
            ss = {sid(d, n) for n in nodes}
            if max(ss) - min(ss) > 1 or shown >= 3: continue
            print("\n[%s] %s" % (d["id"], RAW[d["id"]]["title"]))
            for jj, _ in parts:
                x, y, gg, kk = d["edges"][jj]
                print("   %s --[classifier %s | sau sua %s | gold %s]--> %s" % (name(d, x), obs[jj], fin[jj], gg, name(d, y)))
            print("   tan suat cau hinh trong gold: truoc %d, sau %d" % (FREQ.get(before, 0), FREQ.get(after, 0)))
            for k_ in sorted(ss): print("   câu %d: %s" % (k_, sent(d["id"], k_)))
            shown += 1
    if shown >= 3: break

print(); print("=" * 100); print("4. LUAT EV-EV MOI (mine tren toan bo train)"); print("=" * 100)
R = pickle.load(open(r"C:\Reseach_Quang\tempekg\experiments\rules_full\rules_confirmed.pkl", "rb"))
cfg = json.load(io.open(ART/"rules_full.json", encoding="utf-8"))["config"]
print("combiner:", cfg)
print("so luat theo nhan:", dict(Counter(x["rel"] for x in R)))
print("so luat theo view:", dict(Counter(x["view"] for x in R)))
print("so luat theo do sau:", dict(Counter(len(x["key"]) for x in R)))
act = [x for x in R if x["wlb"] >= cfg.get(x["rel"], 9)]
print("luat duoc bat boi nguong (co the phat nhan): %d, theo nhan %s" % (len(act), dict(Counter(x["rel"] for x in act))))
for lab in ("OVERLAP", "SIMULTANEOUS", "CONTAINS", "BEGINS-ON", "ENDS-ON"):
    lst = sorted((x for x in R if x["rel"] == lab and x["cn"] >= 20), key=lambda x: -x["wlb"])[:5]
    print("\n  %s (ngưỡng bật %s):" % (lab, cfg.get(lab)))
    for x in lst:
        print("    view %-9s lớp %-28s %s  -> k/n disc %d/%d, conf %d/%d, cwlb %.3f" % (
            x["view"], str(x["sig"])[:28], " AND ".join("%s(%s=%s)" % (c[0], c[1], c[2]) for c in x["conds"]), x["k"], x["n"], x["ck"], x["cn"], x["wlb"]))
log("xong")
