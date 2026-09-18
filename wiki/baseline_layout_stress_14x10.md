# Unused-layout + pie + heatmap stress (14x10)

Companion-mode AUTHORING + OBSERVATION of the 14 renderer_v3 layouts never painted in Amex PDF replicas, plus unused chart types pie and heatmap. The original 160-slide strict freeze overflowed 9 leftover non-pie slides; the four dense pies (s146/s147/s148/s150) pack at ordinary_values 18 (#356). The published deck is still DEGRADED (`--no-strict`) for those leftover compositions. HTML was not hand-edited. #354 later added kernel wrap packing for max-cardinality `process_flow` / `timeline` / `data_pipeline` (linear subset recapture below); remaining overflow families are unchanged.

## #354 wrap recapture (linear recipes)

Kernel wrap packing (#354) re-renders the linear subset strict from `tests/fixtures/renderer_v3/linear_wrap_stress.json`. s005 / s016 / s017 / s020 / s055 / s056 / s059 now freeze as the recipe (not list fallback) at type floors. This leftover still fits s056 6x3 so it wraps as the recipe; 6x3+all-details may still overflow if leftover is gone (legal overflow). Recapture: `artifacts/issue_354_linear_wrap/` at 1920×1080, stacked-deck transforms cleared, no image scoring, no D314 rewrite. Remaining overflow families (feedback_loop / state_transition) are unchanged. Identity hashes below are the original 160-slide degraded capture (full deck not re-run).

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tests/fixtures/renderer_v3/linear_wrap_stress.json` | 45835 | `85714abf165b31afe90eead778deb104d9a8963dfa80d10a855350bfd19b905b` |
| `artifacts/issue_354_linear_wrap/html/slide_005.png` | 44736 | `b06bd84aaeaee0dde19d6325209bf9e2f389631db179e648881cf81d2f5f0bb7` |
| `artifacts/issue_354_linear_wrap/html/slide_016.png` | 37382 | `b00dd27146fe6221979eae2c40175f4fc5d8511705048c86832aa6934b6073c1` |
| `artifacts/issue_354_linear_wrap/html/slide_017.png` | 49768 | `78c7c502c82235e76e41a296bc9aac1cc4e47073f9aeedce8aae06b9c27f6555` |
| `artifacts/issue_354_linear_wrap/html/slide_020.png` | 51907 | `a8f784b3de0be927ec906dbda7135287f24adfa21d0769c670aacfc46ab2e516` |
| `artifacts/issue_354_linear_wrap/html/slide_055.png` | 53272 | `33f4ecfbdfdb07a7d75c905d163df14eedef23e7e869f5a7d3916226db254c70` |
| `artifacts/issue_354_linear_wrap/html/slide_056.png` | 81562 | `a10da9aa09cc345efce5a0064c1d731f9deaeeca2d0b414f584be137c78eac88` |
| `artifacts/issue_354_linear_wrap/html/slide_059.png` | 49453 | `0fb3817bec48b258be3d9db695ffe879b1245a68ebb2be1c7be18293f9f642df` |

## Identity

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `passes/pass_01/renderer_v3_out/presentation.html` | 784425 | `2c8aac6cfdf133e8a9a17abdd393bbc6182571c25004522699a9c5c939d89779` |
| `passes/pass_01/renderer_v3_out/run_meta.json` | 629448 | `123dc5c4cb758420796b68ea0fddeff4b3a6cd2fcdb6d35777910962cdcf148e` |

- handoff: 160 slides, `meta.handoff_schema_version=1`, evidence `layout-stress-p001`..`layout-stress-p160` (locator.kind `note`)
- renderer_v3 3.0.0; `run_meta.status=degraded`; `ok=False`; `options.strict=False`
- severity_counts: {'info': 163, 'warning': 1, 'error': 18}; 18 `plan.unresolved_overflow` errors on 9 leftover slides (body+subtitle pairs). Zero pie_chart overflows. s148 relocates two `context_labels` below the plot (`plan.surface_relocated`).
- HTML identity: 160 unique `data-slide-number` 1..160; each `data-layout` matches authored `layout_type`; pie/heatmap both `data-layout=single_chart` with `data-chart-type` pie vs heatmap (not donut)
- Capture: 160 HTML PNGs 1920x1080, deviceScaleFactor=1, stacked-deck fit transforms cleared; `wait_for_paint_ready_charts` on pie slides only; contact sheet 16x10; 160-row `comparison_manifest.json`

## Counts

Original 160-slide `--no-strict` observation (Identity hashes above; #356 pies packed):

- painted clean: 149
- overflow-fallback: 9
- validation-shrunk: 2
- total: 160 = 149 + 9 + 2

After #354 wrap recapture of the linear subset, s005 / s016 / s017 / s020 / s055 / s056 / s059 freeze as recipes. Remaining overflow-fallback in this ledger: s039 (feedback_loop), s127 (state_transition). Full 160-slide HTML was not re-captured.

Each of the 14 layouts plus pie and heatmap appears exactly 10 times. Families are not paraphrases: cardinality, optional fields, and domain differ per variation.

## 1. process_flow

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 001 | ITIL 4 Incident Management | 2 steps | detail 0/2 | painted clean | process-flow horizontal step cards with connectors. |
| 2 | 002 | NIST CSF 2.0 | 3 steps | detail 3/3 | painted clean | process-flow horizontal step cards with connectors. |
| 3 | 003 | SHRM staffing funnel | 4 steps | detail 4/4 | painted clean | process-flow horizontal step cards with connectors. |
| 4 | 004 | FDA CDRH 510(k) | 5 steps | detail 0/5 | painted clean | process-flow horizontal step cards with connectors. |
| 5 | 005 | Toyota Production System | 6 steps | detail 6/6 | painted clean | process-flow wrap 3+3 with sequential connectors; all 6 details at type floor. |
| 6 | 006 | Deming PDCA | 6 steps | detail 0/6 | painted clean | process-flow horizontal step cards with connectors. |
| 7 | 007 | ITIL 4 Incident Management | 3 steps | detail 0/3 | painted clean | process-flow horizontal step cards with connectors. |
| 8 | 008 | COSO Internal Control | 4 steps | detail 4/4 | painted clean | process-flow horizontal step cards with connectors. |
| 9 | 009 | SAFe PI Planning | 5 steps | detail 0/5 | painted clean | process-flow horizontal step cards with connectors. |
| 10 | 010 | ITIL 4 Incident Management | 2 steps | detail 1/2 | painted clean | process-flow horizontal step cards with connectors. |

## 2. timeline

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 011 | IETF RFC 791 / CERN WWW | 2 milestones | detail 2/2 | painted clean | timeline recipe (not fallback). |
| 2 | 012 | Public communications history | 3 milestones | detail 0/3 | painted clean | timeline recipe (not fallback). |
| 3 | 013 | PCI DSS versions | 4 milestones | detail 4/4 | painted clean | timeline recipe (not fallback). |
| 4 | 014 | IETF RFC HTTP chronology | 5 milestones | detail 0/5 | painted clean | timeline recipe (not fallback). |
| 5 | 015 | GDPR / EU data protection | 6 milestones | detail 0/6 | painted clean | timeline recipe (not fallback). |
| 6 | 016 | IPCC assessment reports | 7 milestones | detail 0/7 | painted clean | timeline wrap 4+3; authored year labels unchanged. |
| 7 | 017 | Kubernetes / CNCF releases | 8 milestones | detail 8/8 | painted clean | timeline wrap 4+4; all 8 details at type floor. |
| 8 | 018 | HIPAA / HITECH | 4 milestones | detail 0/4 | painted clean | timeline recipe (not fallback). |
| 9 | 019 | NIST CSF 2.0 | 3 milestones | detail 0/3 | painted clean | timeline recipe (not fallback). |
| 10 | 020 | PCI DSS versions | 8 milestones | detail 0/8 | painted clean | timeline wrap 4+4; wrapping time_label kept verbatim. |

## 3. decision_tree

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 021 | ITIL incident triage | 3 nodes | decisions 1; ways [2]; detail 0 | painted clean | decision-tree bands and rel-node cards. |
| 2 | 022 | ITIL incident triage | 4 nodes | decisions 1; ways [3]; detail 0 | validation-shrunk | Typed graph shrink before render: a 3-way root cannot occupy 5 unique nodes without shared targets; authored 4 nodes. Recipe painted a decision-tree (not overflow). |
| 3 | 023 | HIPAA Privacy Rule | 7 nodes | decisions 3; ways [2]; detail 0 | painted clean | decision-tree bands and rel-node cards. |
| 4 | 024 | FDA device classification | 9 nodes | decisions 3; ways [2, 3]; detail 0 | painted clean | decision-tree bands and rel-node cards. |
| 5 | 025 | OWASP ASVS 4.0 | 11 nodes | decisions 4; ways [2, 3]; detail 0 | painted clean | decision-tree bands and rel-node cards. |
| 6 | 026 | GDPR Article 6 | 13 nodes | decisions 4; ways [3]; detail 0 | validation-shrunk | Typed graph shrink before render: 15-node all-3-way at depth 4 is impossible (4 ternary decisions = 13 nodes); authored 13. Recipe painted a decision-tree. |
| 7 | 027 | GDPR Chapter V | 6 nodes | decisions 2; ways [2, 3]; detail 0 | painted clean | decision-tree bands and rel-node cards. |
| 8 | 028 | COSO / SOX ICFR | 8 nodes | decisions 3; ways [2, 3]; detail 5 | painted clean | decision-tree bands and rel-node cards. |
| 9 | 029 | RACI | 4 nodes | decisions 1; ways [3]; detail 1 | painted clean | decision-tree bands and rel-node cards. |
| 10 | 030 | PCI DSS / HIPAA scoping | 10 nodes | decisions 4; ways [2, 3]; detail 0 | painted clean | decision-tree bands and rel-node cards. |

## 4. feedback_loop

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 031 | Deming PDCA | 3 procedural | detail 0; rel 0; effect 0 | painted clean | feedback_loop recipe (not fallback). |
| 2 | 032 | ITIL practices | 4 procedural | detail 0; rel 0; effect 0 | painted clean | feedback_loop recipe (not fallback). |
| 3 | 033 | Boyd OODA | 5 procedural | detail 5; rel 0; effect 0 | painted clean | feedback_loop recipe (not fallback). |
| 4 | 034 | ITIL CSI | 8 procedural | detail 2; rel 0; effect 0 | painted clean | feedback_loop recipe (not fallback). |
| 5 | 035 | Causal spend loop | 3 causal | detail 0; rel 0; effect 3 | painted clean | feedback_loop recipe (not fallback). |
| 6 | 036 | Capacity balancing loop | 4 causal | detail 0; rel 0; effect 4 | painted clean | feedback_loop recipe (not fallback). |
| 7 | 037 | Toyota TPS | 5 causal | detail 0; rel 5; effect 5 | painted clean | feedback_loop recipe (not fallback). |
| 8 | 038 | NIST CSF Detect/Respond | 6 causal | detail 2; rel 0; effect 6 | painted clean | feedback_loop recipe (not fallback). |
| 9 | 039 | ITIL / ISO 31000 | 8 causal | detail 0; rel 0; effect 8 | overflow-fallback | Freeze overflow; ordered-list fallback with loop-classification. Max 8 wrapping causal items exceed the feedback_loop floor. |
| 10 | 040 | Porter price-volume | 3 causal | detail 0; rel 0; effect 3 | painted clean | feedback_loop recipe (not fallback). |

## 5. layered_architecture

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 041 | Client/server | 2 layers x widths [1, 1] | detail 0/2 | painted clean | layered_architecture recipe (no arrows). |
| 2 | 042 | Edge vs origin | 2 layers x widths [4, 4] | detail 0/8 | painted clean | layered_architecture recipe (no arrows). |
| 3 | 043 | IETF stack | 3 layers x widths [2, 2, 2] | detail 2/6 | painted clean | layered_architecture recipe (no arrows). |
| 4 | 044 | TOGAF ADM | 3 layers x widths [3, 3, 3] | detail 0/9 | painted clean | layered_architecture recipe (no arrows). |
| 5 | 045 | TOGAF-style domains | 4 layers x widths [4, 4, 4, 4] | detail 16/16 | painted clean | layered_architecture recipe (no arrows). |
| 6 | 046 | Layered DDD | 4 layers x widths [1, 1, 1, 1] | detail 0/4 | painted clean | layered_architecture recipe (no arrows). |
| 7 | 047 | NIST CSF 2.0 | 3 layers x widths [4, 4, 4] | detail 0/12 | painted clean | layered_architecture recipe (no arrows). |
| 8 | 048 | Kubernetes planes | 2 layers x widths [2, 2] | detail 0/4 | painted clean | layered_architecture recipe (no arrows). |
| 9 | 049 | Kubernetes / CNCF | 4 layers x widths [2, 2, 2, 2] | detail 0/8 | painted clean | layered_architecture recipe (no arrows). |
| 10 | 050 | One-word architecture | 4 layers x widths [4, 4, 4, 4] | detail 0/16 | painted clean | layered_architecture recipe (no arrows). |

## 6. data_pipeline

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 051 | ETL | 2 stages x [1, 1] | transfer 0; detail 0 | painted clean | data_pipeline recipe (not fallback). |
| 2 | 052 | Medallion ingest/serve | 2 stages x [3, 3] | transfer 1; detail 0 | painted clean | data_pipeline recipe (not fallback). |
| 3 | 053 | Medallion | 3 stages x [2, 2, 2] | transfer 2; detail 0 | painted clean | data_pipeline recipe (not fallback). |
| 4 | 054 | ML scoring chain | 4 stages x [1, 1, 1, 1] | transfer 3; detail 0 | painted clean | data_pipeline recipe (not fallback). |
| 5 | 055 | NIST Detect/Respond | 5 stages x [2, 2, 2, 2, 2] | transfer 4; detail 0 | painted clean | data_pipeline wrap 3+2; transfer labels retained. |
| 6 | 056 | DAMA-style pipeline | 6 stages x [3, 3, 3, 3, 3, 3] | transfer 5; detail 18 | painted clean | data_pipeline wrap 3+3; 6x3 + transfers + details still fit leftover at floors. |
| 7 | 057 | SOX close pipeline | 4 stages x [3, 3, 3, 3] | transfer 3; detail 0 | painted clean | data_pipeline recipe (not fallback). |
| 8 | 058 | Three-stage chain | 3 stages x [1, 1, 1] | transfer 0; detail 0 | painted clean | data_pipeline recipe (not fallback). |
| 9 | 059 | Index pipeline | 6 stages x [1, 1, 1, 1, 1, 1] | transfer 5; detail 0 | painted clean | data_pipeline wrap 3+3; 6x1 chain at type floor. |
| 10 | 060 | HIPAA TPO | 2 stages x [3, 3] | transfer 0; detail 6 | painted clean | data_pipeline recipe (not fallback). |

## 7. stakeholder_map

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 061 | GDPR controller | 1 focal + 2 spokes | dirs undirected; rel 2; detail 0 | painted clean | stakeholder_map hub-spoke recipe. |
| 2 | 062 | PCI DSS network | 1 focal + 3 spokes | dirs to_focal; rel 3; detail 0 | painted clean | stakeholder_map hub-spoke recipe. |
| 3 | 063 | NIST CSF Govern | 1 focal + 4 spokes | dirs from_focal; rel 4; detail 0 | painted clean | stakeholder_map hub-spoke recipe. |
| 4 | 064 | EU MDR actors | 1 focal + 5 spokes | dirs bidirectional; rel 5; detail 0 | painted clean | stakeholder_map hub-spoke recipe. |
| 5 | 065 | SAFe PI stakeholders | 1 focal + 6 spokes | dirs bidirectional,from_focal,to_focal,undirected; rel 6; detail 0 | painted clean | stakeholder_map hub-spoke recipe. |
| 6 | 066 | COSO / SOX board | 1 focal + 7 spokes | dirs bidirectional,from_focal,to_focal,undirected; rel 7; detail 0 | painted clean | stakeholder_map hub-spoke recipe. |
| 7 | 067 | Kubernetes control plane | 1 focal + 8 spokes | dirs bidirectional,from_focal,to_focal,undirected; rel 8; detail 8 | painted clean | stakeholder_map hub-spoke recipe. |
| 8 | 068 | Porter five forces | 1 focal + 4 spokes | dirs bidirectional,from_focal,to_focal,undirected; rel 4; detail 0 | painted clean | stakeholder_map hub-spoke recipe. |
| 9 | 069 | GDPR DPO | 1 focal + 3 spokes | dirs bidirectional,from_focal,to_focal; rel 3; detail 0 | painted clean | stakeholder_map hub-spoke recipe. |
| 10 | 070 | One-word stakeholders | 1 focal + 8 spokes | dirs bidirectional,from_focal,to_focal,undirected; rel 8; detail 0 | painted clean | stakeholder_map hub-spoke recipe. |

## 8. quadrant_matrix

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 071 | BCG matrix | 1 items | occupied high/low=1 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |
| 2 | 072 | BCG matrix | 4 items | occupied high/high=1, high/low=1, low/high=1, low/low=1 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |
| 3 | 073 | Eisenhower matrix | 8 items | occupied high/high=3, high/low=1, low/high=3, low/low=1 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |
| 4 | 074 | ISO 31000 | 12 items | occupied high/high=3, high/low=3, low/high=3, low/low=3 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |
| 5 | 075 | GE/McKinsey-style | 16 items | occupied high/high=4, high/low=4, low/high=4, low/low=4 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |
| 6 | 076 | Value/effort | 6 items | occupied high/high=3, low/high=3 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |
| 7 | 077 | COSO control design | 9 items | occupied high/high=3, high/low=2, low/high=2, low/low=2 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |
| 8 | 078 | BCG matrix | 4 items | occupied high/high=1, high/low=1, low/high=1, low/low=1 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |
| 9 | 079 | BCG matrix | 16 items | occupied high/high=4, high/low=4, low/high=4, low/low=4 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |
| 10 | 080 | BCG matrix | 2 items | occupied high/low=2 | painted clean | quadrant_matrix four labelled bands; empty quadrants stay labelled. |

## 9. quotation

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 081 | Peter Drucker | 1 quotes; paras [1] | attr ['name']; evidence_id 0 | painted clean | quotation blockquotes with attribution meta. |
| 2 | 082 | Stafford Beer POSIWID | 1 quotes; paras [1] | attr ['name+role']; evidence_id 0 | painted clean | quotation blockquotes with attribution meta. |
| 3 | 083 | W. Edwards Deming | 1 quotes; paras [1] | attr ['name+role+organization']; evidence_id 0 | painted clean | quotation blockquotes with attribution meta. |
| 4 | 084 | Gettysburg Address | 1 quotes; paras [3] | attr ['name']; evidence_id 0 | painted clean | quotation blockquotes with attribution meta. |
| 5 | 085 | Drucker and Deming | 2 quotes; paras [1, 1] | attr ['name+role', 'name']; evidence_id 0 | painted clean | quotation blockquotes with attribution meta. |
| 6 | 086 | Crosby, Deming, Drucker | 3 quotes; paras [1, 1, 1] | attr ['name+role+organization', 'name+role+organization', 'name+role+organization']; evidence_id 0 | painted clean | quotation blockquotes with attribution meta. |
| 7 | 087 | ITIL 4 | 3 quotes; paras [1, 1, 1] | attr ['name', 'name', 'name']; evidence_id 0 | painted clean | quotation blockquotes with attribution meta. |
| 8 | 088 | GDPR Articles 6 and 7 | 2 quotes; paras [1, 1] | attr ['name', 'name']; evidence_id 2 | painted clean | quotation blockquotes with attribution meta. |
| 9 | 089 | NIST CSF 2.0 | 1 quotes; paras [2] | attr ['name+organization']; evidence_id 0 | painted clean | quotation blockquotes with attribution meta. |
| 10 | 090 | Gettysburg / ITIL / GDPR | 3 quotes; paras [3, 3, 3] | attr ['name+role+organization', 'name+role+organization', 'name+role+organization']; evidence_id 0 | painted clean | quotation blockquotes with attribution meta. |

## 10. evidence_review

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 091 | NIST CSF 2.0 | 1 findings | evidence_ids [1] | painted clean | evidence_review findings; no source_footer. |
| 2 | 092 | PCI DSS 4.0 | 2 findings | evidence_ids [1, 1] | painted clean | evidence_review findings; no source_footer. |
| 3 | 093 | GDPR / Schrems II | 3 findings | evidence_ids [1, 2, 1] | painted clean | evidence_review findings; no source_footer. |
| 4 | 094 | HIPAA | 4 findings | evidence_ids [1, 1, 1, 1] | painted clean | evidence_review findings; no source_footer. |
| 5 | 095 | COSO 2013 | 5 findings | evidence_ids [1, 1, 1, 1, 1] | painted clean | evidence_review findings; no source_footer. |
| 6 | 096 | NIST CSF 2.0 | 6 findings | evidence_ids [4, 4, 4, 4, 4, 4] | painted clean | evidence_review findings; no source_footer. |
| 7 | 097 | ITIL 4 | 3 findings | evidence_ids [1, 1, 1] | painted clean | evidence_review findings; no source_footer. |
| 8 | 098 | ISO 31000 | 2 findings | evidence_ids [1, 1] | painted clean | evidence_review findings; no source_footer. |
| 9 | 099 | Deming PDCA | 6 findings | evidence_ids [1, 1, 1, 1, 1, 1] | painted clean | evidence_review findings; no source_footer. |
| 10 | 100 | FDA 510(k) | 1 findings | evidence_ids [4] | painted clean | evidence_review findings; no source_footer. |

## 11. risk_opportunity_review

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 101 | ISO 31000 | 1 risks + 1 opportunities | detail r0 o0 | painted clean | risk_opportunity_review two groups. |
| 2 | 102 | HIPAA | 2 risks + 2 opportunities | detail r2 o2 | painted clean | risk_opportunity_review two groups. |
| 3 | 103 | PCI DSS 4.0 | 3 risks + 3 opportunities | detail r0 o0 | painted clean | risk_opportunity_review two groups. |
| 4 | 104 | Porter five forces | 4 risks + 2 opportunities | detail r0 o0 | painted clean | risk_opportunity_review two groups. |
| 5 | 105 | McKinsey 7S | 2 risks + 4 opportunities | detail r0 o0 | painted clean | risk_opportunity_review two groups. |
| 6 | 106 | NIST CSF 2.0 | 6 risks + 6 opportunities | detail r6 o6 | painted clean | risk_opportunity_review two groups. |
| 7 | 107 | ITIL 4 | 3 risks + 3 opportunities | detail r0 o0 | painted clean | risk_opportunity_review two groups. |
| 8 | 108 | GDPR Article 6 | 1 risks + 6 opportunities | detail r0 o0 | painted clean | risk_opportunity_review two groups. |
| 9 | 109 | OWASP ASVS | 6 risks + 1 opportunities | detail r0 o0 | painted clean | risk_opportunity_review two groups. |
| 10 | 110 | Porter five forces | 5 risks + 5 opportunities | detail r0 o0 | painted clean | risk_opportunity_review two groups. |

## 12. recommendation_case

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 111 | NIST CSF 2.0 | 1 rationales | rationale detail 0 | painted clean | recommendation_case plus rationale grid; no takeaway. |
| 2 | 112 | NIST CSF 2.0 | 2 rationales | rationale detail 2 | painted clean | recommendation_case plus rationale grid; no takeaway. |
| 3 | 113 | FDA 510(k) | 3 rationales | rationale detail 0 | painted clean | recommendation_case plus rationale grid; no takeaway. |
| 4 | 114 | PCI DSS 4.0 | 4 rationales | rationale detail 0 | painted clean | recommendation_case plus rationale grid; no takeaway. |
| 5 | 115 | RACI | 5 rationales | rationale detail 0 | painted clean | recommendation_case plus rationale grid; no takeaway. |
| 6 | 116 | GDPR Article 6 | 6 rationales | rationale detail 6 | painted clean | recommendation_case plus rationale grid; no takeaway. |
| 7 | 117 | GDPR Chapter V | 3 rationales | rationale detail 0 | painted clean | recommendation_case plus rationale grid; no takeaway. |
| 8 | 118 | Deming PDCA | 1 rationales | rationale detail 0 | painted clean | recommendation_case plus rationale grid; no takeaway. |
| 9 | 119 | SAFe PI Planning | 6 rationales | rationale detail 0 | painted clean | recommendation_case plus rationale grid; no takeaway. |
| 10 | 120 | COSO | 4 rationales | rationale detail 2 | painted clean | recommendation_case plus rationale grid; no takeaway. |

## 13. state_transition

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 121 | ITIL 4 | 1/1 blocks, 0 steps | step detail 0 | painted clean | state_transition before/after surfaces. |
| 2 | 122 | HIPAA / HITECH | 2/2 blocks, 1 steps | step detail 1 | painted clean | state_transition before/after surfaces. |
| 3 | 123 | GDPR / Schrems II | 3/3 blocks, 2 steps | step detail 2 | painted clean | state_transition before/after surfaces. |
| 4 | 124 | Kubernetes / CNCF | 4/4 blocks, 4 steps | step detail 4 | painted clean | state_transition before/after surfaces. |
| 5 | 125 | PCI DSS 4.0 | 1/1 blocks, 4 steps | step detail 4 | painted clean | state_transition before/after surfaces. |
| 6 | 126 | COSO 2013 | 4/4 blocks, 0 steps | step detail 0 | painted clean | state_transition before/after surfaces. |
| 7 | 127 | ITIL 4 | 1/1 blocks, 1 steps | step detail 0 | overflow-fallback | Freeze overflow; card-comp-fallback card-comp-overflow. Wrapping before/after headings plus a step exceed the state_transition floor. |
| 8 | 128 | NIST CSF 2.0 | 2/2 blocks, 2 steps | step detail 0 | painted clean | state_transition before/after surfaces. |
| 9 | 129 | OWASP ASVS | 1/4 blocks, 0 steps | step detail 0 | painted clean | state_transition before/after surfaces. |
| 10 | 130 | SAFe PI Planning | 4/1 blocks, 0 steps | step detail 0 | painted clean | state_transition before/after surfaces. |

## 14. strategy_board

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 131 | PCI DSS 4.0 | bands 0; pillars 2; footer 0 | pillar items [1, 1] | painted clean | strategy_board mission/pillars recipe. |
| 2 | 132 | NIST CSF 2.0 | bands 2; pillars 2; footer 0 | pillar items [1, 1] | painted clean | strategy_board mission/pillars recipe. |
| 3 | 133 | McKinsey 7S | bands 0; pillars 3; footer 0 | pillar items [2, 2, 2] | painted clean | strategy_board mission/pillars recipe. |
| 4 | 134 | GDPR Article 6 | bands 1; pillars 4; footer 0 | pillar items [1, 1, 1, 1] | painted clean | strategy_board mission/pillars recipe. |
| 5 | 135 | TOGAF ADM | bands 2; pillars 4; footer 2 | pillar items [6, 6, 6, 6] | painted clean | strategy_board mission/pillars recipe. |
| 6 | 136 | Crosby quality | bands 0; pillars 2; footer 2 | pillar items [1, 1] | painted clean | strategy_board mission/pillars recipe. |
| 7 | 137 | RACI / ITIL | bands 0; pillars 2; footer 0 | pillar items [1, 1] | painted clean | strategy_board mission/pillars recipe. |
| 8 | 138 | HIPAA TPO | bands 0; pillars 4; footer 0 | pillar items [1, 1, 1, 1] | painted clean | strategy_board mission/pillars recipe. |
| 9 | 139 | SAFe PI Planning | bands 0; pillars 2; footer 0 | pillar items [6, 6] | painted clean | strategy_board mission/pillars recipe. |
| 10 | 140 | IPCC | bands 1; pillars 3; footer 2 | pillar items [3, 3, 3] | painted clean | strategy_board mission/pillars recipe. |

## 15. pie

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 141 | IEA electricity mix | 2 slices | color 0; short_label 0; context_labels 0; annotations 0; support False | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. |
| 2 | 142 | IEA electricity mix | 3 slices | color 0; short_label 0; context_labels 0; annotations 0; support False | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. |
| 3 | 143 | IEA generation mix | 4 slices | color 4; short_label 0; context_labels 0; annotations 0; support False | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. |
| 4 | 144 | IEA generation mix | 5 slices | color 0; short_label 5; context_labels 0; annotations 0; support False | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. |
| 5 | 145 | IEA electricity mix | 6 slices | color 0; short_label 0; context_labels 0; annotations 0; support False | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. |
| 6 | 146 | IEA generation mix | 8 slices | color 0; short_label 8; context_labels 0; annotations 0; support False | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. Eight-way names outside; percents inside when ≥20% else with the name. Pack at ordinary_values 18 (#356). |
| 7 | 147 | IEA electricity mix | 3 slices | color 0; short_label 0; context_labels 0; annotations 0; support False | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. Zero wedge still named (Unspecified 0%) beside the name (#356). |
| 8 | 148 | IEA generation mix | 4 slices | color 0; short_label 0; context_labels 2; annotations 0; support False | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. Two context_labels freeze as one below-plot row inside pad_b; view_h unchanged (#356). |
| 9 | 149 | IEA generation mix | 5 slices | color 0; short_label 0; context_labels 0; annotations 1; support False | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. |
| 10 | 150 | IEA generation mix | 8 slices | color 0; short_label 0; context_labels 0; annotations 0; support True | painted clean | single_chart pie Chart.js + noscript SVG + D247 semantic table; identity data-chart-type=pie. Eight one-word slices plus independent support_table keep D47 plot floor and complete table (#356). |

## 16. heatmap

| v | slide | domain / source | cardinality | optional fields | classification | observation |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 151 | IEA low-carbon share | 1x1 | finite 1; missing 0; scale generated; context_labels 0; annotations 0; col short_label 0 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. |
| 2 | 152 | Correlation-style matrix | 2x2 | finite 4; missing 0; scale generated; context_labels 0; annotations 0; col short_label 0 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. |
| 3 | 153 | NIST CSF tiers | 3x4 | finite 11; missing 1; scale generated; context_labels 0; annotations 0; col short_label 0 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. |
| 4 | 154 | NIST CSF 2.0 | 6x6 | finite 36; missing 0; scale generated; context_labels 0; annotations 0; col short_label 0 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. |
| 5 | 155 | NIST-ish occupancy | 12x12 | finite 143; missing 1; scale generated; context_labels 0; annotations 0; col short_label 12 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. 12 wrapping column labels used authored short_label C01–C12 (`plan.short_label_used`); no ellipsis. |
| 6 | 156 | NIST CSF tiers | 4x4 | finite 16; missing 0; scale fixed; context_labels 0; annotations 0; col short_label 0 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. |
| 7 | 157 | NIST CSF 2.0 | 5x3 | finite 10; missing 5; scale generated; context_labels 0; annotations 0; col short_label 0 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. |
| 8 | 158 | IPCC-ish occupancy | 2x8 | finite 16; missing 0; scale generated; context_labels 0; annotations 0; col short_label 0 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. |
| 9 | 159 | NIST CSF 2.0 | 8x2 | finite 16; missing 0; scale generated; context_labels 0; annotations 0; col short_label 2 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. |
| 10 | 160 | NIST CSF 2.0 | 4x4 | finite 16; missing 0; scale generated; context_labels 0; annotations 2; col short_label 0 | painted clean | single_chart native HTML heatmap-table (not Chart.js); identity data-chart-type=heatmap. |

## Closed-set fields not legally exercised

- `strategy_board` footer length 6: v5 authored 2 footer items (schema allows 1-6). Pillars already at 4x6 plus 2 bands; a 6-item footer was not packed.
- pie `support` `metric_strip`: v10 used independent `support_table` (legal). metric_strip remains unpainted in this set.
- heatmap `context_labels`: none authored. v10 used two `category_range` annotations instead.
- heatmap annotation anchors `chart` and `category`: only `category_range` used (chart/category/category_range are the legal heatmap set).
- pie `short_label` combined with authored `color` on the same slice: v3 colors without short_label; v4/v6 short_label without color.
- Repair-only fields (`refs_repaired`, `groups_repaired`, `support_repaired`, `provenance_unavailable`) were correctly omitted.
- Hierarchy and donut are out of scope (already painted on Q4 2021).

## Capture artifacts

- `passes/pass_01/compare/html/slide_001.png` .. `slide_160.png` (each 1920x1080)
- `passes/pass_01/compare/contact_sheet.png` (labeled 16x10 grid)
- `passes/pass_01/compare/comparison_manifest.json` (160 rows: slide_number, family, layout_type, chart_type or null, variation 1-10, domain, classification)

