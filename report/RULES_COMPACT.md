# Bộ luật EV–EV gọn: 378 luật, cùng dự đoán với 54.719 luật

Sinh tự động bởi `experiments/rules_full/compact_listing.py` từ `src/artifacts/rules_compact.json`.
Cách rút gọn và chứng minh: `RULESET.md` mục 12. Mỗi họ = cùng nhãn, cùng dạng và thuộc tính điều kiện,
khác giá trị. Cột *lớp* là view và lớp nơi luật áp dụng; `k/n` trên DISCOVERY, `ck/cn` trên
CONFIRMATION-1; ★ = cũng nằm trong bộ 279 luật (biến thể B).

## CONTAINS — 276 luật, 136 họ

### EQ(type_pair) (23)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = rev | type_pair = (Catastrophe, Motion_directional) | 11/32 | 12/12 | 0.758 |
| ★ | global = * | type_pair = (Catastrophe, Achieve) | 14/32 | 21/24 | 0.690 |
| ★ | anchor = False | type_pair = (Military_operation, Motion_directional) | 19/47 | 12/13 | 0.667 |
| ★ | global = * | type_pair = (Competition, Action) | 15/44 | 10/11 | 0.623 |
| ★ | sdist = 2-3 | type_pair = (Catastrophe, Coming_to_be) | 19/55 | 15/18 | 0.608 |
| ★ | order = rev | type_pair = (Catastrophe, Arriving) | 15/40 | 12/14 | 0.601 |
| ★ | bucket_a = lead | type_pair = (Traveling, Social_event) | 39/51 | 9/10 | 0.596 |
| ★ | anchor = False | type_pair = (Catastrophe, Temporary_stay) | 10/31 | 9/10 | 0.596 |
| ★ | global = * | type_pair = (Military_operation, Defending) | 25/75 | 19/24 | 0.595 |
| ★ | order = rev | type_pair = (Catastrophe, Damaging) | 19/60 | 11/13 | 0.578 |
| ★ | global = * | type_pair = (Military_operation, Hostile_encounter) | 180/292 | 61/92 | 0.562 |
| ★ | sdist = 4-7 | type_pair = (Catastrophe, Becoming) | 41/97 | 22/30 | 0.556 |
| ★ | anchor_sd = (False, '0') | type_pair = (Hostile_encounter, Hostile_encounter) | 23/34 | 10/12 | 0.552 |
|  | anchor_sd = (False, '8+') | type_pair = (Military_operation, Escaping) | 29/53 | 13/17 | 0.527 |
| ★ | anchor = False | type_pair = (Military_operation, Process_start) | 17/40 | 13/17 | 0.527 |
| ★ | anchor = True | type_pair = (Catastrophe, Coming_to_be) | 17/47 | 13/17 | 0.527 |
| ★ | sdist = 8+ | type_pair = (Military_operation, Motion) | 23/49 | 11/14 | 0.524 |
| ★ | order = fwd | type_pair = (Military_operation, Arranging) | 23/57 | 9/11 | 0.523 |
|  | sdist = 0 | type_pair = (Competition, Conquering) | 25/38 | 14/19 | 0.512 |
| ★ | order = rev | type_pair = (Catastrophe, Motion) | 25/68 | 14/19 | 0.512 |
| ★ | sdist = 8+ | type_pair = (Military_operation, Attack) | 55/123 | 17/24 | 0.508 |
| ★ | order = fwd | type_pair = (Military_operation, Process_start) | 19/47 | 15/21 | 0.500 |
| ★ | global = * | type_pair = (Military_operation, Arriving) | 43/123 | 18/26 | 0.500 |

### EQ(type_b) ∧ HAS(roleset_a) (11)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | roleset_a ∋ Loss ∧ type_b = Arriving | 52/67 | 26/32 | 0.647 |
| ★ | anchor = True | roleset_a ∋ Host ∧ type_b = Defending | 29/43 | 14/16 | 0.640 |
| ★ | bucket_a = lead | roleset_a ∋ Loss ∧ type_b = Motion_directional | 30/49 | 25/33 | 0.590 |
| ★ | anchor = True | roleset_a ∋ Loss ∧ type_b = Motion_directional | 21/39 | 24/32 | 0.579 |
|  | bucket_a = lead | roleset_a ∋ Participant ∧ type_b = Hold | 33/58 | 11/13 | 0.578 |
| ★ | bucket_a = late | roleset_a ∋ Loss ∧ type_b = Cause_change_of_strength | 25/50 | 13/16 | 0.570 |
| ★ | order = rev | roleset_a ∋ Loss ∧ type_b = Cause_change_of_strength | 34/58 | 13/16 | 0.570 |
|  | anchor_sd = (True, '4-7') | roleset_a ∋ Host ∧ type_b = Conquering | 23/31 | 10/12 | 0.552 |
| ★ | global = * | roleset_a ∋ Winner ∧ type_b = Defending | 26/35 | 11/14 | 0.524 |
| ★ | sdist = 0 | roleset_a ∋ Host ∧ type_b = Conquering | 23/32 | 9/11 | 0.523 |
|  | bucket_a = lead | roleset_a ∋ Loss ∧ type_b = Self_motion | 38/53 | 15/21 | 0.500 |

### EQ(bucket_b) ∧ EQ(type_a) (10)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 2-3 | bucket_b = early ∧ type_a = Military_operation | 80/165 | 42/51 | 0.697 |
| ★ | sdist = 1 | bucket_b = early ∧ type_a = Military_operation | 112/237 | 59/80 | 0.632 |
| ★ | order = fwd | type_a = Hostile_encounter ∧ bucket_b = early | 462/831 | 183/284 | 0.587 |
| ★ | order = fwd | bucket_b = early ∧ type_a = Competition | 206/362 | 73/108 | 0.583 |
| ★ | sdist = 2-3 | bucket_b = early ∧ type_a = Hostile_encounter | 238/472 | 103/168 | 0.538 |
| ★ | anchor_sd = (False, '4-7') | bucket_b = mid ∧ type_a = Hostile_encounter | 709/1502 | 279/489 | 0.526 |
| ★ | anchor = False | type_a = Catastrophe ∧ bucket_b = early | 292/670 | 157/275 | 0.512 |
| ★ | sdist_ord = ('4-7', 'fwd') | bucket_b = mid ∧ type_a = Hostile_encounter | 947/2066 | 405/745 | 0.508 |
| ★ | sdist = 2-3 | bucket_b = early ∧ type_a = Catastrophe | 139/281 | 78/133 | 0.501 |
| ★ | sdist = 1 | bucket_b = early ∧ type_a = Catastrophe | 145/339 | 91/157 | 0.501 |

### HAS(anchor_roles) ∧ HAS(roleset_a) (10)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | roleset_a ∋ Name ∧ anchor_roles ∋ (Loser, Patient) | 25/29 | 10/11 | 0.623 |
|  | sdist = 8+ | anchor_roles ∋ (Location, Location) ∧ roleset_a ∋ Loser | 24/69 | 22/28 | 0.605 |
|  | global = * | roleset_a ∋ Winner ∧ anchor_roles ∋ (Loser, Agent) | 53/95 | 15/19 | 0.567 |
|  | global = * | roleset_a ∋ Name ∧ anchor_roles ∋ (Loser, Agent) | 63/101 | 15/20 | 0.531 |
|  | global = * | roleset_a ∋ Name ∧ anchor_roles ∋ (Location, Host) | 33/66 | 57/90 | 0.530 |
| ★ | order = fwd | anchor_roles ∋ (Location, Location) ∧ roleset_a ∋ Event | 560/963 | 228/400 | 0.521 |
| ★ | global = * | roleset_a ∋ Participant ∧ anchor_roles ∋ (Location, Host) | 33/62 | 49/78 | 0.517 |
| ★ | sdist = 4-7 | anchor_roles ∋ (Location, Location) ∧ roleset_a ∋ Event | 230/409 | 113/194 | 0.512 |
| ★ | sdist_ord = ('8+', 'fwd') | anchor_roles ∋ (Location, Location) ∧ roleset_a ∋ Host | 138/271 | 40/63 | 0.511 |
| ★ | global = * | roleset_a ∋ Host ∧ anchor_roles ∋ (Agent, Winner) | 73/117 | 35/55 | 0.504 |

### HAS(anchor_roles) (9)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = fwd | anchor_roles ∋ (Loser, Agent) | 48/94 | 13/15 | 0.621 |
|  | bucket_a = lead | anchor_roles ∋ (Agent, Winner) | 62/79 | 23/29 | 0.616 |
| ★ | order = fwd | anchor_roles ∋ (Location, Host) | 39/98 | 41/56 | 0.604 |
|  | sdist_ord = ('4-7', 'fwd') | anchor_roles ∋ (Participant, Patient) | 29/45 | 13/16 | 0.570 |
|  | sdist = 4-7 | anchor_roles ∋ (Location, Host) | 21/50 | 28/39 | 0.562 |
|  | global = * | anchor_roles ∋ (Participant, Loser) | 25/61 | 16/21 | 0.549 |
| ★ | order = fwd | anchor_roles ∋ (Host, Location) | 43/113 | 32/47 | 0.538 |
| ★ | global = * | anchor_roles ∋ (Score, Score) | 61/136 | 22/31 | 0.534 |
| ★ | sdist_ord = ('4-7', 'fwd') | anchor_roles ∋ (Host, Host) | 72/212 | 53/85 | 0.517 |

### EQ(bucket_b) ∧ EQ(type_pair) (7)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | bucket_b = early ∧ type_pair = (Military_operation, Attack) | 37/51 | 15/16 | 0.717 |
|  | global = * | bucket_b = early ∧ type_pair = (Catastrophe, Motion) | 35/64 | 35/42 | 0.694 |
| ★ | sdist = 4-7 | bucket_b = mid ∧ type_pair = (Hostile_encounter, Bodily_harm) | 19/46 | 10/12 | 0.552 |
| ★ | sdist = 4-7 | bucket_b = mid ∧ type_pair = (Catastrophe, Motion) | 69/121 | 40/59 | 0.551 |
| ★ | anchor_sd = (True, '4-7') | bucket_b = mid ∧ type_pair = (Competition, Competition) | 73/151 | 48/75 | 0.527 |
| ★ | sdist = 4-7 | bucket_b = mid ∧ type_pair = (Hostile_encounter, Attack) | 94/155 | 21/30 | 0.521 |
|  | global = * | bucket_b = early ∧ type_pair = (Catastrophe, Becoming) | 18/27 | 12/16 | 0.505 |

### EQ(bucket_a) ∧ HAS(roleset_a) (7)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = fwd | bucket_a = lead ∧ roleset_a ∋ Winner | 530/917 | 194/264 | 0.679 |
| ★ | anchor = True | bucket_a = lead ∧ roleset_a ∋ Participant | 387/765 | 127/177 | 0.647 |
| ★ | sdist_ord = ('2-3', 'fwd') | bucket_a = lead ∧ roleset_a ∋ Host | 159/309 | 65/89 | 0.630 |
| ★ | sdist_ord = ('4-7', 'fwd') | bucket_a = lead ∧ roleset_a ∋ Participant | 214/442 | 76/112 | 0.587 |
| ★ | anchor = True | bucket_a = lead ∧ roleset_a ∋ Host | 532/1050 | 217/341 | 0.584 |
| ★ | sdist_ord = ('4-7', 'fwd') | bucket_a = lead ∧ roleset_a ∋ Host | 331/628 | 127/201 | 0.563 |
| ★ | sdist_ord = ('2-3', 'fwd') | bucket_a = lead ∧ roleset_a ∋ Loss | 220/398 | 110/190 | 0.508 |

### CNT(anchor_roles) ∧ HAS(roleset_a) (6)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('8+', 'rev') | |anchor_roles| = 2 ∧ roleset_a ∋ Loss | 16/36 | 12/12 | 0.758 |
|  | sdist = 8+ | |anchor_roles| = 3 ∧ roleset_a ∋ Score | 20/28 | 10/11 | 0.623 |
| ★ | sdist_ord = ('4-7', 'fwd') | |anchor_roles| = 2 ∧ roleset_a ∋ Participant | 162/298 | 65/103 | 0.535 |
|  | sdist = 4-7 | roleset_a ∋ Name ∧ |anchor_roles| = 3 | 141/329 | 105/179 | 0.513 |
| ★ | sdist_ord = ('8+', 'fwd') | roleset_a ∋ Host ∧ |anchor_roles| = 3 | 72/107 | 21/31 | 0.501 |
| ★ | sdist = 4-7 | roleset_a ∋ Host ∧ |anchor_roles| = 3 | 145/310 | 86/148 | 0.501 |

### HAS(roleset_a) ∧ HAS(roleset_b) (6)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | roleset_a ∋ Participant ∧ roleset_b ∋ Name | 98/155 | 33/44 | 0.606 |
| ★ | bucket_a = lead | roleset_a ∋ Loss ∧ roleset_b ∋ Location_original | 62/99 | 33/47 | 0.560 |
|  | bucket_a = lead | roleset_a ∋ Loss ∧ roleset_b ∋ Location_final | 71/107 | 34/50 | 0.542 |
| ★ | sdist = 4-7 | roleset_a ∋ Location ∧ roleset_b ∋ Score | 38/128 | 30/45 | 0.521 |
| ★ | bucket_a = lead | roleset_a ∋ Loss ∧ roleset_b ∋ State | 49/70 | 22/32 | 0.514 |
|  | sdist_ord = ('4-7', 'fwd') | roleset_a ∋ Participant ∧ roleset_b ∋ Event | 49/102 | 35/55 | 0.504 |

### HAS(etypeset_shared) ∧ HAS(roleset_a) (6)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = rev | etypeset_shared ∋ Person ∧ roleset_a ∋ Participant | 34/72 | 11/13 | 0.578 |
|  | bucket_a = late | etypeset_shared ∋ Person ∧ roleset_a ∋ Participant | 36/77 | 10/12 | 0.552 |
|  | sdist_ord = ('8+', 'fwd') | etypeset_shared ∋ Location ∧ roleset_a ∋ Winner | 78/128 | 35/52 | 0.538 |
|  | sdist_ord = ('8+', 'fwd') | etypeset_shared ∋ Location ∧ roleset_a ∋ Event | 92/135 | 37/57 | 0.519 |
|  | anchor_sd = (True, '4-7') | etypeset_shared ∋ Person ∧ roleset_a ∋ Participant | 76/119 | 19/27 | 0.515 |
| ★ | global = * | etypeset_shared ∋ Person ∧ roleset_a ∋ Score | 31/52 | 14/19 | 0.512 |

### EQ(type_a) ∧ HAS(roleset_b) (5)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | type_a = Competition ∧ roleset_b ∋ Object | 18/29 | 13/14 | 0.685 |
|  | global = * | type_a = Competition ∧ roleset_b ∋ Assailant | 19/32 | 15/17 | 0.657 |
| ★ | sdist = 8+ | type_a = Military_operation ∧ roleset_b ∋ Location_final | 49/90 | 16/20 | 0.584 |
| ★ | sdist_ord = ('8+', 'fwd') | type_a = Military_operation ∧ roleset_b ∋ Location_original | 33/65 | 18/24 | 0.551 |
|  | bucket_a = late | type_a = Military_operation ∧ roleset_b ∋ Location_original | 24/36 | 12/15 | 0.548 |

### EQ(multi_mention_a) ∧ HAS(roleset_b) (4)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Catastrophe | multi_mention_a = True ∧ roleset_b ∋ Location_original | 72/118 | 36/47 | 0.628 |
|  | global = * | multi_mention_a = True ∧ roleset_b ∋ Name | 206/338 | 96/152 | 0.553 |
|  | order = fwd | multi_mention_a = True ∧ roleset_b ∋ Winner | 73/110 | 27/39 | 0.536 |
| ★ | sdist_ord = ('2-3', 'fwd') | multi_mention_a = True ∧ roleset_b ∋ Host | 41/63 | 13/17 | 0.527 |

### CNT(etypeset_b) ∧ HAS(roleset_a) (4)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 4-7 | roleset_a ∋ Score ∧ |etypeset_b| = 3 | 15/25 | 10/11 | 0.623 |
| ★ | bucket_a = lead | |etypeset_b| = 2 ∧ roleset_a ∋ Participant | 209/367 | 64/94 | 0.581 |
|  | sdist_ord = ('4-7', 'fwd') | roleset_a ∋ Host ∧ |etypeset_b| = 3 | 34/69 | 16/21 | 0.549 |
| ★ | global = * | roleset_a ∋ Participant ∧ |etypeset_b| = 3 | 86/169 | 25/37 | 0.515 |

### EQ(multi_mention_a) ∧ EQ(type_b) (4)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | multi_mention_a = True ∧ type_b = Motion_directional | 44/65 | 25/32 | 0.612 |
| ★ | bucket_a = lead | multi_mention_a = True ∧ type_b = Self_motion | 73/115 | 26/34 | 0.600 |
| ★ | bucket_a = lead | multi_mention_a = True ∧ type_b = Arriving | 87/138 | 27/37 | 0.570 |
| ★ | global = * | multi_mention_a = True ∧ type_b = Cause_change_of_strength | 131/215 | 50/78 | 0.530 |

### HAS(etypeset_b) ∧ HAS(roleset_a) (4)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = fwd | etypeset_b ∋ Building ∧ roleset_a ∋ Score | 58/103 | 38/54 | 0.572 |
| ★ | anchor_sd = (True, '4-7') | etypeset_b ∋ Person ∧ roleset_a ∋ Event | 104/166 | 37/58 | 0.509 |
|  | anchor_sd = (True, '4-7') | roleset_a ∋ Name ∧ etypeset_b ∋ Building | 67/140 | 60/100 | 0.502 |
| ★ | sdist = 0 | etypeset_b ∋ Person ∧ roleset_a ∋ Event | 61/91 | 15/21 | 0.500 |

### EQ(bucket_a) ∧ HAS(anchor_roles) (3)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | bucket_a = lead ∧ anchor_roles ∋ (Host, Location) | 19/38 | 14/14 | 0.785 |
| ★ | etype_a = Influence | bucket_a = lead ∧ anchor_roles ∋ (Agent, Agent) | 32/57 | 12/14 | 0.601 |
|  | order = fwd | bucket_a = lead ∧ anchor_roles ∋ (Participant, Agent) | 57/73 | 12/15 | 0.548 |

### EQ(bucket_b) ∧ HAS(anchor_roles) (3)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 4-7 | bucket_b = mid ∧ anchor_roles ∋ (Participant, Patient) | 25/34 | 12/13 | 0.667 |
| ★ | sdist = 4-7 | bucket_b = mid ∧ anchor_roles ∋ (Participant, Agent) | 37/56 | 14/18 | 0.548 |
| ★ | etype_a = Competition | bucket_b = early ∧ anchor_roles ∋ (Agent, Winner) | 28/37 | 18/26 | 0.500 |

### EQ(type_b) ∧ REL(mention_cmp) (3)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | mention_cmp = a>b ∧ type_b = Escaping | 60/103 | 14/17 | 0.590 |
|  | global = * | mention_cmp = a>b ∧ type_b = Competition | 134/220 | 76/113 | 0.582 |
| ★ | global = * | mention_cmp = a>b ∧ type_b = Coming_to_be | 73/158 | 40/57 | 0.573 |

### EQ(multi_mention_a) ∧ HAS(anchor_roles) (3)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | multi_mention_a = True ∧ anchor_roles ∋ (Location_original, Location) | 22/34 | 11/13 | 0.578 |
| ★ | sdist = 4-7 | multi_mention_a = True ∧ anchor_roles ∋ (Location, Location) | 290/595 | 123/202 | 0.540 |
|  | order = fwd | multi_mention_a = True ∧ anchor_roles ∋ (Participant, Agent) | 22/28 | 9/11 | 0.523 |

### EQ(nrole_a) ∧ HAS(roleset_b) (3)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist_ord = ('4-7', 'fwd') | nrole_a = 5 ∧ roleset_b ∋ Participant | 31/81 | 26/36 | 0.560 |
|  | sdist_ord = ('4-7', 'fwd') | nrole_a = 5 ∧ roleset_b ∋ Host | 43/113 | 50/77 | 0.538 |
|  | bucket_a = lead | nrole_a = 4 ∧ roleset_b ∋ Event | 45/61 | 20/29 | 0.508 |

### EQ(bucket_a) ∧ EQ(type_b) (3)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('2-3', 'fwd') | bucket_a = lead ∧ type_b = Cause_change_of_strength | 61/113 | 25/36 | 0.531 |
| ★ | order = fwd | bucket_a = lead ∧ type_b = Competition | 232/521 | 136/230 | 0.527 |
| ★ | sdist_ord = ('4-7', 'fwd') | bucket_a = lead ∧ type_b = Arriving | 98/220 | 44/70 | 0.511 |

### ALL(roleset_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Military_operation | roleset_a = {Location} | 245/345 | 31/31 | 0.890 |
| ★ | bucket_a = lead | roleset_a = {Location} | 333/586 | 73/121 | 0.514 |

### HAS(roleset_b) ∧ REL(a_before_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = late | a_before_b = False ∧ roleset_b ∋ Original_Location | 9/50 | 18/18 | 0.824 |
| ★ | bucket_a = late | a_before_b = False ∧ roleset_b ∋ Final_Location | 11/54 | 20/27 | 0.553 |

### EQ(type_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | type_a = Military_operation | 1055/1757 | 473/614 | 0.735 |
| ★ | bucket_a = lead | type_a = Hostile_encounter | 2587/4694 | 904/1478 | 0.587 |

### EQ(bucket_a) ∧ EQ(type_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = fwd | bucket_a = lead ∧ type_a = Competition | 738/1268 | 296/405 | 0.686 |
| ★ | anchor = True | bucket_a = lead ∧ type_a = Traveling | 165/263 | 46/75 | 0.500 |

### HAS(anchor_roles) ∧ HAS(roleset_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 4-7 | roleset_b ∋ Patient ∧ anchor_roles ∋ (Participant, Patient) | 28/40 | 13/14 | 0.685 |
| ★ | sdist = 4-7 | roleset_b ∋ Participant ∧ anchor_roles ∋ (Name, Name) | 26/52 | 25/36 | 0.531 |

### EQ(nrole_a) ∧ HAS(etypeset_shared) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | nrole_a = 5 ∧ etypeset_shared ∋ Building | 66/105 | 66/87 | 0.659 |
| ★ | bucket_a = lead | nrole_a = 5 ∧ etypeset_shared ∋ Person | 97/167 | 37/53 | 0.565 |

### EQ(multi_mention_b) ∧ REL(same_type) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | same_type = True ∧ multi_mention_b = True | 74/128 | 27/34 | 0.632 |
| ★ | sdist = 0 | same_type = True ∧ multi_mention_b = True | 38/88 | 18/25 | 0.524 |

### CNT(etypeset_shared) ∧ EQ(bucket_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Military_operation | |etypeset_shared| = 1 ∧ bucket_b = early | 163/277 | 62/87 | 0.610 |
| ★ | etype_a = Use_firearm | |etypeset_shared| = 1 ∧ bucket_b = early | 17/105 | 28/42 | 0.516 |

### HAS(anchor_roles) ∧ HAS(anchor_roles) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | anchor_roles ∋ (Event, Event) ∧ anchor_roles ∋ (Location, Host) | 13/25 | 30/40 | 0.598 |
|  | global = * | anchor_roles ∋ (Location, Location) ∧ anchor_roles ∋ (Loser, Patient) | 45/75 | 14/18 | 0.548 |

### EQ(type_b) ∧ HAS(anchor_roles) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | type_b = Conquering ∧ anchor_roles ∋ (Loser, Patient) | 17/27 | 9/10 | 0.596 |
| ★ | order = rev | anchor_roles ∋ (Location, Location) ∧ type_b = Use_firearm | 16/54 | 22/31 | 0.534 |

### EQ(multi_mention_a) ∧ EQ(type_pair) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | multi_mention_a = True ∧ type_pair = (Catastrophe, Motion) | 100/182 | 59/85 | 0.590 |
| ★ | global = * | multi_mention_a = True ∧ type_pair = (Catastrophe, Arriving) | 73/107 | 21/29 | 0.543 |

### EQ(nrole_b) ∧ HAS(roleset_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | roleset_a ∋ Host ∧ nrole_b = 5 | 100/164 | 53/76 | 0.587 |
| ★ | sdist_ord = ('4-7', 'fwd') | roleset_a ∋ Host ∧ nrole_b = 5 | 75/160 | 45/73 | 0.502 |

### HAS(roleset_b) ∧ REL(mention_cmp) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor = False | mention_cmp = a>b ∧ roleset_b ∋ Location_final | 124/270 | 47/67 | 0.583 |
| ★ | order = fwd | mention_cmp = a>b ∧ roleset_b ∋ Participant | 62/117 | 37/58 | 0.509 |

### CNT(anchor_roles) ∧ EQ(multi_mention_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 4-7 | multi_mention_a = True ∧ |anchor_roles| = 2 | 279/552 | 121/186 | 0.580 |
| ★ | global = * | multi_mention_a = True ∧ |anchor_roles| = 3 | 422/789 | 172/305 | 0.508 |

### HAS(anchor_roles) ∧ REL(sent_gap) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | sent_gap = 4+ ∧ anchor_roles ∋ (Participant, Winner) | 22/35 | 11/13 | 0.578 |
|  | global = * | sent_gap = 4+ ∧ anchor_roles ∋ (Host, Location) | 27/61 | 27/37 | 0.570 |

### EQ(nrole_b) ∧ HAS(anchor_roles) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = fwd | nrole_b = 5 ∧ anchor_roles ∋ (Participant, Participant) | 31/53 | 25/34 | 0.569 |
| ★ | sdist = 0 | nrole_b = 4 ∧ anchor_roles ∋ (Winner, Agent) | 20/26 | 9/11 | 0.523 |

### EQ(type_pair) ∧ HAS(etypeset_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | etypeset_a ∋ Location ∧ type_pair = (Military_operation, Escaping) | 49/80 | 19/25 | 0.566 |
| ★ | global = * | etypeset_a ∋ Location ∧ type_pair = (Military_operation, Control) | 19/37 | 14/19 | 0.512 |

### ALL(roleset_a) ∧ EQ(bucket_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 2-3 | bucket_b = early ∧ roleset_a = {Location} | 27/56 | 10/12 | 0.552 |
| ★ | order = fwd | bucket_b = early ∧ roleset_a = {Location} | 51/119 | 16/22 | 0.518 |

### CNT(etypeset_shared) ∧ HAS(anchor_roles) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 4-7 | |etypeset_shared| = 2 ∧ anchor_roles ∋ (Participant, Patient) | 24/34 | 10/12 | 0.552 |
|  | global = * | |etypeset_shared| = 2 ∧ anchor_roles ∋ (Location, Host) | 14/29 | 25/37 | 0.515 |

### EQ(bucket_a) ∧ HAS(roleset_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('2-3', 'fwd') | bucket_a = lead ∧ roleset_b ∋ Name | 132/255 | 58/89 | 0.548 |
| ★ | order = fwd | bucket_a = lead ∧ roleset_b ∋ Original_Location | 44/80 | 24/35 | 0.520 |

### EQ(nrole_b) ∧ HAS(roleset_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | nrole_b = 3 ∧ roleset_b ∋ Event | 35/56 | 12/15 | 0.548 |
| ★ | bucket_a = lead | nrole_b = 5 ∧ roleset_b ∋ Participant | 44/79 | 51/80 | 0.528 |

### CNT(anchor_roles) ∧ EQ(type_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('4-7', 'fwd') | |anchor_roles| = 2 ∧ type_a = Competition | 236/467 | 117/191 | 0.542 |
| ★ | order = fwd | type_a = Competition ∧ |anchor_roles| = 3 | 355/696 | 192/324 | 0.538 |

### ALL(roleset_shared) ∧ EQ(type_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | roleset_shared = {Location} ∧ type_b = Getting | 54/90 | 24/34 | 0.538 |
| ★ | bucket_a = lead | roleset_shared = {Location} ∧ type_b = Arriving | 74/130 | 35/54 | 0.515 |

### EQ(multi_mention_a) ∧ HAS(roleset_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | multi_mention_a = True ∧ roleset_a ∋ Name | 509/913 | 196/335 | 0.532 |
| ★ | order = fwd | multi_mention_a = True ∧ roleset_a ∋ Host | 463/915 | 139/240 | 0.516 |

### HAS(roleset_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | roleset_b ∋ Passby | 75/134 | 53/83 | 0.531 |
| ★ | order = rev | roleset_b ∋ Passby | 22/123 | 33/51 | 0.510 |

### CNT(etypeset_shared) ∧ HAS(roleset_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist_ord = ('4-7', 'fwd') | |etypeset_shared| = 2 ∧ roleset_a ∋ Participant | 106/172 | 48/75 | 0.527 |
| ★ | anchor_sd = (True, '4-7') | |etypeset_shared| = 2 ∧ roleset_a ∋ Participant | 119/203 | 58/95 | 0.510 |

### EQ(type_a) ∧ HAS(anchor_roles) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist_ord = ('4-7', 'fwd') | anchor_roles ∋ (Location, Location) ∧ type_a = Competition | 238/416 | 105/176 | 0.523 |
| ★ | global = * | type_a = Military_operation ∧ anchor_roles ∋ (Patient, Patient) | 153/297 | 72/122 | 0.501 |

### EQ(bucket_a) ∧ HAS(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Social_event | bucket_a = lead ∧ etypeset_a ∋ Building | 78/124 | 19/19 | 0.832 |

### HAS(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Competition | etypeset_a ∋ Product | 173/240 | 13/13 | 0.772 |

### ALL(etypeset_a) ∧ EQ(bucket_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Traveling | bucket_a = lead ∧ etypeset_a = {Location} | 36/51 | 13/13 | 0.772 |

### EQ(bucket_b) ∧ HAS(roleset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Catastrophe | bucket_b = early ∧ roleset_b ∋ Location_original | 31/48 | 34/39 | 0.733 |

### ALL(etypeset_a) ∧ HAS(etypeset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Military_operation | etypeset_b ∋ Organization ∧ etypeset_a = {Location} | 145/235 | 36/43 | 0.700 |

### ALL(etypeset_a) ∧ CNT(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Military_operation | |roleset_shared| = 0 ∧ etypeset_a = {Location} | 172/258 | 18/20 | 0.699 |

### REL(mention_cmp) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Competition | mention_cmp = a>b | 450/738 | 196/275 | 0.657 |

### CNT(etypeset_shared) ∧ EQ(nrole_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | |etypeset_shared| = 2 ∧ nrole_a = 5 | 194/344 | 111/154 | 0.645 |

### EQ(has_loc_a) ∧ HAS(anchor_roles) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = fwd | has_loc_a = False ∧ anchor_roles ∋ (Loser, Loser) | 35/54 | 14/16 | 0.640 |

### ALL(anchor_roles) ∧ EQ(nrole_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | nrole_a = 3 ∧ anchor_roles = {(Location_original, Location)} | 20/31 | 14/16 | 0.640 |

### EQ(bucket_a) ∧ HAS(etypeset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Social_event | bucket_a = lead ∧ etypeset_b ∋ Building | 45/86 | 17/20 | 0.640 |

### EQ(nrole_a) ∧ REL(mention_cmp) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | mention_cmp = a>b ∧ nrole_a = 5 | 357/722 | 139/199 | 0.631 |

### EQ(type_pair) ∧ REL(mention_cmp) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | mention_cmp = a>b ∧ type_pair = (Catastrophe, Self_motion) | 34/51 | 10/11 | 0.623 |

### HAS(anchor_roles) ∧ MIX(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | etypeset_a có ≥ 2 loại ∧ anchor_roles ∋ (Host, Location) | 26/57 | 33/43 | 0.623 |

### CNT(roleset_shared) ∧ EQ(bucket_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Military_operation | |roleset_shared| = 3 ∧ bucket_b = early | 90/152 | 40/54 | 0.611 |

### HAS(anchor_roles) ∧ HAS(etypeset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Competition | etypeset_b ∋ Person ∧ anchor_roles ∋ (Loser, Patient) | 25/35 | 12/14 | 0.601 |

### ALL(roleset_shared) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | roleset_shared = {Location} ∧ roleset_a ∋ Participant | 172/319 | 54/76 | 0.600 |

### CNT(etypeset_b) ∧ EQ(bucket_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Military_operation | |etypeset_b| = 2 ∧ bucket_b = early | 112/187 | 38/52 | 0.597 |

### EQ(bucket_b) ∧ EQ(nrole_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Hostile_encounter | nrole_a = 0 ∧ bucket_b = lead | 25/29 | 9/10 | 0.596 |

### EQ(multi_mention_a) ∧ MIX(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Military_operation | etypeset_a có ≥ 2 loại ∧ multi_mention_a = True | 151/187 | 32/44 | 0.582 |

### EQ(bucket_b) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = fwd | bucket_b = early ∧ roleset_shared ∋ Name | 71/117 | 30/41 | 0.581 |

### HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | roleset_a ∋ Name | 851/1656 | 353/570 | 0.579 |

### EQ(bucket_a) ∧ EQ(multi_mention_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('2-3', 'fwd') | bucket_a = lead ∧ multi_mention_a = True | 616/1123 | 242/388 | 0.575 |

### CNT(etypeset_shared) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = rev | |etypeset_shared| = 2 ∧ type_b = Bodily_harm | 13/39 | 21/28 | 0.566 |

### ALL(etypeset_shared) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | roleset_a ∋ Winner ∧ etypeset_shared = {Building} | 43/70 | 17/22 | 0.566 |

### EQ(multi_mention_a) ∧ HAS(etypeset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 2-3 | multi_mention_a = True ∧ etypeset_shared ∋ Building | 24/44 | 17/22 | 0.566 |

### EQ(bucket_a) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = fwd | bucket_a = lead ∧ roleset_shared ∋ Participant | 57/97 | 24/33 | 0.558 |

### EQ(type_a) ∧ REL(mention_cmp) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (False, '4-7') | mention_cmp = a>b ∧ type_a = Catastrophe | 291/606 | 130/208 | 0.558 |

### EQ(type_a) ∧ HAS(etypeset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = late | etypeset_shared ∋ Person ∧ type_a = Social_event | 35/98 | 10/12 | 0.552 |

### EQ(bucket_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Catastrophe | bucket_a = lead | 1236/2585 | 612/1052 | 0.552 |

### HAS(etypeset_a) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('2-3', 'fwd') | etypeset_a ∋ Building ∧ roleset_shared ∋ Name | 20/39 | 16/21 | 0.549 |

### CNT(anchor_roles) ∧ CNT(etypeset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Social_event | |anchor_roles| = 2 ∧ |etypeset_b| = 3 | 66/107 | 14/18 | 0.548 |

### EQ(bucket_b) ∧ REL(same_type) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | bucket_b = lead ∧ same_type = True | 114/200 | 47/71 | 0.546 |

### ALL(roleset_a) ∧ HAS(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = rev | etypeset_a ∋ Person ∧ roleset_a = {Agent} | 40/191 | 47/71 | 0.546 |

### REL(mention_cmp) ∧ REL(role_subset) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | mention_cmp = a>b ∧ role_subset = True | 645/1108 | 230/387 | 0.545 |

### EQ(nrole_a) ∧ EQ(type_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 4-7 | type_a = Military_operation ∧ nrole_a = 1 | 88/155 | 26/37 | 0.542 |

### EQ(type_pair) ∧ HAS(anchor_roles) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | anchor_roles ∋ (Location, Location) ∧ type_pair = (Competition, Conquering) | 43/67 | 29/42 | 0.540 |

### CNT(anchor_roles) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | |anchor_roles| = 2 ∧ type_b = Getting | 59/104 | 29/42 | 0.540 |

### EQ(multi_mention_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Hostile_encounter | multi_mention_a = True | 1033/1814 | 291/500 | 0.538 |

### HAS(etypeset_a) ∧ REL(same_type) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | same_type = True ∧ etypeset_a ∋ Building | 48/83 | 41/62 | 0.537 |

### HAS(etypeset_b) ∧ REL(same_type) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | same_type = True ∧ etypeset_b ∋ Building | 50/87 | 36/54 | 0.534 |

### CNT(roleset_shared) ∧ EQ(bucket_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | bucket_a = lead ∧ |roleset_shared| = 3 | 1565/3349 | 669/1191 | 0.533 |

### EQ(bucket_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Military_operation | bucket_b = lead | 137/216 | 49/76 | 0.533 |

### HAS(etypeset_shared) ∧ HAS(etypeset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | etypeset_shared ∋ Organization ∧ etypeset_shared ∋ Building | 58/88 | 46/71 | 0.532 |

### EQ(type_pair) ∧ HAS(etypeset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist_ord = ('2-3', 'fwd') | etypeset_b ∋ Building ∧ type_pair = (Competition, Competition) | 16/30 | 13/17 | 0.527 |

### HAS(roleset_a) ∧ REL(a_before_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (False, '0') | a_before_b = False ∧ roleset_a ∋ Name | 23/64 | 13/17 | 0.527 |

### EQ(nrole_a) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | nrole_a = 5 ∧ type_b = Process_end | 46/75 | 13/17 | 0.527 |

### ALL(anchor_roles) ∧ HAS(etypeset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Military_operation | etypeset_b ∋ Person ∧ anchor_roles = {(Agent, Agent)} | 24/36 | 13/17 | 0.527 |

### EQ(type_a) ∧ REL(a_before_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | a_before_b = False ∧ type_a = Military_operation | 97/164 | 35/53 | 0.526 |

### HAS(roleset_b) ∧ HAS(roleset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Catastrophe | roleset_b ∋ Passby ∧ roleset_b ∋ Original_Location | 20/32 | 29/43 | 0.525 |

### EQ(multi_mention_a) ∧ EQ(type_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('1', 'fwd') | multi_mention_a = True ∧ type_a = Military_operation | 18/36 | 11/14 | 0.524 |

### ALL(etypeset_a) ∧ EQ(nrole_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Social_event | nrole_b = 2 ∧ etypeset_a = {Building} | 19/32 | 11/14 | 0.524 |

### ALL(etypeset_shared) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | etypeset_shared = {Organization} ∧ type_pair = (Hostile_encounter, Process_start) | 18/27 | 9/11 | 0.523 |

### ALL(etypeset_shared) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = lead | etypeset_shared = {Organization} ∧ type_b = Defending | 22/36 | 9/11 | 0.523 |

### ALL(roleset_b) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | roleset_a ∋ Loss ∧ roleset_b = {Patient} | 83/129 | 30/45 | 0.521 |

### EQ(bucket_a) ∧ REL(same_type) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('2-3', 'fwd') | bucket_a = lead ∧ same_type = True | 179/342 | 76/125 | 0.520 |

### CNT(etypeset_shared) ∧ EQ(multi_mention_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | multi_mention_a = True ∧ |etypeset_shared| = 2 | 437/728 | 161/278 | 0.520 |

### CNT(etypeset_b) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = fwd | |etypeset_b| = 2 ∧ roleset_shared ∋ Participant | 60/116 | 37/57 | 0.519 |

### ALL(etypeset_a) ∧ REL(role_subset) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | role_subset = True ∧ etypeset_a = {Organization} | 385/683 | 113/192 | 0.518 |

### EQ(bucket_b) ∧ EQ(multi_mention_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = fwd | multi_mention_a = True ∧ bucket_b = early | 594/1176 | 221/391 | 0.516 |

### HAS(etypeset_a) ∧ HAS(roleset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 4-7 | etypeset_a ∋ Location ∧ roleset_b ∋ Score | 26/82 | 22/32 | 0.514 |

### CNT(roleset_shared) ∧ HAS(roleset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist_ord = ('4-7', 'fwd') | |roleset_shared| = 3 ∧ roleset_b ∋ Host | 59/193 | 55/89 | 0.514 |

### EQ(bucket_b) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | anchor_sd = (False, '1') | bucket_b = early ∧ roleset_a ∋ Loss | 71/135 | 47/75 | 0.514 |

### EQ(multi_mention_a) ∧ EQ(nrole_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | multi_mention_a = True ∧ nrole_b = 5 | 161/325 | 69/114 | 0.514 |

### EQ(type_a) ∧ MIX(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (False, '8+') | etypeset_a có ≥ 2 loại ∧ type_a = Military_operation | 201/352 | 95/161 | 0.513 |

### HAS(roleset_a) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | roleset_a ∋ Participant ∧ roleset_a ∋ Score | 95/156 | 14/19 | 0.512 |

### EQ(nrole_a) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('2-3', 'fwd') | nrole_a = 3 ∧ type_pair = (Catastrophe, Arriving) | 23/35 | 14/19 | 0.512 |

### HAS(etypeset_shared) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | anchor_sd = (True, '4-7') | etypeset_shared ∋ Location ∧ roleset_shared ∋ Event | 59/122 | 41/65 | 0.509 |

### CNT(etypeset_b) ∧ REL(a_before_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Military_operation | |etypeset_b| = 2 ∧ a_before_b = False | 149/210 | 54/88 | 0.509 |

### HAS(anchor_roles) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | roleset_shared ∋ Location ∧ anchor_roles ∋ (Participant, Winner) | 29/61 | 17/24 | 0.508 |

### EQ(type_a) ∧ HAS(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor = False | etypeset_a ∋ Location ∧ type_a = Military_operation | 707/1490 | 217/389 | 0.508 |

### EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | type_b = Hostile_encounter | 431/812 | 164/290 | 0.508 |

### EQ(bucket_b) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor = True | bucket_b = early ∧ type_b = Use_firearm | 41/120 | 20/29 | 0.508 |

### ALL(etypeset_shared) ∧ EQ(type_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (True, '8+') | etypeset_shared = {Organization} ∧ type_a = Military_operation | 48/92 | 34/53 | 0.507 |

### EQ(nrole_a) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (True, '4-7') | nrole_a = 5 ∧ roleset_a ∋ Participant | 92/160 | 71/119 | 0.507 |

### CNT(anchor_roles) ∧ EQ(bucket_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = fwd | bucket_a = lead ∧ |anchor_roles| = 3 | 591/1311 | 280/510 | 0.506 |

### HAS(roleset_a) ∧ REL(mention_cmp) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (True, '2-3') | mention_cmp = a>b ∧ roleset_a ∋ Host | 100/158 | 27/41 | 0.505 |

### CNT(anchor_roles) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | |anchor_roles| = 3 ∧ type_pair = (Competition, Earnings_and_losses) | 33/51 | 12/16 | 0.505 |

### EQ(has_org_b) ∧ HAS(anchor_roles) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | has_org_b = False ∧ anchor_roles ∋ (Loser, Patient) | 28/42 | 12/16 | 0.505 |

### EQ(same_type) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 0 | same_type = False ∧ roleset_shared ∋ Name | 17/25 | 12/16 | 0.505 |

### EQ(has_loc_b) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 8+ | has_loc_b = True ∧ roleset_a ∋ Loser | 27/81 | 31/48 | 0.504 |

### CNT(etypeset_shared) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = fwd | |etypeset_shared| = 2 ∧ roleset_shared ∋ Event | 122/229 | 74/125 | 0.504 |

### CNT(anchor_roles) ∧ EQ(nrole_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = fwd | nrole_a = 5 ∧ |anchor_roles| = 3 | 320/753 | 165/294 | 0.504 |

### EQ(type_b) ∧ HAS(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | etypeset_a ∋ Organization ∧ type_b = Motion_directional | 52/87 | 24/36 | 0.503 |

### EQ(bucket_b) ∧ REL(role_subset) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | role_subset = True ∧ bucket_b = lead | 199/401 | 78/133 | 0.501 |

### EQ(multi_mention_b) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | type_b = Hostile_encounter ∧ multi_mention_b = True | 36/66 | 15/21 | 0.500 |

### CNT(roleset_shared) ∧ EQ(type_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (True, '2-3') | |roleset_shared| = 0 ∧ type_a = Catastrophe | 23/48 | 18/26 | 0.500 |

### CNT(roleset_shared) ∧ EQ(multi_mention_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 0 | |roleset_shared| = 3 ∧ multi_mention_b = True | 38/115 | 18/26 | 0.500 |

## SIMULTANEOUS — 55 luật, 43 họ

### EQ(order) ∧ REL(a_before_b) (3)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Damaging | a_before_b = False ∧ order = same | 11/54 | 8/18 | 0.246 |
| ★ | etype_a = Supply | order = same ∧ a_before_b = False | 9/52 | 7/22 | 0.164 |
| ★ | etype_a = Judgment_communication | order = same ∧ a_before_b = False | 14/50 | 6/19 | 0.154 |

### EQ(type_b) ∧ HAS(anchor_roles) (3)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 0 | anchor_roles ∋ (Location, Location) ∧ type_b = Military_operation | 11/57 | 8/20 | 0.219 |
|  | sdist = 0 | anchor_roles ∋ (Patient, Patient) ∧ type_b = Military_operation | 12/33 | 6/16 | 0.185 |
| ★ | sdist = 0 | anchor_roles ∋ (Location, Location) ∧ type_b = Use_firearm | 10/64 | 5/15 | 0.152 |

### HAS(roleset_shared) ∧ REL(a_before_b) (3)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | a_before_b = False ∧ roleset_shared ∋ Speaker | 10/43 | 5/11 | 0.213 |
|  | sdist = 0 | a_before_b = False ∧ roleset_shared ∋ Content | 23/101 | 10/31 | 0.186 |
|  | anchor = True | a_before_b = False ∧ roleset_shared ∋ Victim | 11/51 | 9/28 | 0.179 |

### EQ(bucket_b) ∧ HAS(roleset_shared) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | bucket_b = lead ∧ roleset_shared ∋ Participant | 16/48 | 5/10 | 0.237 |
|  | global = * | bucket_b = lead ∧ roleset_shared ∋ Host | 24/76 | 9/33 | 0.151 |

### HAS(roleset_b) ∧ REL(a_before_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | anchor_sd = (True, '0') | a_before_b = False ∧ roleset_b ∋ Action | 10/41 | 5/11 | 0.213 |
|  | etype_a = Attack | a_before_b = False ∧ roleset_b ∋ Consequence | 11/125 | 5/12 | 0.193 |

### HAS(anchor_roles) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Attack | anchor_roles ∋ (Consequence, Consequence) | 18/116 | 8/24 | 0.180 |
| ★ | etype_a = Killing | anchor_roles ∋ (Victim, Patient) | 12/42 | 5/13 | 0.177 |

### EQ(bucket_b) ∧ HAS(roleset_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = lead | bucket_b = lead ∧ roleset_b ∋ Participant | 15/57 | 6/18 | 0.163 |
|  | etype_a = Competition | roleset_b ∋ Event ∧ bucket_b = lead | 21/69 | 8/28 | 0.153 |

### REL(a_before_b) ∧ REL(same_type) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor = True | a_before_b = False ∧ same_type = True | 284/1231 | 81/424 | 0.156 |
| ★ | sdist = 0 | a_before_b = False ∧ same_type = True | 110/427 | 30/143 | 0.151 |

### EQ(type_pair) ∧ REL(a_before_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | a_before_b = False ∧ type_pair = (Military_operation, Military_operation) | 11/46 | 5/15 | 0.152 |
| ★ | anchor = True | a_before_b = False ∧ type_pair = (Bodily_harm, Killing) | 19/39 | 4/11 | 0.152 |

### EQ(type_b) ∧ REL(a_before_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | a_before_b = False ∧ type_b = Request | 13/68 | 9/21 | 0.245 |

### EQ(multi_mention_b) ∧ HAS(anchor_roles) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Catastrophe | anchor_roles ∋ (Patient, Location) ∧ multi_mention_b = True | 12/56 | 5/10 | 0.237 |

### HAS(roleset_shared) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | anchor = True | roleset_shared ∋ Agent ∧ roleset_shared ∋ Victim | 8/37 | 6/13 | 0.232 |

### EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = rev | type_pair = (Attack, Attack) | 15/178 | 11/29 | 0.227 |

### EQ(type_pair) ∧ HAS(anchor_roles) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | anchor_roles ∋ (Agent, Agent) ∧ type_pair = (Military_operation, Military_operation) | 10/42 | 7/17 | 0.216 |

### EQ(type_b) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = rev | type_b = Attack ∧ roleset_a ∋ Consequence | 13/91 | 7/18 | 0.203 |

### EQ(type_a) ∧ REL(a_before_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (True, '0') | a_before_b = False ∧ type_a = Bodily_harm | 28/91 | 7/18 | 0.203 |

### CNT(anchor_roles) ∧ HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = late | |anchor_roles| = 2 ∧ roleset_shared ∋ Victim | 8/45 | 9/26 | 0.194 |

### HAS(anchor_roles) ∧ REL(a_before_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | a_before_b = False ∧ anchor_roles ∋ (Participant, Participant) | 23/69 | 10/31 | 0.186 |

### EQ(order) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor = False | order = rev ∧ type_pair = (Catastrophe, Catastrophe) | 15/71 | 10/31 | 0.186 |

### CNT(etypeset_shared) ∧ EQ(bucket_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Competition | |etypeset_shared| = 2 ∧ bucket_b = lead | 18/67 | 10/31 | 0.186 |

### CNT(etypeset_a) ∧ REL(same_type) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | order = rev | same_type = True ∧ |etypeset_a| = 3 | 12/51 | 7/20 | 0.181 |

### EQ(has_org_a) ∧ HAS(anchor_roles) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Hold | has_org_a = False ∧ anchor_roles ∋ (Agent, Host) | 12/29 | 5/13 | 0.177 |

### EQ(bucket_a) ∧ REL(same_type) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist_ord = ('2-3', 'rev') | same_type = True ∧ bucket_a = early | 21/66 | 8/25 | 0.172 |

### CNT(roleset_shared) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | anchor_sd = (True, '0') | |roleset_shared| = 3 ∧ type_b = Military_operation | 13/46 | 7/21 | 0.172 |

### EQ(bucket_b) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | global = * | bucket_b = early ∧ type_pair = (Catastrophe, Catastrophe) | 37/134 | 11/38 | 0.170 |

### EQ(type_pair) ∧ HAS(etypeset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = mid | etypeset_shared ∋ Location ∧ type_pair = (Social_event, Social_event) | 13/40 | 4/10 | 0.168 |

### CNT(anchor_roles) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = mid | |anchor_roles| = 2 ∧ type_pair = (Social_event, Social_event) | 14/48 | 4/10 | 0.168 |

### EQ(order) ∧ HAS(roleset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Bodily_harm | order = same ∧ roleset_b ∋ Victim | 16/38 | 4/10 | 0.168 |

### EQ(type_pair) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = mid | roleset_a ∋ Participant ∧ type_pair = (Social_event, Social_event) | 9/49 | 4/10 | 0.168 |

### EQ(nrole_a) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | anchor = True | nrole_a = 4 ∧ type_pair = (Social_event, Social_event) | 19/87 | 4/10 | 0.168 |

### CNT(anchor_roles) ∧ EQ(bucket_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Competition | |anchor_roles| = 3 ∧ bucket_b = lead | 27/87 | 12/43 | 0.167 |

### CNT(anchor_roles) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | |anchor_roles| = 2 ∧ type_b = Military_operation | 15/61 | 8/26 | 0.165 |

### HAS(roleset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | roleset_shared ∋ Participant | 15/64 | 7/22 | 0.164 |

### EQ(type_b) ∧ HAS(etypeset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | etypeset_shared ∋ Organization ∧ type_b = Military_operation | 13/69 | 7/22 | 0.164 |

### CNT(roleset_shared) ∧ EQ(order) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Damaging | |roleset_shared| = 3 ∧ order = same | 17/98 | 8/27 | 0.159 |

### CNT(anchor_roles) ∧ EQ(has_org_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Hold | has_org_a = False ∧ |anchor_roles| = 3 | 11/55 | 10/36 | 0.158 |

### CNT(anchor_roles) ∧ EQ(order) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Damaging | order = same ∧ |anchor_roles| = 3 | 14/73 | 6/19 | 0.154 |

### CNT(anchor_roles) ∧ REL(a_before_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | a_before_b = False ∧ |anchor_roles| = 3 | 127/539 | 35/170 | 0.152 |

### HAS(anchor_roles) ∧ REL(same_type) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | global = * | same_type = True ∧ anchor_roles ∋ (Victim, Victim) | 14/57 | 5/15 | 0.152 |

### CNT(anchor_roles) ∧ CNT(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | order = rev | |anchor_roles| = 3 ∧ |etypeset_a| = 3 | 20/86 | 5/15 | 0.152 |

### HAS(anchor_roles) ∧ HAS(anchor_roles) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Damaging | anchor_roles ∋ (Agent, Agent) ∧ anchor_roles ∋ (Patient, Patient) | 12/52 | 5/15 | 0.152 |

### EQ(type_b) ∧ HAS(etypeset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | etypeset_a ∋ Person ∧ type_b = Social_event | 14/70 | 5/15 | 0.152 |

### MIX(roleset_shared) ∧ REL(a_before_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Statement | a_before_b = False ∧ roleset_shared có ≥ 2 loại | 11/44 | 4/11 | 0.152 |

## OVERLAP — 47 luật, 30 họ

### EQ(type_b) ∧ HAS(roleset_a) (6)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 0 | roleset_a ∋ Victim ∧ type_b = Bodily_harm | 36/98 | 13/34 | 0.239 |
| ★ | sdist = 0 | type_b = Bodily_harm ∧ roleset_a ∋ Instrument | 19/53 | 7/20 | 0.181 |
| ★ | sdist = 0 | roleset_a ∋ Cause ∧ type_b = Bodily_harm | 23/66 | 5/16 | 0.142 |
| ★ | bucket_a = early | type_b = Bodily_harm ∧ roleset_a ∋ Cause | 10/55 | 4/13 | 0.127 |
|  | bucket_a = early | type_b = Bodily_harm ∧ roleset_a ∋ Victim | 15/88 | 7/30 | 0.118 |
|  | anchor = True | roleset_a ∋ Victim ∧ type_b = Bodily_harm | 41/195 | 14/82 | 0.105 |

### EQ(type_pair) (5)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = late | type_pair = (Damaging, Destroying) | 10/120 | 9/34 | 0.146 |
| ★ | anchor = True | type_pair = (Damaging, Destroying) | 14/99 | 7/27 | 0.132 |
| ★ | sdist = 0 | type_pair = (Motion, Damaging) | 8/29 | 5/18 | 0.125 |
| ★ | sdist = 0 | type_pair = (Bodily_harm, Death) | 8/37 | 4/14 | 0.117 |
| ★ | global = * | type_pair = (Killing, Bodily_harm) | 40/228 | 14/77 | 0.112 |

### ALL(roleset_shared) ∧ EQ(type_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | roleset_shared = {Location} ∧ type_b = Bodily_harm | 38/99 | 12/36 | 0.202 |
|  | bucket_a = early | roleset_shared = {Location} ∧ type_b = Bodily_harm | 16/92 | 7/34 | 0.103 |

### EQ(order) ∧ HAS(anchor_roles) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = late | order = same ∧ anchor_roles ∋ (Location_original, Location) | 9/73 | 6/17 | 0.173 |
| ★ | etype_a = Killing | anchor_roles ∋ (Location, Location) ∧ order = same | 57/211 | 16/67 | 0.153 |

### HAS(anchor_roles) ∧ HAS(roleset_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 0 | roleset_a ∋ Victim ∧ anchor_roles ∋ (Agent, Killer) | 17/45 | 4/11 | 0.152 |
|  | sdist = 0 | anchor_roles ∋ (Location, Location) ∧ roleset_a ∋ Victim | 67/302 | 18/93 | 0.126 |

### EQ(order) ∧ EQ(type_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = late | order = same ∧ type_a = Bodily_harm | 17/164 | 10/40 | 0.142 |
| ★ | bucket_a = early | order = same ∧ type_a = Killing | 19/115 | 7/32 | 0.110 |

### HAS(anchor_roles) ∧ HAS(roleset_b) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = late | anchor_roles ∋ (Agent, Agent) ∧ roleset_b ∋ Loss | 15/274 | 16/80 | 0.127 |
|  | etype_a = Damaging | anchor_roles ∋ (Location, Location) ∧ roleset_b ∋ Cause | 13/69 | 6/25 | 0.115 |

### EQ(type_a) ∧ HAS(anchor_roles) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = late | type_a = Damaging ∧ anchor_roles ∋ (Patient, Patient) | 8/50 | 4/14 | 0.117 |
| ★ | bucket_a = late | anchor_roles ∋ (Agent, Agent) ∧ type_a = Damaging | 19/293 | 12/63 | 0.112 |

### EQ(type_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | anchor_sd = (True, '0') | type_a = Killing | 61/305 | 17/95 | 0.115 |
| ★ | anchor_sd = (True, '0') | type_a = Bodily_harm | 33/257 | 14/83 | 0.103 |

### ALL(roleset_shared) ∧ HAS(roleset_a) (2)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 0 | roleset_shared = {Location} ∧ roleset_a ∋ Victim | 55/248 | 13/70 | 0.112 |
|  | anchor_sd = (True, '0') | roleset_shared = {Location} ∧ roleset_a ∋ Instrument | 17/67 | 5/22 | 0.101 |

### EQ(bucket_a) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | anchor_sd = (True, '0') | bucket_a = early ∧ type_b = Bodily_harm | 26/104 | 8/23 | 0.188 |

### ALL(etypeset_b) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | etypeset_b = {Location} ∧ type_pair = (Damaging, Destroying) | 9/25 | 4/10 | 0.168 |

### EQ(shares_anchor) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | bucket_a = late | shares_anchor = True ∧ type_pair = (Damaging, Destroying) | 9/66 | 7/22 | 0.164 |

### CNT(anchor_roles) ∧ HAS(roleset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Damaging | |anchor_roles| = 2 ∧ roleset_b ∋ Cause | 13/58 | 6/18 | 0.163 |

### EQ(type_a) ∧ HAS(etypeset_shared) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (True, '0') | etypeset_shared ∋ Location ∧ type_a = Damaging | 23/101 | 9/32 | 0.156 |

### EQ(order) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = early | order = same ∧ type_b = Bodily_harm | 27/123 | 8/31 | 0.137 |

### CNT(roleset_shared) ∧ EQ(order) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Killing | |roleset_shared| = 1 ∧ order = same | 60/269 | 17/82 | 0.134 |

### CNT(etypeset_shared) ∧ EQ(order) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Killing | |etypeset_shared| = 1 ∧ order = same | 47/233 | 14/70 | 0.123 |

### EQ(nrole_b) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 0 | nrole_b = 3 ∧ roleset_a ∋ Killer | 29/152 | 10/46 | 0.123 |

### HAS(anchor_roles) ∧ REL(role_subset) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Damaging | role_subset = True ∧ anchor_roles ∋ (Agent, Agent) | 20/210 | 10/50 | 0.112 |

### CNT(roleset_shared) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (False, '0') | |roleset_shared| = 0 ∧ type_b = Damaging | 8/48 | 5/20 | 0.112 |

### EQ(type_b) ∧ HAS(anchor_roles) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | bucket_a = late | anchor_roles ∋ (Agent, Agent) ∧ type_b = Destroying | 16/228 | 14/77 | 0.112 |

### HAS(roleset_a) ∧ HAS(roleset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | sdist = 0 | roleset_b ∋ Location ∧ roleset_a ∋ Killer | 36/189 | 10/52 | 0.108 |

### EQ(has_person_b) ∧ EQ(type_pair) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor = True | has_person_b = False ∧ type_pair = (Bodily_harm, Death) | 9/43 | 3/10 | 0.108 |

### HAS(etypeset_b) ∧ HAS(roleset_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (True, '0') | roleset_b ∋ Cause ∧ etypeset_b ∋ Product | 8/39 | 3/10 | 0.108 |

### HAS(anchor_roles) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | anchor_roles ∋ (Agent, Cause) | 23/97 | 5/21 | 0.106 |

### ALL(etypeset_b) ∧ EQ(type_b) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | anchor_sd = (True, '0') | etypeset_b = {Location} ∧ type_b = Destroying | 23/132 | 10/53 | 0.106 |

### EQ(order) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
|  | etype_a = Killing | order = same ∧ roleset_a ∋ Cause | 25/120 | 8/40 | 0.105 |

### EQ(order) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | etype_a = Damaging | order = same | 37/280 | 19/119 | 0.105 |

### CNT(anchor_roles) ∧ HAS(roleset_a) (1)

| | Lớp | Điều kiện | k/n | ck/cn | wlb |
|---|---|---|---|---|---|
| ★ | sdist = 0 | |anchor_roles| = 2 ∧ roleset_a ∋ Victim | 56/293 | 14/83 | 0.103 |
