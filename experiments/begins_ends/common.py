# -*- coding: utf-8 -*-
"""Shared loaders for the BEGINS-ON / ENDS-ON study. Plain Python, streaming, modest memory."""
import io, json, math, hashlib, re
from pathlib import Path
from collections import Counter, defaultdict

SRC = Path(r"C:\Reseach_Quang\tempekg\src")
GRAPH = SRC / "graph"
ART = SRC / "artifacts"
RAW = Path(r"C:\Reseach_Quang\MAVEN_ERE")
OUT = Path(r"C:\Reseach_Quang\tempekg\experiments\begins_ends")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
RARE = ("BEGINS-ON", "ENDS-ON")
SYM = {"SIMULTANEOUS", "BEGINS-ON"}
Z = 1.959963985
ETYPES = ("EE", "ET", "TE", "TT")   # EV-EV, EV->TIMEX, TIMEX->EV, TIMEX-TIMEX (stored direction)


def h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def split_of(doc):
    """0 DISCOVERY, 1 CONFIRMATION-1, 2 CONFIRMATION-2 (train only). Valid is 3."""
    if h(doc) % 10 >= 4:
        return 0
    return 1 if h("s2" + doc) % 2 == 0 else 2


def wlb(k, n):
    if n == 0:
        return 0.0
    p = k / n
    return (p + Z * Z / (2 * n) - Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))) / (1 + Z * Z / n)


def iter_kg(split):
    for line in io.open(GRAPH / f"{split}.jsonl", encoding="utf-8"):
        yield json.loads(line)


def iter_raw(split):
    for line in io.open(RAW / f"{split}.jsonl", encoding="utf-8"):
        yield json.loads(line)


def etype_of(na, nb):
    return ("E" if na["kind"] == "event" else "T") + ("E" if nb["kind"] == "event" else "T")


def load_preds(keep_docs):
    """Stream pred_layered_full.json and keep only keys whose doc id is in keep_docs."""
    pat = re.compile(r'"([0-9a-f]{32})\|([^"|]+)\|([^"|]+)":\s*"([A-Z-]+)"')
    out = {}
    buf = ""
    with io.open(ART / "pred_layered_full.json", encoding="utf-8") as f:
        while True:
            chunk = f.read(1 << 22)
            if not chunk:
                break
            buf += chunk
            last = 0
            for m in pat.finditer(buf):
                last = m.end()
                if m.group(1) in keep_docs:
                    out[(m.group(1), m.group(2), m.group(3))] = m.group(4)
            buf = buf[last:]
    return out


def prf(tp, fp, fn):
    P = tp / (tp + fp) if tp + fp else 0.0
    R = tp / (tp + fn) if tp + fn else 0.0
    F = 2 * P * R / (P + R) if P + R else 0.0
    return P, R, F


def macro(pred, gold):
    tp, fp, fn = Counter(), Counter(), Counter()
    for q, g in zip(pred, gold):
        if q == g:
            tp[g] += 1
        else:
            fp[q] += 1
            fn[g] += 1
    per = {r: prf(tp[r], fp[r], fn[r]) for r in RELS}
    return sum(v[2] for v in per.values()) / 6, per, sum(tp.values()) / max(1, len(gold))
