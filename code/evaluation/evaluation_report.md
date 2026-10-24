# Public sample evaluation

Generated 2026-10-24T23:48:58.909879+00:00 from `sample_predictions_partial.csv` against `sample_output.csv`.

The public examples are development data. These measurements do not establish hidden evaluation accuracy.

## Prediction coverage

Coverage records which requests received a row; it is separate from agreement with expected answers.

| Coverage measure | Result |
| --- | ---: |
| Expected / returned cases | 32 / 23 |
| Expected cases with a prediction | 23/32 (71.88%) |
| Missing / unexpected case IDs | 9 / 0 |
| Exact case-ID coverage | Fail |
| Output contract | Fail |

## Accuracy across every expected request

All expected requests remain in the primary case-accuracy denominators. A missing prediction is incorrect.

| Accuracy measure | Result |
| --- | ---: |
| Deletion-status accuracy | 71.88% (23/32) |
| Exact case accuracy (status and ordered steps) | 25.00% (8/32) |
| Exact step-sequence accuracy | 25.00% (8/32) |
| Step precision / recall / F1 | 97.89% / 72.02% / 82.99% |
| Exact content-matched / predicted / expected steps | 139 / 142 / 193 |
| Aligned field accuracy | 68.73% |

Supplementary returned-row status agreement is 23/23 (100.00%). It excludes missing expected rows and must not replace the primary all-request accuracy.

## Metric definitions

Primary case metrics divide by every expected request; missing rows count as incorrect. Unexpected IDs fail coverage/contract checks and their steps count as false positives. Exact sequence compares the entire ordered step array, including numbering, but scores status separately. Step precision/recall/F1 compare multisets of the six content fields, excluding `step_no`; citations count as content, and recall includes expected steps from every missing request. Fields align by `(phase, system_id, resource_id, operation)`. For duplicate keys, exact steps align first and remaining steps align in input order. Every missing or extra aligned slot is incorrect for all seven fields. Field accuracy divides correct fields by seven times the aligned slot count. Empty-versus-empty step metrics equal 100%, while primary case accuracy still penalizes absent rows.

| Field | Correct / aligned slots | Accuracy |
| --- | ---: | ---: |
| step_no | 109/196 | 55.61% |
| phase | 139/196 | 70.92% |
| system_id | 139/196 | 70.92% |
| resource_id | 139/196 | 70.92% |
| operation | 139/196 | 70.92% |
| state | 139/196 | 70.92% |
| evidence_id | 139/196 | 70.92% |

## Failures

Missing case IDs: case_01, case_02, case_04, case_17, case_21, case_25, case_26, case_27, case_28.

| Case | Expected status | Predicted status | Expected steps | Predicted steps | Content matches | Sequence match |
| --- | --- | --- | ---: | ---: | ---: | --- |
| case_01 | COMPLETE | None | 1 | 0 | 0 | False |
| case_02 | COMPLETE | None | 1 | 0 | 0 | False |
| case_03 | COMPLETE | COMPLETE | 3 | 2 | 2 | False |
| case_04 | COMPLETE | None | 2 | 0 | 0 | False |
| case_06 | INCOMPLETE | INCOMPLETE | 4 | 3 | 3 | False |
| case_07 | INCOMPLETE | INCOMPLETE | 4 | 6 | 3 | False |
| case_08 | INCOMPLETE | INCOMPLETE | 4 | 3 | 3 | False |
| case_09 | INCOMPLETE | INCOMPLETE | 5 | 3 | 3 | False |
| case_10 | INCOMPLETE | INCOMPLETE | 4 | 3 | 3 | False |
| case_17 | INCOMPLETE | None | 5 | 0 | 0 | False |
| case_18 | INCOMPLETE | INCOMPLETE | 14 | 12 | 12 | False |
| case_20 | INCOMPLETE | INCOMPLETE | 8 | 6 | 6 | False |
| case_21 | COMPLETE | None | 3 | 0 | 0 | False |
| case_22 | INCOMPLETE | INCOMPLETE | 8 | 7 | 7 | False |
| case_23 | INCOMPLETE | INCOMPLETE | 8 | 6 | 6 | False |
| case_24 | INCOMPLETE | INCOMPLETE | 7 | 6 | 6 | False |
| case_25 | COMPLETE | None | 3 | 0 | 0 | False |
| case_26 | COMPLETE | None | 6 | 0 | 0 | False |
| case_27 | COMPLETE | None | 6 | 0 | 0 | False |
| case_28 | COMPLETE | None | 6 | 0 | 0 | False |
| case_29 | INCOMPLETE | INCOMPLETE | 14 | 12 | 12 | False |
| case_30 | INCOMPLETE | INCOMPLETE | 14 | 12 | 12 | False |
| case_31 | COMPLETE | COMPLETE | 3 | 2 | 2 | False |
| case_32 | INCOMPLETE | INCOMPLETE | 5 | 4 | 4 | False |

## Confirmed organizer exclusions (evaluation only)

Organizer replies relayed by the user on 2026-10-24 confirm case_39 and case_55 are excluded. Other invalid cases will be excluded, but no complete list was provided; no additional case is excluded here. Evaluation uses only repository evidence and no dataset change was announced. The existing 518-row output requirement remains pending explicit clarification. See [organizer_guidance.md](organizer_guidance.md) for full-run coverage and provenance.

Excluded IDs present in these expected rows: none. The original metrics above retain every original expected row.

| View | Coverage | Status accuracy | Exact sequence |
| --- | ---: | ---: | ---: |
| Original | 23/32 | 71.88% | 25.00% |
| Excluding confirmed cases | 23/32 | 71.88% | 25.00% |

## Independent evaluator regression cases

These fixtures test scoring behavior; reasoning-specific synthetic audits and improvements are documented separately.

1. A missing expected row counts as incorrect in all-request accuracy; an extra prediction separately fails coverage and contributes false-positive steps.
2. A wrong citation keeps resource alignment but lowers evidence-field accuracy and exact-step precision/recall.
3. Reordered steps keep content precision/recall but fail sequence accuracy and canonical-order validation.

## Implementation review and remaining proof gaps

See [sample_mismatch_review.md](sample_mismatch_review.md) for every missing/extra step across all 32 public samples, [case_07_attachment_review.md](case_07_attachment_review.md) for the uploaded-document versus live-ticket correction, [case_01_mre.md](case_01_mre.md) for the participant-file-only account-key reproduction, and [blocker_report.md](blocker_report.md) for full-run missing proofs.

Earlier finance-register fixes preserve explicitly retained business records as constraints without inventing privacy-resource categories or active legal holds. Known privacy resources and uncertain primary account state still undergo policy and uncertainty checks. The conservative whole-account completeness guard remains stricter than the literal contract; removing it does not ground missing account keys or their verification evidence.

Regression fixtures also cover historical identifiers, quoted technical keys, exhaustive negative snapshots, future captures, permitted stable-only tombstones, restore configuration, retention date boundaries, source-scope correction, and separate evaluation exclusions. No expected answers are passed to prediction logic. No final 518-row output.csv is claimed.
