# Event-Centric Graph and Motif-Mining Review Report

## Scope and inputs

This report is reproducible from the two train files only:

- MAVEN-Arg: `MAVEN-Arg/train.jsonl`
- MAVEN-ERE: `MAVEN_ERE/train.jsonl`

No train/dev/test labels were mixed. The report describes alignment, a document-level Event-Centric Graph, and one structural motif; it does not implement a general temporal miner.

## Alignment and usable temporal pairs

- Documents: MAVEN-Arg=2913, MAVEN-ERE=2913, matched=2913.
- Alignment key: `doc_id + EVENT_* id`, validated by equal `type_id` in both datasets.
- All MAVEN-ERE temporal pairs: 792,445.
- Retained pairs: 430,118.
- Excluded because an endpoint is absent from MAVEN-Arg event clusters: 360,418.
- Excluded because an aligned endpoint has a `type_id` mismatch: 1,909.

### Temporal-label distribution

| Relation | All MAVEN-ERE pairs | Retained aligned pairs |
|---|---:|---:|
| BEFORE | 683,581 | 390,821 |
| BEGINS-ON | 453 | 242 |
| CONTAINS | 95,933 | 32,544 |
| ENDS-ON | 281 | 98 |
| OVERLAP | 6,376 | 2,627 |
| SIMULTANEOUS | 5,821 | 3,786 |

## Stored Event-Centric Graph

Store one heterogeneous graph per document. Event clusters are central nodes. The temporal relation under prediction is stored separately from input edges.

| Node type | Source fields | Key attributes |
|---|---|---|
| `document` | `id`, `title` | `doc_id`, title |
| `event` | MAVEN-Arg/MAVEN-ERE `events` | event ID, type, type ID, trigger mentions |
| `entity` | MAVEN-Arg `entities` | entity ID, entity type, mentions |
| `argument_span` | MAVEN-Arg event arguments without `entity_id` | text, character offset |

| Edge type | Source → target | Properties |
|---|---|---|
| `HAS_EVENT` | document → event | — |
| `HAS_ARGUMENT` | event → entity or argument span | argument role, e.g. `Agent`, `Location` |
| temporal target | event → event | label such as `BEFORE`; excluded from input when that pair is masked |

Recommended record shape:

```json
{"doc_id":"…","nodes":[…],"input_edges":[…],"temporal_targets":[{"source":"event:E1","target":"event:E2","relation":"BEFORE"}]}
```

The prototype graph artifact is `event_temporal_mining/data/processed/graph_demo/event_centric_graph_sample.json`. It contains a temporal edge solely for illustration and marks it `available_to_pattern_extractor_when_masked: false`.

## Audited structural motif

Pattern signature, with the raw entity ID abstracted to variable `x`:

```text
E1(type=Motion)      --Location_final--> x
E2(type=Process_end) --Location-------> x
```

Only direct MAVEN-Arg `entity_id` sharing is considered shared-entity evidence. Identical raw argument strings are not promoted to entity identity.

- Support: 25
- `BEFORE`: 24
- `CONTAINS`: 1
- Constraint confidence `P → BEFORE`: 24/25 = 0.96

For a masked pair, extract this motif using only node types and `HAS_ARGUMENT` edges. Look up its train-derived relation counts and predict the relation with the largest count. The masked pair's temporal target is never an input feature.

### Representative occurrence

- Document: `364ed14fc610df6e25a2f446e2b2d2ab`
- `Motion` event: `EVENT_d2587256a67ce75ea9d9d864288d822c` — trigger `landed`
- `Process_end` event: `EVENT_f652152ef7245a6f5c27396a2b1964e1` — trigger `concluded`
- Shared entity: `ENTITY_185734cbbe4da16fb0782dfaa326529c` — `marsala`
- Gold relation: `BEFORE`

## Full occurrence list for this motif

Every row is one motif occurrence. Check its event IDs in both train JSONL files and its temporal label in `MAVEN_ERE/train.jsonl`.

| # | doc_id | Relation | Motion event | Process-end event | Shared entity |
|---:|---|---|---|---|---|
| 1 | `364ed14fc610df6e25a2f446e2b2d2ab` | BEFORE | `EVENT_d2587256a67ce75ea9d9d864288d822c` (landed) | `EVENT_f652152ef7245a6f5c27396a2b1964e1` (concluded) | `ENTITY_185734cbbe4da16fb0782dfaa326529c` (marsala) |
| 2 | `364ed14fc610df6e25a2f446e2b2d2ab` | BEFORE | `EVENT_451b7cde13d2b8c21426db027c51096f` (sailed) | `EVENT_f652152ef7245a6f5c27396a2b1964e1` (concluded) | `ENTITY_185734cbbe4da16fb0782dfaa326529c` (marsala) |
| 3 | `364ed14fc610df6e25a2f446e2b2d2ab` | CONTAINS | `EVENT_f535eb21f8f958a04cbc69c1d1521186` (Expedition, venture, expedition, Expedition, expedition) | `EVENT_f652152ef7245a6f5c27396a2b1964e1` (concluded) | `ENTITY_185734cbbe4da16fb0782dfaa326529c` (marsala) |
| 4 | `e6d8238a82cde37697289bc6aa6ffb1c` | BEFORE | `EVENT_2336362035071c07731be7ea1dfa4e56` (saw) | `EVENT_1411b1840bdf4226a2857c1a60d2842a` (finished) | `ENTITY_6e2aad45a89f5ee9383a6eef2439933a` (Australia, Australia) |
| 5 | `5b13a815e03b4abd610bf9b8e0666a57` | BEFORE | `EVENT_d1a89192590c61e122ded4342a76c5a6` (kicked off) | `EVENT_c679242ee2e253187eb294426bdbb4ba` (ended) | `ENTITY_9de648dae8774cd631007aea2978c329` (London, London) |
| 6 | `07ee88ae17abb6e129b892eb5e1c6bd4` | BEFORE | `EVENT_c939e417e0aa65b57c6b0a7f7908e655` (sneak) | `EVENT_e1cbf320b3f75684d3cdf2ed80c83079` (ended) | `ENTITY_84c8f59c0ce91019b807b1f843a77594` (Comiskey Park, Comiskey Park) |
| 7 | `07ee88ae17abb6e129b892eb5e1c6bd4` | BEFORE | `EVENT_b87a122e87b59ba3f29325f9fb7c6409` (come to) | `EVENT_e1cbf320b3f75684d3cdf2ed80c83079` (ended) | `ENTITY_84c8f59c0ce91019b807b1f843a77594` (Comiskey Park, Comiskey Park) |
| 8 | `21bb5507853217956cd55937caed27b4` | BEFORE | `EVENT_f43b23d5495c1187d346d3634d618096` (poured) | `EVENT_157e0a7ffb422e655999dcaa8838224a` (stop) | `ENTITY_e33f378fff42a80d7bd29e0c0f49bad2` (Houston, Houston, Houston, Houston) |
| 9 | `166e11f609149fbb697b9a6f6a11b2ce` | BEFORE | `EVENT_25b491067ad2441404372ff118432f09` (moved) | `EVENT_ad2181a3cdddb4f07d553de4e4fe2ac4` (culminated) | `ENTITY_f8ad9210e8a55ae03f564cece87fa85f` (Yorktown, Yorktown, Yorktown, Yorktown, Yorktown) |
| 10 | `f97bdf89e9de3458b32a5b7f7ea07e53` | BEFORE | `EVENT_e96dba51ee907401c495e0e016198e9e` (march) | `EVENT_3776521b2233f3146076ca608f592391` (end) | `ENTITY_0c0141b38d96e771cadb8006f5371aa4` (Richmond) |
| 11 | `2bee7035ea8636ab5e9860564770a18f` | BEFORE | `EVENT_81e4a55ac8b26c52ccb3a43f7ce45a40` (travelling) | `EVENT_356fe2954844b5e4fe9eedba124fa7ba` (end) | `ENTITY_f70b27ce0c260cd5c44a1cfe1d317f16` (Dublin, Dublin, Dublin) |
| 12 | `b9aeb3fa9d6f6813bf8f8f4114cda34f` | BEFORE | `EVENT_fb4efbaca3e92f673183117f7dade737` (sailed) | `EVENT_888f950b14ec87370270d36da9e11b02` (end) | `ENTITY_9b0030083b36e7b9ec9980fb1e3afa62` (England, England, England) |
| 13 | `6f2964836fde4ad662ddaf3e949b21bc` | BEFORE | `EVENT_c1027b12704ea01eabee98fe061b7491` (rode) | `EVENT_38f2b4db3a84699767fc183ac6d4a9e2` (ending) | `ENTITY_9aeb5566899fdc49f75519a13850d179` (Western Pennsylvania, western Pennsylvania, western Pennsylvania) |
| 14 | `2cbb655873a7ed17ae2db6b373479371` | BEFORE | `EVENT_264e60c1a92a9d9d56bd655b1efbc055` (pursuit) | `EVENT_979cfd1a7df48713c71a341b896dec89` (ended) | `ENTITY_67f3d1bf7f14a17e35d2946dec4d6a51` (El Arish) |
| 15 | `dd624a600fda162816cdc29f6f945f5f` | BEFORE | `EVENT_1043738603ac6fdb45324f6568bbd7a9` (advanced) | `EVENT_d444aaee5556d33a4fac41abab6ee4a5` (halted) | `ENTITY_aaf83faa53883a84d3d54c68f68d6542` (Falaise, north of Falaise) |
| 16 | `836342aa7b1f5a224189e54c0513d4c8` | BEFORE | `EVENT_dee53164f1be3ea78e76d8766139a728` (pumped) | `EVENT_37d302eb625b520abcae10cd325c0e6f` (ended) | `ENTITY_0c6c93b00265744d3eb2d8c093493d71` (Dubrovka Theater) |
| 17 | `0802d01cd176987cb3d7b4cfc8f23179` | BEFORE | `EVENT_4a3fe6126dd4329f4402af857b6bed21` (sailed) | `EVENT_e94915ee375bc47eb700cafe8dec4962` (expired) | `ENTITY_fefe552d66d3c7aabc9c3d52e940a253` (Kowloon, Kowloon Peninsula, Kowloon, Kowloon) |
| 18 | `0802d01cd176987cb3d7b4cfc8f23179` | BEFORE | `EVENT_4a3fe6126dd4329f4402af857b6bed21` (sailed) | `EVENT_7a82eee7ab190e79e7d875eba898b63f` (ending) | `ENTITY_fefe552d66d3c7aabc9c3d52e940a253` (Kowloon, Kowloon Peninsula, Kowloon, Kowloon) |
| 19 | `e9f7e9927c4a675d5974432c3a6e2ebf` | BEFORE | `EVENT_25c7847b98aa7b4eacbdd1b6b1fdc85c` (slipped) | `EVENT_1f6a93040c9eb179e132f342d0171689` (end) | `ENTITY_fdea14753b266160e8fc32f35987f3a5` (Gibraltar, Gibraltar, Gibraltar) |
| 20 | `b3e3edb78265c71ecd519a8c1d5ec96b` | BEFORE | `EVENT_98e950fd2fc020684ae4d7281d7b609a` (threw) | `EVENT_e74cd82b85bc2ff7645b62525a3eb85e` (ended) | `ENTITY_ad0a55777fba41b5fa74f7ef6a16fc8d` (Sandomierz, Sandomierz, Sandomierz, Sandomierz, Sandomierz, Sandomierz) |
| 21 | `fd580b38915316b118de3633042af2a1` | BEFORE | `EVENT_26639d511b1c894b4ea1a8efb6080fd6` (came) | `EVENT_ba24b6eb08dd6b3af8a96c2fe65abaa1` (ended) | `ENTITY_580dcdb5af6271d9d0fccd49cd7185ce` (Rozafa Castle) |
| 22 | `66103145709a4765be54c1d818523f4b` | BEFORE | `EVENT_e2f79f56ef51ef915947f8cc3cca2b4d` (riding) | `EVENT_f6260e6fa69b355c0eabc571a3b5b5bf` (end) | `ENTITY_79eddb1001c9d36f343d6cca3f6316cb` (Amman, Amman) |
| 23 | `4d3c10942365d57eed09af50d7f05b4d` | BEFORE | `EVENT_d900a4ad004990aa2ddd49e9b72590cd` (sailed) | `EVENT_9a23caf99e48b3f739032f723e133bcc` (cease) | `ENTITY_31bfdd6265de3933df23559756330823` (Alexandria, Alexandria) |
| 24 | `0259dfb7eeb9ab20f5e86b2a3e2093ce` | BEFORE | `EVENT_c8ca854d2be78b6961f3bced1765bfcd` (expedition) | `EVENT_2282b8e8879d854f694ae59e8faf8647` (ending) | `ENTITY_b377e51a35ce07ce94f3d889a568c1d4` (Belgium, Belgium, Belgium, Belgium) |
| 25 | `50530ded21d9691582331f64fc658dab` | BEFORE | `EVENT_a4c3dd82ae968eaa68497186d80ce27a` (kicked off) | `EVENT_2d0960179a76bf26fb01ad79c2ac6050` (ended) | `ENTITY_7b0a86fb85eee353928d1877a9994436` (Nashville) |

## Reproduce

```bash
python3 event_temporal_mining/src/generate_graph_mining_review_report.py \
  --arg-path MAVEN-Arg/train.jsonl \
  --ere-path MAVEN_ERE/train.jsonl \
  --output-path event_temporal_mining/results/graph_mining_review_report.md
```
