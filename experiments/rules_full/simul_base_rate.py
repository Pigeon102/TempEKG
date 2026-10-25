"""SIMULTANEOUS base rate over EV->EV pairs: all pairs vs same-sentence pairs (sentence distance 0).

Sentence distance is |sent_first(a) - sent_first(b)|, as in mine_compositional.pair_features,
which defines the sdist view used by the miner. Printed for the training split (all documents and
the DISCOVERY part used for mining) and for the validation split.
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import hashlib, json
from collections import Counter
from pathlib import Path

GRAPH = Path(__file__).resolve().parents[2] / "src" / "graph"


def rates(split, only_discovery=False):
    c = Counter()
    with open(GRAPH / (split + ".jsonl"), encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if only_discovery and int(hashlib.md5(d["doc_id"].encode()).hexdigest(), 16) % 10 < 4:
                continue                      # DISCOVERY = md5(doc) % 10 >= 4, as in mine_full.py
            nd = d["nodes"]
            for e in d["target_edges"]:
                a, b = nd.get(e["s"]), nd.get(e["t"])
                if not a or not b or a["kind"] != "event" or b["kind"] != "event":
                    continue
                same = a.get("sent_first") is not None and a.get("sent_first") == b.get("sent_first")
                simu = e["rel"] == "SIMULTANEOUS"
                c["all"] += 1; c["all_simu"] += simu
                if same: c["same"] += 1; c["same_simu"] += simu
    return c


for name, split, disc in (("train (all)", "train", False), ("train DISCOVERY", "train", True), ("validation", "valid", False)):
    c = rates(split, disc)
    print("%-16s all EV->EV %7d  SIMULTANEOUS %5d = %.2f%% | same sentence %6d  SIMULTANEOUS %5d = %.2f%%"
          % (name, c["all"], c["all_simu"], 100 * c["all_simu"] / c["all"], c["same"], c["same_simu"], 100 * c["same_simu"] / c["same"]))
