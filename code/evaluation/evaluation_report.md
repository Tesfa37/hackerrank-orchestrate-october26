# Public sample evaluation

Generated 2026-10-24T21:11:17.151692+00:00 from `sample_predictions_partial.csv` against `sample_output.csv`.

The public examples are development data. These measurements do not establish hidden evaluation accuracy.

## Prediction coverage

Coverage records which requests received a row; it is separate from agreement with expected answers.

| Coverage measure | Result |
| --- | ---: |
| Expected / returned cases | 32 / 19 |
| Expected cases with a prediction | 19/32 (59.38%) |
| Missing / unexpected case IDs | 13 / 0 |
| Exact case-ID coverage | Fail |
| Output contract | Fail |

## Accuracy across every expected request

All expected requests remain in the primary case-accuracy denominators. A missing prediction is incorrect.

| Accuracy measure | Result |
| --- | ---: |
| Deletion-status accuracy | 59.38% (19/32) |
| Exact case accuracy (status and ordered steps) | 21.88% (7/32) |
| Exact step-sequence accuracy | 21.88% (7/32) |
| Step precision / recall / F1 | 94.96% / 58.55% / 72.44% |
| Exact content-matched / predicted / expected steps | 113 / 119 / 193 |
| Aligned field accuracy | 54.99% |

Supplementary returned-row status agreement is 19/19 (100.00%). It excludes missing expected rows and must not replace the primary all-request accuracy.

## Metric definitions

Primary case metrics divide by every expected request; missing rows count as incorrect. Unexpected IDs fail coverage/contract checks and their steps count as false positives. Exact sequence compares the entire ordered step array, including numbering, but scores status separately. Step precision/recall/F1 compare multisets of the six content fields, excluding `step_no`; citations count as content, and recall includes expected steps from every missing request. Fields align by `(phase, system_id, resource_id, operation)`. For duplicate keys, exact steps align first and remaining steps align in input order. Every missing or extra aligned slot is incorrect for all seven fields. Field accuracy divides correct fields by seven times the aligned slot count. Empty-versus-empty step metrics equal 100%, while primary case accuracy still penalizes absent rows.

| Field | Correct / aligned slots | Accuracy |
| --- | ---: | ---: |
| step_no | 88/199 | 44.22% |
| phase | 113/199 | 56.78% |
| system_id | 113/199 | 56.78% |
| resource_id | 113/199 | 56.78% |
| operation | 113/199 | 56.78% |
| state | 113/199 | 56.78% |
| evidence_id | 113/199 | 56.78% |

## Failures

Missing case IDs: case_01, case_02, case_04, case_08, case_12, case_17, case_21, case_24, case_25, case_26, case_27, case_28, case_29.

| Case | Expected status | Predicted status | Expected steps | Predicted steps | Content matches | Sequence match |
| --- | --- | --- | ---: | ---: | ---: | --- |
| case_01 | COMPLETE | None | 1 | 0 | 0 | False |
| case_02 | COMPLETE | None | 1 | 0 | 0 | False |
| case_03 | COMPLETE | COMPLETE | 3 | 2 | 2 | False |
| case_04 | COMPLETE | None | 2 | 0 | 0 | False |
| case_06 | INCOMPLETE | INCOMPLETE | 4 | 3 | 3 | False |
| case_07 | INCOMPLETE | INCOMPLETE | 4 | 9 | 3 | False |
| case_08 | INCOMPLETE | None | 4 | 0 | 0 | False |
| case_09 | INCOMPLETE | INCOMPLETE | 5 | 3 | 3 | False |
| case_10 | INCOMPLETE | INCOMPLETE | 4 | 3 | 3 | False |
| case_12 | INCOMPLETE | None | 5 | 0 | 0 | False |
| case_17 | INCOMPLETE | None | 5 | 0 | 0 | False |
| case_18 | INCOMPLETE | INCOMPLETE | 14 | 12 | 12 | False |
| case_20 | INCOMPLETE | INCOMPLETE | 8 | 6 | 6 | False |
| case_21 | COMPLETE | None | 3 | 0 | 0 | False |
| case_22 | INCOMPLETE | INCOMPLETE | 8 | 7 | 7 | False |
| case_23 | INCOMPLETE | INCOMPLETE | 8 | 6 | 6 | False |
| case_24 | INCOMPLETE | None | 7 | 0 | 0 | False |
| case_25 | COMPLETE | None | 3 | 0 | 0 | False |
| case_26 | COMPLETE | None | 6 | 0 | 0 | False |
| case_27 | COMPLETE | None | 6 | 0 | 0 | False |
| case_28 | COMPLETE | None | 6 | 0 | 0 | False |
| case_29 | INCOMPLETE | None | 14 | 0 | 0 | False |
| case_30 | INCOMPLETE | INCOMPLETE | 14 | 12 | 12 | False |
| case_31 | COMPLETE | COMPLETE | 3 | 2 | 2 | False |
| case_32 | INCOMPLETE | INCOMPLETE | 5 | 4 | 4 | False |

## Independent evaluator regression cases

These fixtures test scoring behavior; reasoning-specific synthetic audits and improvements are documented separately.

1. A missing expected row counts as incorrect in all-request accuracy; an extra prediction separately fails coverage and contributes false-positive steps.
2. A wrong citation keeps resource alignment but lowers evidence-field accuracy and exact-step precision/recall.
3. Reordered steps keep content precision/recall but fail sequence accuracy and canonical-order validation.

## Investigation and validation

All 175 independent regression tests pass, along with Node syntax validation. Participant dataset bytes match the official upstream snapshot; inputs and existing credential bindings were not changed. All 518 identities resolve uniquely, including 100 historical request emails. Independent raw inspection found no missing past identifiers or eligible primary-record parsing misses among the account-proof blockers. All 15 PDFs/images received genuine source-only semantic reinspection.

Coverage is separate from accuracy: primary status and exact-sequence scores use all 32 expected cases; unresolved predictions count incorrect. Returned-row status agreement is supplementary, not a replacement for all-case accuracy. Step precision/recall includes citations; missing expected steps remain in recall and aligned-field denominators. Public samples are development data, not hidden-test accuracy.

The strict full run resolves 419/518 requests and deliberately exits 2. The remaining 99 are grouped in [blocker_report.md](blocker_report.md): 69 have negative snapshots without an eligible owned account key, 25 have direct account evidence captured after cutoff, 3 have neither eligible direct primary evidence nor a complete primary scope, and 2 have insufficient media field/access coverage. The original 98 were 69/25/3/1; the additional hold is an archive whose existence was incorrectly treated as current restore permission. No final output.csv is fabricated.

Fixes include known-key absence from a first complete snapshot, unparsed replica-state guards, source/catalog timing, quoted technical keys versus document/ticket aliases, exact textual UTC times, bounded date-only retention, object names versus personal names, stable tombstone references versus direct PII, and archive existence versus restore authorization. Received rejected responses remain quarantined; genuine recovery requires unchanged provider content, original request and attempt provenance, and current validation. Bounded corrective requests carry no expected answers.

Independent synthetic regressions cover: export-only intent (no deletion), historical-email replica exposure (incomplete), future capture (excluded), active sync (disable first), restore-blocked archives (retain), stable-only partial tombstones (unknown, never PII), explicit full tombstone redaction (compliant), complete scoped negatives for an owned key (absent), unparsed replicas (held), retention-date boundary ambiguity (held), and unsafe output destinations (preserved).

The sample run still exposes a reasoning gap for five finance-register rows: explicit retention dates are present, but their business order references are not confidently mapped to a supplied deletion-policy category/condition. This is a policy/record interpretation gap, not an absent document. Three sample subjects have no grounded eligible identity/resource association; other missing cases lack deletion proof or full tombstone-field coverage. Existing object-store findings were not dropped merely to match reference labels: the visible object filename differs from the support attachment, so a same-object alias is unproven.

No hidden accuracy is claimed. Source-fact validation and unit tests do not prove exhaustive discovery. Read blocker_report.md for representative cases, exact missing proofs, capture times and full group membership.

- `.cache/sample_predictions_partial.csv` SHA-256: `93b4af2fdaab0e3ca3e3d6e21c46fa4b110446f256abd34b3c001ebb73e4f19a`

- `.cache/full_predictions_partial.csv` SHA-256: `0bba8ac64fcf3eadfcfe1468ef89fd5fcd9dbbad8815e40f3b7445bd767a288a`
