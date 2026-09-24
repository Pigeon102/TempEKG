# -*- coding: utf-8 -*-
"""Step 2b (descriptive): when the textual / calendar cue that the definition points to is present,
which gold label does the pair actually carry?  Counts on TRAIN (all three splits) and on VALID
separately. Descriptive only -- no rule is selected here, so opening valid does not leak into Step 2c
(the valid column is reported, but no threshold or rule choice is made from it)."""
import gzip, io
from collections import Counter, defaultdict
from common import *

CUES = [
    # (edge type, name, required atoms, forbidden atoms, which label the definition predicts)
    ("TT", "range and its first date: CAL same_start, not equal", {"CAL:same_start"}, {"CAL:equal"}, "BEGINS-ON"),
    ("TT", "CAL same_start & A is the range", {"CAL:same_start", "CAL:A_range"}, {"CAL:equal"}, "BEGINS-ON"),
    ("TT", "CAL same_start & B is the range", {"CAL:same_start", "CAL:B_range"}, {"CAL:equal"}, "BEGINS-ON"),
    ("TT", "CAL same_end, not equal", {"CAL:same_end"}, {"CAL:equal"}, "(same end)"),
    ("TT", "CAL A_end_is_B_start (shared boundary)", {"CAL:A_end_is_B_start"}, set(), "ENDS-ON"),
    ("TT", "'from A to B' (head is the 'from' side)", {"PAT:FROMTO", "ORD:A1"}, set(), "ENDS-ON"),
    ("TT", "'from B to A' (head is the 'to' side)", {"PAT:FROMTO", "ORD:B1"}, set(), "ENDS-ON"),
    ("TT", "'between A and B' (head first)", {"PAT:BETWEENAND", "ORD:A1"}, set(), "ENDS-ON"),
    ("TT", "'A to/through/- B' same sentence, head first", {"PAT:XTOY", "ORD:A1"}, set(), "ENDS-ON"),
    ("TT", "'for DURATION' B + same sentence", {"PAT:FOR_DUR_B", "SD:0"}, set(), "BEGINS-ON"),
    ("ET", "event ... since/from TIMEX (same sentence)", {"PAT:SINCE_B"}, set(), "BEGINS-ON"),
    ("ET", "TIMEX preceded directly by 'since'", {"B.p1:since", "SD:0"}, set(), "BEGINS-ON"),
    ("ET", "TIMEX preceded directly by 'from'", {"B.p1:from", "SD:0"}, set(), "BEGINS-ON"),
    ("ET", "event ... until/till/through/by TIMEX", {"PAT:UNTIL_B"}, set(), "ENDS-ON"),
    ("ET", "TIMEX preceded directly by 'until'", {"B.p1:until", "SD:0"}, set(), "ENDS-ON"),
    ("ET", "event 'for DURATION' (same sentence)", {"PAT:FOR_DUR_B"}, set(), "BEGINS-ON"),
    ("ET", "'DURATION after' event", {"PAT:DUR_AFTER_B"}, set(), "BEGINS-ON"),
    ("ET", "event is a BEGIN verb, same sentence", {"A.tc:BEGIN", "SD:0"}, set(), "BEGINS-ON"),
    ("ET", "event is an END verb, same sentence", {"A.tc:END", "SD:0"}, set(), "ENDS-ON"),
    ("ET", "'from TIMEX to ...' TIMEX is from-side", {"PAT:FROMTO", "ORD:B1"}, set(), "BEGINS-ON"),
    ("ET", "'from ... to TIMEX' TIMEX is to-side", {"PAT:FROMTO", "ORD:A1"}, set(), "ENDS-ON"),
    ("TE", "TIMEX ... until event", {"PAT:UNTIL_A"}, set(), "ENDS-ON"),
    ("EE", "head is a BEGIN verb, same sentence", {"A.tc:BEGIN", "SD:0"}, set(), "BEGINS-ON"),
    ("EE", "tail is a BEGIN verb, same sentence", {"B.tc:BEGIN", "SD:0"}, set(), "BEGINS-ON"),
    ("EE", "head is an END verb, same sentence", {"A.tc:END", "SD:0"}, set(), "ENDS-ON"),
    ("EE", "'since' between, same sentence", {"BW:since"}, set(), "BEGINS-ON"),
    ("EE", "'until' between, same sentence", {"BW:until"}, set(), "ENDS-ON"),
    ("EE", "'when' between, same sentence", {"BW:when"}, set(), "BEGINS-ON/ENDS-ON"),
    ("EE", "'as soon as' (soon between)", {"BW:soon"}, set(), "BEGINS-ON"),
]

cnt = defaultdict(Counter)
docs = defaultdict(set)
with gzip.open(OUT / "features.tsv.gz", "rt", encoding="utf-8") as f:
    for l in f:
        sp, doc, s, t, et, g, at = l.rstrip("\n").split("\t")
        A = set(at.split("|"))
        part = "valid" if sp == "3" else "train"
        for i, (cet, name, req, forb, pred) in enumerate(CUES):
            if et == cet and req <= A and not (forb & A):
                cnt[(i, part)][g] += 1
                if g in RARE: docs[(i, part, g)].add(doc)

L = io.open(OUT / "logs" / "s04_cue_tables.log", "w", encoding="utf-8")
def P(s=""):
    print(s); L.write(s + "\n")
P("Gold label distribution when a definition-derived cue is present (train = all 3 train splits)")
P("%-3s %-52s %-9s | %6s %6s %6s %6s %6s %6s %6s | BO docs EO docs" % ("ET", "cue", "part", "n", "BEF", "CONT", "SIM", "OVL", "BO", "EO"))
for i, (cet, name, req, forb, pred) in enumerate(CUES):
    for part in ("train", "valid"):
        c = cnt[(i, part)]; n = sum(c.values())
        P("%-3s %-52s %-9s | %6d %6d %6d %6d %6d %6d %6d | %3d %3d" % (
            cet, name[:52], part, n, c["BEFORE"], c["CONTAINS"], c["SIMULTANEOUS"], c["OVERLAP"], c["BEGINS-ON"], c["ENDS-ON"],
            len(docs[(i, part, "BEGINS-ON")]), len(docs[(i, part, "ENDS-ON")])))
    P("    definition predicts: %s" % pred)
