# -*- coding: utf-8 -*-
"""Step 2a: definition-driven, label-free features for EVERY target edge (train + valid).

Nothing here reads a gold temporal label except to copy the edge's own label into the output
column 'gold' (used only as the mining target). No neighbouring edge label is read.

Atoms (all scoped later by edge type; A = head = stored s, B = tail = stored t):
  ORD:A1 / ORD:B1            which mention comes first in the text (closest mention pair)
  SD:0 / SD:1 / SD:2-3 / SD:4+   sentence distance;  TG:<bucket> token gap when same sentence
  X.tt:<type>  X.sh:<shape>  X.dur  (TIMEX type, surface shape, duration-like)       X in {A,B}
  X.et:<event type>  X.tw:<trigger lower>  X.tc:<BEGIN|END|DUR|none>  (event side)
  X.p1:<word before>  X.p2:<2 words before>  X.n1:<word after>
  BW:<word>                  each word between the two mentions (same sentence, gap <= 8)
  PAT:FROMTO / PAT:BETWEENAND / PAT:SINCE / PAT:UNTIL / PAT:FOR_DUR / PAT:DUR_AFTER / PAT:RANGE_A/B
  CAL:<relation>             calendar comparison of the two TIMEX strings (TIMEX-TIMEX only)
Output: features.tsv.gz  columns split, doc, s, t, etype, gold, atoms('|'-joined)
"""
import io, re, gzip, time
from common import *

T0 = time.time()
BEGIN_W = re.compile(r"^(begin|began|begun|beginning|begins|start|started|starting|starts|launch\w*|open\w*|found(ed|ing)?|establish\w*|commenc\w*|initiat\w*|inaugurat\w*|creat\w*|form(ed|ation)?|outbreak|onset|broke|erupt\w*|develop\w*|emerg\w*|introduc\w*|debut\w*|premier\w*|kick\w*)$")
END_W = re.compile(r"^(end|ended|ending|ends|finish\w*|conclu\w*|terminat\w*|clos\w*|ceas\w*|dissolv\w*|dissolution|dissipat\w*|abolish\w*|surrender\w*|disband\w*|expir\w*|culminat\w*|halt\w*|stop\w*|lift\w*|withdr\w*|retir\w*|died|death|collaps\w*|over)$")
DUR_W = re.compile(r"^(last\w*|continu\w*|remain\w*|span\w*|run|ran|running|persist\w*|stay\w*|rul\w*|reign\w*|serv\w*|lived|occup\w*|war|wars|campaign|period|season|era|tour|festival|siege|rebellion|conflict|struggle|revolution|dynasty|held|took)$")
MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"])}
MONTHS.update({m[:3]: v for m, v in list(MONTHS.items())})
MONTHS["sept"] = 9
NUMW = r"(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty|hundred|several|few|many|some|nearly|about|almost|over|the next|the following|the previous|the past|the last|more)"
UNIT = r"(second|minute|hour|day|night|week|month|year|decade|centur)"
DASH = r"[–—\-~]|to"


def tok_norm(w):
    return w.lower()


def shape(text):
    t = text.strip().lower()
    if re.search(r"\d{1,2}:\d{2}|utc|gmt|\ba\.?m\b|\bp\.?m\b|o'clock|noon|midnight", t): return "TIME"
    if re.match(r"^\d{3,4}s$|^the \d{3,4}s$|centur", t) or re.search(r"\b\d{3,4}s\b", t): return "DECADE_CENT"
    if re.match(r"^\d{1,4}\s*(" + DASH + r")\s*\d{1,4}( (bc|bce|ad|ce))?$", t): return "YEAR_RANGE"
    if re.search(r"\d\s*[–—\-]\s*\d", t) and any(m in t for m in MONTHS): return "DAY_RANGE"
    if re.match(r"^\d{3,4}( (bc|bce|ad|ce))?$", t) or re.match(r"^(ad|ce) \d{1,4}$", t): return "YEAR"
    if re.match(r"^\d{1,2}$", t): return "BARE_NUM"
    has_m = any(re.search(r"\b" + m + r"\b", t) for m in MONTHS)
    has_y = re.search(r"\b\d{3,4}\b", t) is not None
    has_d = re.search(r"\b\d{1,2}(st|nd|rd|th)?\b", t) is not None
    if has_m and has_y and has_d: return "FULL_DATE"
    if has_m and has_y: return "MONTH_YEAR"
    if has_m and has_d: return "DAY_MONTH"
    if has_m: return "MONTH"
    if re.search(r"\b" + UNIT, t) and re.search(r"\b" + NUMW + r"\b|-(day|year|week|month|hour)", t):
        if re.search(r"\b(later|after|ago|before|earlier|previous|following|next|past|last)\b", t): return "REL_QTY"
        return "QTY"
    if re.match(r"^(the |that |this |same |its )", t) or re.search(r"\b(same|following|previous|next|time|then|now|today|yesterday)\b", t): return "RELATIVE"
    if has_y: return "HAS_YEAR"
    return "OTHER"


def ymd(y, m=None, d=None, bc=False):
    y = -y if bc else y
    return (y, m, d)


def parse_cal(text):
    """-> (start, end) with start/end = (year|None, month|None, day|None) at their granularity, or None."""
    t = text.strip().lower().replace(",", " ")
    t = re.sub(r"\s+", " ", t)
    bc = bool(re.search(r"\b(bc|bce)\b", t))
    m = re.match(r"^(\d{3,4})\s*(?:[–—\-~]|to)\s*(\d{1,4})(?: (?:bc|bce|ad|ce))?$", t)
    if m:
        y1 = int(m.group(1)); y2s = m.group(2)
        y2 = int(y2s) if len(y2s) >= 3 else int(str(y1)[:len(str(y1)) - len(y2s)] + y2s)
        if bc: y1, y2 = -y1, -y2
        return ((y1, None, None), (y2, None, None))
    m = re.match(r"^(\d{3,4})( (?:bc|bce|ad|ce))?$", t)
    if m:
        y = int(m.group(1)); y = -y if bc else y
        return ((y, None, None), (y, None, None))
    m = re.match(r"^(?:the )?(\d{3})0s$", t)
    if m:
        y = int(m.group(1)) * 10
        return ((y, None, None), (y + 9, None, None))
    yr = re.search(r"\b(\d{3,4})\b", t)
    y = int(yr.group(1)) if yr else None
    if y is not None and bc: y = -y
    mons = [(mm.start(), MONTHS[mm.group(1)]) for mm in re.finditer(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b", t)]
    days = [int(x) for x in re.findall(r"\b(\d{1,2})(?:st|nd|rd|th)?\b", t)]
    if not mons:
        return None
    if len(mons) >= 2:        # "february 20 - february 23 1651", "march through may"
        d1 = days[0] if days else None; d2 = days[1] if len(days) > 1 else None
        return ((y, mons[0][1], d1), (y, mons[-1][1], d2))
    mo = mons[0][1]
    if len(days) >= 2 and re.search(r"\d\s*[–—\-]\s*\d", t):   # "26-28 april 1922"
        return ((y, mo, days[0]), (y, mo, days[1]))
    if days:
        return ((y, mo, days[0]), (y, mo, days[0]))
    return ((y, mo, None), (y, mo, None))


def lo(p):   # lowest point of a partial date
    return (p[0], p[1] or 1, p[2] or 1)


def hi(p):
    return (p[0], p[1] or 12, p[2] or 31)


def unit(p):  # coarsest granularity label
    return "Y" if p[1] is None else ("M" if p[2] is None else "D")


def cal_atoms(ta, tb):
    A = parse_cal(ta); B = parse_cal(tb)
    if A is None or B is None:
        return ["CAL:unparsed"]
    (as_, ae), (bs, be) = A, B
    # inherit a missing year from the other side
    def fill(p, q):
        return (p[0] if p[0] is not None else q[0], p[1], p[2])
    ref = next((x for x in (as_, ae, bs, be) if x[0] is not None), None)
    if ref is None:
        ref = (2000, None, None)
    as_, ae, bs, be = [fill(x, ref) for x in (as_, ae, bs, be)]
    out = []
    aS, aE, bS, bE = lo(as_), hi(ae), lo(bs), hi(be)
    if aS == bS: out.append("CAL:same_start")
    if aE == bE: out.append("CAL:same_end")
    if aS == bS and aE == bE: out.append("CAL:equal")
    if aE < bS: out.append("CAL:A_before_B")
    if bE < aS: out.append("CAL:B_before_A")
    if aS <= bS and bE <= aE and not (aS == bS and aE == bE): out.append("CAL:A_contains_B")
    if bS <= aS and aE <= bE and not (aS == bS and aE == bE): out.append("CAL:B_contains_A")
    # shared boundary unit: A's end unit == B's start unit (e.g. 1810-1814 / 1814-1817)
    if ae[:{"Y": 1, "M": 2, "D": 3}[unit(ae)]] == bs[:{"Y": 1, "M": 2, "D": 3}[unit(bs)]] and aS < bS:
        out.append("CAL:A_end_is_B_start")
    if be[:{"Y": 1, "M": 2, "D": 3}[unit(be)]] == as_[:{"Y": 1, "M": 2, "D": 3}[unit(as_)]] and bS < aS:
        out.append("CAL:B_end_is_A_start")
    if A[0] != A[1]: out.append("CAL:A_range")
    if B[0] != B[1]: out.append("CAL:B_range")
    if not out: out.append("CAL:overlap_other")
    return out


def event_class(w):
    w = w.lower().split()[0] if w.strip() else w
    if BEGIN_W.match(w): return "BEGIN"
    if END_W.match(w): return "END"
    if DUR_W.match(w): return "DUR"
    return "none"


def side_atoms(X, node, men, toks):
    sid, st, en, _ = men
    sent = toks[sid]
    p1 = tok_norm(sent[st - 1]) if st >= 1 else "<s>"
    p2 = (tok_norm(sent[st - 2]) if st >= 2 else "<s>") + "_" + p1
    n1 = tok_norm(sent[en]) if en < len(sent) else "</s>"
    out = [X + ".p1:" + p1, X + ".p2:" + p2, X + ".n1:" + n1]
    if node["kind"] == "event":
        tw = " ".join(sent[st:en]).lower()
        out += [X + ".et:" + node["type"], X + ".tw:" + tw, X + ".tc:" + event_class(tw)]
    else:
        tt = node.get("timex_type", "?")
        sh = shape(node.get("text", ""))
        out += [X + ".tt:" + tt, X + ".sh:" + sh]
        if tt == "DURATION" or sh in ("QTY", "REL_QTY"): out.append(X + ".dur")
    return out


def edge_atoms(na, nb, ma_list, mb_list, toks):
    best = None
    for a in ma_list:
        for b in mb_list:
            key = (abs(a[0] - b[0]), abs(a[1] - b[1]) if a[0] == b[0] else 0)
            if best is None or key < best[0]:
                best = (key, a, b)
    _, a, b = best
    out = []
    sd = abs(a[0] - b[0])
    out.append("SD:" + ("0" if sd == 0 else "1" if sd == 1 else "2-3" if sd <= 3 else "4+"))
    a_first = (a[0], a[1]) < (b[0], b[1])
    out.append("ORD:A1" if a_first else "ORD:B1")
    out += side_atoms("A", na, a, toks) + side_atoms("B", nb, b, toks)
    if sd == 0:
        f, s = (a, b) if a_first else (b, a)
        gap = s[1] - f[2]
        out.append("TG:" + ("<=0" if gap <= 0 else "1" if gap == 1 else "2-3" if gap <= 3 else "4-8" if gap <= 8 else "9+"))
        sent = [tok_norm(w) for w in toks[a[0]]]
        between = sent[f[2]:s[1]] if gap > 0 else []
        if 0 < gap <= 8:
            for w in set(between):
                out.append("BW:" + w)
        pre_f = sent[max(0, f[1] - 3):f[1]]
        pre_s = sent[max(0, s[1] - 2):s[1]]
        if "from" in pre_f and gap <= 8 and any(w in ("to", "through", "until", "till", "–", "-", "thru") for w in between):
            out.append("PAT:FROMTO")
        if "between" in pre_f and gap <= 8 and "and" in between:
            out.append("PAT:BETWEENAND")
        if gap <= 12 and any(w in ("to", "through", "until", "till", "–", "-") for w in between) and not "from" in pre_f:
            out.append("PAT:XTOY")
        if re.search(r"(commenc|began|begun|start|initiat|opened)", " ".join(between)) or \
           re.search(r"(conclud|ended|finish|until|ending)", " ".join(between)):
            out.append("PAT:ASPECT_BETWEEN")
        # event / timex specific constructions, stated from the TIMEX side
        for X, node, m in (("A", na, a), ("B", nb, b)):
            if node["kind"] != "timex": continue
            pre = sent[max(0, m[1] - 3):m[1]]
            post = sent[m[2]:m[2] + 2]
            if any(w in ("since", "from", "starting", "beginning", "began", "begun") for w in pre): out.append("PAT:SINCE_" + X)
            if any(w in ("until", "till", "til", "through", "by", "to", "ended", "ending") for w in pre): out.append("PAT:UNTIL_" + X)
            if "for" in pre and (node.get("timex_type") == "DURATION" or shape(node.get("text", "")) in ("QTY",)): out.append("PAT:FOR_DUR_" + X)
            if any(w in ("after", "later", "since") for w in post): out.append("PAT:DUR_AFTER_" + X)
            if any(w in ("before", "earlier", "ago") for w in post): out.append("PAT:DUR_BEFORE_" + X)
    if na["kind"] == "timex" and nb["kind"] == "timex":
        out += cal_atoms(na.get("text", ""), nb.get("text", ""))
    return out


n_out = 0
with gzip.open(OUT / "features.tsv.gz", "wt", encoding="utf-8") as fo:
    for split in ("train", "valid"):
        raw_it = iter_raw(split)
        rawd = {}
        for rec in iter_kg(split):
            doc = rec["doc_id"]
            while doc not in rawd:
                r = next(raw_it)
                rawd = {r["id"]: r}
            r = rawd[doc]
            toks = r["tokens"]
            M = {}
            for ev in r["events"]:
                M[ev["id"]] = [(mm["sent_id"], mm["offset"][0], mm["offset"][1], mm["trigger_word"]) for mm in ev["mention"]]
            for tx in r["TIMEX"]:
                M[tx["id"]] = [(tx["sent_id"], tx["offset"][0], tx["offset"][1], tx["mention"])]
            nd = rec["nodes"]
            sp = split_of(doc) if split == "train" else 3
            for e in rec["target_edges"]:
                na, nb = nd.get(e["s"]), nd.get(e["t"])
                if not na or not nb: continue
                at = edge_atoms(na, nb, M[e["s"]], M[e["t"]], toks)
                at = sorted(set(a.replace("|", "/").replace("\t", " ") for a in at))
                fo.write("%d\t%s\t%s\t%s\t%s\t%s\t%s\n" % (sp, doc, e["s"], e["t"], etype_of(na, nb), e["rel"], "|".join(at)))
                n_out += 1
        print("[%5.0fs] %s done, %d edges so far" % (time.time() - T0, split, n_out), flush=True)
print("edges written:", n_out)
