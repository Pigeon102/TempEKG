# -*- coding: utf-8 -*-
"""Predictions of the full-train EV-EV rule set for EVERY EV-EV pair (train and valid), with the
combiner chosen on CONFIRMATION-2 (per-label precision floors), merged into a copy of the
all-edge prediction file so the later steps (layered rules, Bai 2) can be rebuilt on it.

Output: src/artifacts/pred_all_edges_full.json  (EV-EV from the new rules, TIMEX edges unchanged)
"""
import io, os, sys, json, pickle
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mine_full as MF

def main():
    NW = int(os.environ.get("NW", "4"))
    rules = pickle.load(open(MF.OUT/"rules_confirmed.pkl", "rb"))
    cfg = json.load(io.open(MF.ART/("rules_full%s.json" % MF.SFX), encoding="utf-8"))["config"]
    RL = [x["rel"] for x in rules]; CW = [x["wlb"] for x in rules]
    TH = {r: cfg.get(r, 9) for r in MF.RELS}
    # keys in cache order, per split
    keys = defaultdict(list)
    for split in ("train", "valid"):
        for line in io.open(MF.GRAPH/f"{split}.jsonl", encoding="utf-8"):
            rec = json.loads(line); nd = rec["nodes"]
            s = MF.split_of(rec["doc_id"]) if split == "train" else 3
            for e in rec["target_edges"]:
                na, nb = nd.get(e["s"]), nd.get(e["t"])
                if not na or not nb or na["kind"] != "event" or nb["kind"] != "event": continue
                keys[s].append("%s|%s|%s" % (rec["doc_id"], e["s"], e["t"]))
    out = {}
    for which in (0, 1, 2, 3):
        with open(MF.OUT/("cache_sp%d.pkl" % which), "rb") as fh: n = len(pickle.load(fh)["lab"])
        assert n == len(keys[which]), (which, n, len(keys[which]))
        MF.log("ban luat tren phan %d (%d cap) ..." % (which, n))
        F = MF.fire_all(which, n, NW)
        for k, hits in zip(keys[which], F):
            best = None
            for rid in hits:
                if CW[rid] >= TH[RL[rid]] and (best is None or CW[rid] > best[1]): best = (RL[rid], CW[rid])
            out[k] = best[0] if best else "BEFORE"
    base = json.load(io.open(MF.ART/("pred_all_edges%s.json" % MF.SFX), encoding="utf-8"))
    n_over = sum(1 for k in out if k in base)
    base.update(out)
    json.dump(base, io.open(MF.ART/("pred_all_edges_full%s.json" % MF.SFX), "w", encoding="utf-8"))
    MF.log("da ghi pred_all_edges_full.json: %d du doan EV-EV moi (%d thay cho du doan cu)" % (len(out), n_over))

if __name__ == "__main__":
    main()
