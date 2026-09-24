"""Vi sao thuoc tinh node lam kieu class OOP — demo cu the.

Yeu cau: "thuoc tinh node lam theo kieu class cua OOP de minh co the de chinh thuoc tinh".
Day la kiem chung dieu do dung: THEM/SUA mot thuoc tinh = SUA MOT DONG.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecskg.schema import Node, Event, Attr, TimeX

print('='*68)
print('1. Rang buoc kieu tu dong')
print('='*68)
e = Event(nid='d1:E0', doc_id='d1', surface='attacked', etype='Attack')
print('  e.conf =', e.conf, '(default tu khai bao)')
e.conf = '0.8'
print('  gan chuoi "0.8" -> tu ep kieu:', repr(e.conf))
try:
    e.sent_id = 'khong phai so'
except TypeError as ex:
    print('  chan sai kieu:', ex)
try:
    Event(nid='x', mau_sac='do')
except AttributeError as ex:
    print('  chan thuoc tinh la:', str(ex)[:70], '...')

print()
print('='*68)
print('2. THEM mot thuoc tinh moi = MOT DONG')
print('='*68)
print("""  Vi du: muon them 'do tin cay lop lap lai' vao Event.
  Chi can them vao class Event trong schema.py:

      recurrence = Attr(str, default='UNKNOWN',
                        doc='PERIODIC / CONTINUOUS / ONE_OFF', index=True)

  Sau dong do, TU DONG co: default, ep kieu, chi muc tra cuu,
  serialize khi save, deserialize khi load, va mo ta trong schema().
  KHONG phai sua build(), save(), load(), hay ham validate nao.""")

# lam that
Event.recurrence = Attr(str, default='UNKNOWN',
                        doc='PERIODIC / CONTINUOUS / ONE_OFF', index=True)
Event.recurrence.__set_name__(Event, 'recurrence')
Event._attrs['recurrence'] = Event.recurrence

e2 = Event(nid='d1:E1', doc_id='d1', surface='ceremony', etype='Ceremony',
           recurrence='PERIODIC')
print('\n  vua them xong:')
print('   ', e2.as_dict())
print('    e.recurrence (node cu, lay default) =', e.recurrence)

print()
print('='*68)
print('3. Ke thua: sua Node la moi loai node deu doi')
print('='*68)
print('  Node co %d thuoc tinh; Event ke thua het + %d rieng'
      % (len(Node._attrs), len(Event._attrs)-len(Node._attrs)))
print('  rieng cua Event:', sorted(set(Event._attrs)-set(Node._attrs)))
print('  rieng cua TimeX:', sorted(set(TimeX._attrs)-set(Node._attrs)))

print()
print('='*68)
print('4. Bay moc thoi gian cua SEM quy ve (lo,hi) bang MOT phuong thuc')
print('='*68)
t = TimeX(nid='t1', doc_id='d1', surface='1947', eb=19470101, le=19471231, gran='year')
print('  interval bat dinh eb/le ->', t.bounds())
t2 = TimeX(nid='t2', doc_id='d1', surface='21 July 1947', stamp=19470721, gran='day')
print('  moc don stamp        ->', t2.bounds())
t3 = TimeX(nid='t3', doc_id='d1', surface='later', gran='unknown')
print('  thoi gian KY HIEU    ->', t3.bounds(), '| is_symbolic =', t3.is_symbolic())
print("""
  SEM co 7 thuoc tinh timestamp; ta khai bao du ca 7. UTime(lo,hi) cu la
  truong hop rieng. Thoi gian KY HIEU (chi biet thu tu, khong biet gia tri)
  duoc bieu dien tu nhien bang bounds() = None thay vi phai dat co rieng.""")
