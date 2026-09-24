# -*- coding: utf-8 -*-
"""Summarise the seed sweep: per metric, per pipeline, mean +- sd over seeds, and the paired
difference new - old with a paired t interval (Student t, df = n - 1). Seed 0 = the original runs."""
import io, re, math, sys
from pathlib import Path
ROOT = Path(r"C:\Reseach_Quang\tempekg\experiments")
L = ROOT/"seeds"/"logs"
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}

def read(p):
    try: return io.open(p, encoding="utf-8", errors="replace").read()
    except FileNotFoundError: return None

def parse_layered(txt):
    m = re.search(r"GOP 188\.924 CANH: giai doan 1 macro ([\d.]+)% .*?theo tang ([\d.]+)%", txt)
    ee = re.search(r"EV-EV --.*?giai doan 1:\s+macro\s+([\d.]+)%.*?\+ pattern \+ luat lien tang\s+macro\s+([\d.]+)%", txt, re.S)
    return {"2.1 gop": float(m.group(1)), "2.2 gop": float(m.group(2)),
            "2.1 EV-EV": float(ee.group(1)), "2.2 EV-EV": float(ee.group(2))} if m and ee else {}

def parse_combo(txt):
    out = {}
    m = re.search(r"chi tam giac \| macro-F1.*?macro-F1\s+([\d.]+)%", txt)
    if m: out["2.3 gop"] = float(m.group(1))
    m = re.search(r"B -> tam giac \| giam loi.*?loi\s+([\d.]+)% ->\s+([\d.]+)%", txt)
    if m: out["Bai 2 loi truoc"] = float(m.group(1)); out["Bai 2 loi sau"] = float(m.group(2))
    m = re.search(r"B -> tam giac \| macro-F1.*?macro-F1\s+([\d.]+)%", txt)
    if m: out["Bai 2 macro"] = float(m.group(1))
    return out

def seed_metrics(s):
    R = {}
    if s == 0:
        new_l = read(ROOT/"logs"/"layered_rules_full.log"); new_c = read(ROOT/"logs"/"bai2_combo_full.log")
        old_l = read(ROOT/"logs"/"layered_rules.log"); old_c = read(ROOT/"logs"/"bai2_combo.log")
    else:
        new_l = read(L/f"s{s}_new_layered.log"); new_c = read(L/f"s{s}_new_combo.log")
        old_l = read(L/f"s{s}_old_layered.log"); old_c = read(L/f"s{s}_old_combo.log")
    for nm, lt, ct in (("new", new_l, new_c), ("old", old_l, old_c)):
        d = {}
        if lt: d.update(parse_layered(lt))
        if ct: d.update(parse_combo(ct))
        R[nm] = d
    return R

seeds = [0] + [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else [0, 1, 2, 3, 4]
data = {s: seed_metrics(s) for s in seeds}
METRICS = ["2.1 EV-EV", "2.1 gop", "2.2 EV-EV", "2.2 gop", "2.3 gop", "Bai 2 loi truoc", "Bai 2 loi sau", "Bai 2 macro"]
def ms(xs):
    n = len(xs); m = sum(xs)/n
    sd = math.sqrt(sum((x - m)**2 for x in xs)/(n - 1)) if n > 1 else 0.0
    return m, sd
print("=" * 118); print("SEED SWEEP -- valid co dinh; seed doi cach chia train, fold cross-fit va PYTHONHASHSEED"); print("=" * 118)
print("  %-16s | %-44s | %-44s" % ("chi so", "moi: tung seed -> TB +- sd", "cu: tung seed -> TB +- sd"))
for k in METRICS:
    cells = []
    for nm in ("new", "old"):
        xs = [data[s][nm][k] for s in seeds if k in data[s][nm]]
        if not xs: cells.append("-"); continue
        m, sd = ms(xs)
        cells.append("%s -> %.2f +- %.2f" % (" ".join("%.2f" % x for x in xs), m, sd))
    print("  %-16s | %-44s | %-44s" % (k, cells[0], cells[1]))
print()
print("  HIEU CAP moi - cu (cung seed):")
for k in METRICS:
    ds = [data[s]["new"][k] - data[s]["old"][k] for s in seeds if k in data[s]["new"] and k in data[s]["old"]]
    if len(ds) < 2: continue
    m, sd = ms(ds); n = len(ds); se = sd/math.sqrt(n); t = m/se if se > 0 else float("inf")
    tc = T975.get(n - 1, 2.0)
    print("    %-16s n=%d  hieu TB %+.2f  sd %.2f  95%% CI [%+.2f, %+.2f]  t=%.2f  moi > cu o %d/%d seed" %
          (k, n, m, sd, m - tc*se, m + tc*se, t, sum(1 for d in ds if d > 0), n))
