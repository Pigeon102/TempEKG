"""Chuyen du lieu rockit wikidata sang dung format PaTeCon, dung CHINH logic
read_wikidata_csv() cua ho (read_datasets.py dong 60-82), roi cat con 5 cot
nhu pre_process() cua ho lam.
"""
import sys, os

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)

out = []
for line in open(src, encoding='utf-8', errors='ignore'):
    if 'sameAs' in line:
        continue
    post = line.strip().replace(' ', '').replace('pinstConf(', '').replace(')', '').replace('"', '')
    t = post.split(',')
    if len(t) < 5:
        continue
    # pre_process() cua ho: bo <>, giu 5 cot dau
    out.append('\t'.join(t[:5]))

open(dst, 'w', encoding='utf-8').write('\n'.join(out))
print('wrote %s : %d facts' % (dst, len(out)))
print('sample:')
for l in out[:3]:
    print('  ', l)
