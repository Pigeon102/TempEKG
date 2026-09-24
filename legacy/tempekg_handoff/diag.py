import re, collections, json

s = open('tempekg_finish.js', encoding='utf-8').read()
esc = collections.Counter(re.findall(r'\\u[0-9a-fA-F]{4}', s))
low = {k: v for k, v in esc.items() if int(k[2:], 16) < 32}
print('total uXXXX escapes:', sum(esc.values()))
print('LOW (<0x20) escapes:', low)
print('sample escapes:', dict(list(esc.items())[:10]))

p = json.load(open('recovered/payload.json', encoding='utf-8'))
parts = [p['FACTS'], p['RESEARCH_DIGEST']]
parts += list(p['DESIGNS_FULL'].values())
parts += list(p['DESIGNS_CONDENSED'].values())
parts += list(p['VERDICTS_DONE'].values())
blob = ''.join(parts)
bad = collections.Counter(ch for ch in blob
                          if (ord(ch) < 32 and ch not in '\n\t') or ord(ch) == 127
                          or 0x80 <= ord(ch) <= 0x9f or ord(ch) in (0x2028, 0x2029))
print('raw control/format chars inside recovered DATA:', {hex(ord(k)): v for k, v in bad.items()})
