# Public sample evaluation

Generated 2026-10-24T21:30:36.331964+00:00 from `sample_predictions_partial.csv` against `sample_output.csv`.

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
| Step precision / recall / F1 | 95.86% / 72.02% / 82.25% |
| Exact content-matched / predicted / expected steps | 139 / 145 / 193 |
| Aligned field accuracy | 67.70% |

Supplementary returned-row status agreement is 23/23 (100.00%). It excludes missing expected rows and must not replace the primary all-request accuracy.

## Metric definitions

Primary case metrics divide by every expected request; missing rows count as incorrect. Unexpected IDs fail coverage/contract checks and their steps count as false positives. Exact sequence compares the entire ordered step array, including numbering, but scores status separately. Step precision/recall/F1 compare multisets of the six content fields, excluding `step_no`; citations count as content, and recall includes expected steps from every missing request. Fields align by `(phase, system_id, resource_id, operation)`. For duplicate keys, exact steps align first and remaining steps align in input order. Every missing or extra aligned slot is incorrect for all seven fields. Field accuracy divides correct fields by seven times the aligned slot count. Empty-versus-empty step metrics equal 100%, while primary case accuracy still penalizes absent rows.

| Field | Correct / aligned slots | Accuracy |
| --- | ---: | ---: |
| step_no | 109/199 | 54.77% |
| phase | 139/199 | 69.85% |
| system_id | 139/199 | 69.85% |
| resource_id | 139/199 | 69.85% |
| operation | 139/199 | 69.85% |
| state | 139/199 | 69.85% |
| evidence_id | 139/199 | 69.85% |

## Failures

Missing case IDs: case_01, case_02, case_04, case_17, case_21, case_25, case_26, case_27, case_28.

| Case | Expected status | Predicted status | Expected steps | Predicted steps | Content matches | Sequence match |
| --- | --- | --- | ---: | ---: | ---: | --- |
| case_01 | COMPLETE | None | 1 | 0 | 0 | False |
| case_02 | COMPLETE | None | 1 | 0 | 0 | False |
| case_03 | COMPLETE | COMPLETE | 3 | 2 | 2 | False |
| case_04 | COMPLETE | None | 2 | 0 | 0 | False |
| case_06 | INCOMPLETE | INCOMPLETE | 4 | 3 | 3 | False |
| case_07 | INCOMPLETE | INCOMPLETE | 4 | 9 | 3 | False |
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

## Independent evaluator regression cases

These fixtures test scoring behavior; reasoning-specific synthetic audits and improvements are documented separately.

1. A missing expected row counts as incorrect in all-request accuracy; an extra prediction separately fails coverage and contributes false-positive steps.
2. A wrong citation keeps resource alignment but lowers evidence-field accuracy and exact-step precision/recall.
3. Reordered steps keep content precision/recall but fail sequence accuracy and canonical-order validation.

## Focused review of all 32 public samples

See [sample_mismatch_review.md](sample_mismatch_review.md) for every missing/extra content step, its participant-visible source and proof/root-cause classification, and [case_01_mre.md](case_01_mre.md) for a participant-file-only reproduction requiring no model cache. The reference CSV is consumed only inside evaluation; no expected resource IDs or labels are supplied to prediction code.

### Change from the previous pushed checkpoint

| Measure | Before | After |
| --- | ---: | ---: |
| Sample coverage | 19/32 (59.375%) | 23/32 (71.875%) |
| Status accuracy on all32 | 59.375% | 71.875% |
| Exact sequence | 7/32 (21.875%) | 8/32 (25%) |
| Step precision | 94.96% | 95.86% |
| Step recall | 58.55% | 72.02% |
| Step F1 | 72.44% | 82.25% |
| Aligned field accuracy | 54.99% | 67.70% |
| Full resolved / blocked | 419 /99 | 419 /99 |

All 178 regression tests and Node syntax checks pass. All reruns in this review were offline, with zero new API requests. The configured paid API budget remains$0, with existing credentials unchanged.

### Finance-register correction

The five ORD rows are ordinary business references with explicit retention instructions, not source-proven profiles, exports or active legal holds. Treating them as UNKNOWN privacy-resource obligations incorrectly blocked whole cases. They now remain in the full source facts as retained_business_constraint records: no destructive operation or invented privacy category is produced. Known privacy-resource prefixes, visible direct identifiers and uncertain primary references remain subject to normal uncertainty checks. This removes the finance-specific hold from all five samples; case_21 still independently lacks account-deletion proof, so four additional rows are returned. This is not a claim that an active legal hold exists, or that unshown PII was removed.

### Missing verifications and guard

Many missing verifications refer to absent/sanitized resources with no eligible subject ownership edge. Other cases are held atomically rather than emitting a partial plan. Additional genuinely grounded records are not discarded solely because reference steps omit them. The per-step table distinguishes these from state/citation/policy discrepancies.

A blanket mandatory primary-account absence/tombstone anchor is stricter than the literal contract. The contract requires proof that every relevant copy has its required treatment, rather than naming one mandatory resource category. The guard remains a conservative check for the current whole-account workflow: an audit-record-only match does not establish full deletion, and removing it would not recover the missing resource keys or verification evidence. Scoped engine fixtures do not impose that anchor. No guard was disabled merely to emit a row.

### Minimal source-consistency example

For case_01, expected account_001 occurs zero times in the cited SQL snapshot. The only eligible activity naming that key has no subject identifier and reports an operation claim rather than observed state. Identity/history supplies user_01/email/phone/hash but no account key. Required proof is an eligible subject-to-account association or keyed readback; deriving account_001 from user_01 would be a forbidden suffix assumption. The executable MRE records those counts rather than injecting a mapping.

### Remaining work and limits

The full run still holds69 account ownership gaps despite negative snapshots,25 future-capture exclusions,3 missing eligible primary/scope proofs,1 tombstone field-coverage gap, and1 archive restore-authorization gap. No final output.csv is manufactured. Public samples remain development data; no hidden accuracy is claimed.

Independent fixtures exercise finance/reference retention without invented category, quoted keys, historical-email replicas, future captures, complete negative snapshots with known owned keys, missing replica state, stable-only tombstones, restore access, date boundaries, and report/input protection. The new mismatch-counter regressions distinguish citation changes from numbering/order differences.
