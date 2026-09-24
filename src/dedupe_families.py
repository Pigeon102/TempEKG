"""Collapse families that differ only in which type attribute they abstracted away.

export_rules.py keys a family by its skeleton, and `EQ(type_a=Competition)` and
`EQ(type_pair=(Competition, Attack))` are different skeletons. Once the type literal is
replaced by a wildcard and then dropped, both leave the same abstract rule, so the same
statement is written twice with different member counts. 380 of 1,453 entries are such
duplicates; the honest count is 1,073.

Keeps the entry with the most members (it saw more evidence) and sums the member counts,
since the variants really are distinct instantiations of one family.

Usage:
    python dedupe_families.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE / "artifacts"   # mined artifacts; see data/README.md


def main() -> int:
    src = ART / "families.json"
    fams = json.loads(src.read_text(encoding="utf-8"))
    print(f"input: {len(fams):,} families")

    groups = defaultdict(list)
    for f in fams:
        groups[(f["text"], f["rel"], f["view"], f["sig"])].append(f)

    out = []
    for key, members in groups.items():
        best = max(members, key=lambda m: m["members"])
        merged = dict(best)
        merged["members"] = sum(m["members"] for m in members)
        merged["variants"] = len(members)
        types = []
        for m in members:
            for t in m.get("types", []):
                if t not in types:
                    types.append(t)
        merged["types"] = types[:12]
        out.append(merged)

    out.sort(key=lambda f: -f["wlb"])
    dst = ART / "families_dedup.json"
    dst.write_text(json.dumps(out, indent=1), encoding="utf-8")

    print(f"output: {len(out):,} distinct families  ({len(fams)-len(out):,} duplicates removed)")
    from collections import Counter
    print(f"  by relation: {dict(Counter(f['rel'] for f in out).most_common())}")
    print(f"  by view:     {dict(Counter(f['view'] for f in out).most_common())}")
    print(f"wrote {dst.name}")

    print()
    print("TOP 15 by Wilson lower bound")
    for f in out[:15]:
        print(f"  wlb {f['wlb']:.3f}  lift {f['lift']:5.2f}x  n={f['n']:>6,}  "
              f"-> {f['rel']:<13} [{f['view']}={f['sig'][:18]}]  {f['members']} biến thể")
        print(f"      {f['text'][:92]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
