"""EXP11 - Tan cong nut that DO PHU bang entity linking.

EXP9: 80-89% cap roi xuong majority vi C1 khong cham toi.
EXP7: 37.5% event co ZERO linked entity; 60% argument la span chua link.

Y tuong: link 60% span chua gan bang khop chuoi TRONG document:
  - neu chuoi chuan hoa trung mot mention cua entity co san -> gan vao entity do
  - neu khong -> tao pseudo-entity theo chuoi chuan hoa (cac span giong nhau gop lai)

Do: bac event truoc/sau, so cap dong-tham-du truoc/sau, va do phu C1 tang bao nhieu.
"""
import json, zipfile, io, collections, re

STOP = re.compile(r'^(the|a|an|his|her|its|their|our|this|that|these|those)\s+', re.I)


def norm(s):
    s = s.strip().lower()
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    prev = None
    while prev != s:
        prev = s
        s = STOP.sub('', s)
    return s


z = zipfile.ZipFile('MAVEN-Arg.zip')
before_arity, after_arity = [], []
before_pairs = after_pairs = 0
before_zero = after_zero = 0
n_span = n_linked_to_entity = n_pseudo = 0
tot_ev = 0

for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)

            # chuoi chuan hoa -> entity_id (tu cac mention co san)
            surf2ent = {}
            for en in d['entities']:
                for m in en['mention']:
                    k = norm(m['mention'])
                    if k:
                        surf2ent.setdefault(k, en['id'])

            ev_before, ev_after = {}, {}
            for e in d['events']:
                tot_ev += 1
                linked, extended = set(), set()
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            linked.add(v['entity_id'])
                            extended.add(v['entity_id'])
                        else:
                            n_span += 1
                            k = norm(v.get('content', ''))
                            if not k:
                                continue
                            if k in surf2ent:
                                extended.add(surf2ent[k])
                                n_linked_to_entity += 1
                            else:
                                extended.add('PSEUDO::' + k)
                                n_pseudo += 1
                ev_before[e['id']] = linked
                ev_after[e['id']] = extended
                before_arity.append(len(linked))
                after_arity.append(len(extended))
                before_zero += (len(linked) == 0)
                after_zero += (len(extended) == 0)

            for store, acc in ((ev_before, 'b'), (ev_after, 'a')):
                ids = [i for i in store if store[i]]
                cnt = 0
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        if store[ids[i]] & store[ids[j]]:
                            cnt += 1
                if acc == 'b':
                    before_pairs += cnt
                else:
                    after_pairs += cnt

import statistics
print('tong event: %d' % tot_ev)
print()
print('%-28s %12s %12s %10s' % ('', 'TRUOC', 'SAU', 'thay doi'))
print('-' * 66)
print('%-28s %12.2f %12.2f %9.0f%%'
      % ('bac trung binh', statistics.mean(before_arity), statistics.mean(after_arity),
         100*(statistics.mean(after_arity)/statistics.mean(before_arity)-1)))
print('%-28s %12d %12d %9.0f%%'
      % ('event bac 0', before_zero, after_zero, 100*(after_zero/before_zero-1)))
print('%-28s %11.1f%% %11.1f%%' % ('  ty le bac 0', 100*before_zero/tot_ev, 100*after_zero/tot_ev))
print('%-28s %12d %12d %9.0f%%'
      % ('cap dong-tham-du', before_pairs, after_pairs,
         100*(after_pairs/before_pairs-1)))
print()
print('span chua link           : %d' % n_span)
print('  -> khop entity co san  : %d (%.1f%%)' % (n_linked_to_entity, 100*n_linked_to_entity/n_span))
print('  -> tao pseudo-entity   : %d (%.1f%%)' % (n_pseudo, 100*n_pseudo/n_span))
