import io

p = 'gen_handoff.py'
s = open(p, encoding='utf-8', newline='').read()
broken = "newline='\n'"          # a real newline got inserted by the bad patch
good = "newline=" + chr(92) + "'" + chr(92) + chr(110) + chr(92) + "'"
# build the correct replacement literally: newline='\n'  (backslash + n inside quotes)
good = "newline='" + chr(92) + "n'"
n = s.count(broken)
s = s.replace(broken, good)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('repaired sites:', n)

import py_compile
py_compile.compile(p, doraise=True)
print('gen_handoff.py compiles OK')
