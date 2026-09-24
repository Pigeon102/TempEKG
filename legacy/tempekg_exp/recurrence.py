"""Xu ly SU KIEN LAP LAI dung cach — thay nguong tho ">=3 nam".

Van de (nguoi dung chi ra): hop thuong nien, giai dau hang nam -> cung entity, cung loai
event, thoi gian khac nhau, KHONG phai loi. PaTeCon gan co het.

Do duoc (EXP21): 487 ung vien mutual exclusion tren MAVEN, 58.3% cach >=3 nam.
Nguong tho 3 nam chua phan biet duoc 3 truong hop:
   - LAP LAI DINH KY   : cac lan cach DEU nhau        (hop le)
   - KEO DAI           : mot su viec trai dai nhieu nam (hop le)
   - LOI               : hai gia tri cho cung mot lan  (sai)

Day chinh la future work PaTeCon tuyen bo (§8): "predicates can be broadened to encompass
quantitative relationships, such as t2 - t1 <= 10 years".
"""
import statistics


def classify(years, min_gap_by_type=None, event_type=None):
    """Phan loai mot chuoi nam ma mot entity xuat hien voi CUNG mot loai event.

    Tra ve (nhan, ly_do).
    """
    ys = sorted(set(years))
    if len(ys) < 2:
        return 'SINGLE', 'chi mot moc'

    gaps = [ys[i+1] - ys[i] for i in range(len(ys)-1)]
    span = ys[-1] - ys[0]

    # 1. LOI tiem tang: tat ca cung nam (khac ngay/thang) -> nghi ngo
    if span == 0:
        return 'SUSPECT', 'cung nam, khac gia tri'

    # 2. DINH KY: >=3 moc va khoang cach deu nhau
    if len(ys) >= 3:
        if len(set(gaps)) == 1:
            return 'PERIODIC', 'cach deu %d nam' % gaps[0]
        if statistics.pstdev(gaps) <= 0.5 and statistics.mean(gaps) >= 1:
            return 'PERIODIC', 'gan deu (TB %.1f nam, do lech %.1f)' % (
                statistics.mean(gaps), statistics.pstdev(gaps))

    # 3. KEO DAI: cac moc lien tiep (cach 1 nam), lien tuc
    if all(g == 1 for g in gaps) and len(ys) >= 2:
        return 'CONTINUOUS', 'lien tiep %d nam (%d-%d)' % (len(ys), ys[0], ys[-1])

    # 4. nguong theo LOAI EVENT (hoc tu du lieu) thay cho nguong chung
    thr = (min_gap_by_type or {}).get(event_type)
    if thr is not None:
        if min(gaps) >= thr:
            return 'RECURRING', 'khoang cach nho nhat %d >= nguong hoc duoc %d' % (min(gaps), thr)
        return 'SUSPECT', 'khoang cach %d < nguong hoc duoc %d' % (min(gaps), thr)

    # 5. mac dinh: cach xa -> lap lai
    if min(gaps) >= 3:
        return 'RECURRING', 'cach nhau >=3 nam'
    return 'SUSPECT', 'cach gan (%s nam)' % gaps


def learn_thresholds(samples, quantile=0.10):
    """Hoc nguong khoang-cach-toi-thieu RIENG cho tung loai event.

    samples: list of (event_type, [years])
    Y tuong: voi loai event lap lai binh thuong (Competition), phan lon khoang cach lon.
    Lay phan vi thap lam nguong: duoi nguong do thi dang ngo.
    """
    by = {}
    for typ, years in samples:
        ys = sorted(set(years))
        if len(ys) < 2:
            continue
        gaps = [ys[i+1]-ys[i] for i in range(len(ys)-1)]
        by.setdefault(typ, []).extend(gaps)
    out = {}
    for typ, gs in by.items():
        if len(gs) < 5:
            continue
        gs = sorted(gs)
        idx = max(0, int(quantile * len(gs)) - 1)
        out[typ] = gs[idx]
    return out
