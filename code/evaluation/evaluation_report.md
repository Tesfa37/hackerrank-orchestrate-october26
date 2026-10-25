# Selected submission evaluation

**Selected strategy: evidence-based prediction.** The strict auditor is retained as a historical evidence-certification baseline. The blanket INCOMPLETE fallback is rejected because its unsupported fallback rows lack required plans.

Selected file: root `output.csv`; SHA256 `dab79bc63c7a8d5357c3b865e091f34f2cc9a7c49a940aec3e326e85669f64d1`. The checksum-bound `output.assumptions.json` preserves source facts, unresolved obligations and explicit predictions. Public expected answers are consumed only inside evaluation, never by prediction code.

## Selected full-dataset candidate

| Measure | Result |
| --- | ---: |
| Predictions / expected cases | 518 / 518 |
| Structurally valid / invalid rows | 518 / 0 |
| Reported structural validation failures | 0 |
| COMPLETE / INCOMPLETE / NOT_APPLICABLE | 153 / 355 / 10 |
| INCOMPLETE plans with all three ordered phases | 355/355 |
| Citation-ID/capture availability errors | 0 |
| Novel unsupported resource references | 0 |
| Assumption-dependent cases | 99 |
| Conditional COMPLETE predictions | 98 |
| Inferred archive-risk cases / directly unsupported factual steps | 1 / 1 |

All original 518 requested case IDs remain in the candidate, exactly once in lexicographic order. Structural validity means the specified CSV/JSON fields, numbering, phases, operation/state pairs, plan relationships and citation availability pass validation. It does not mean every conditional conclusion is entailed by complete evidence.

The 98 conditional COMPLETE predictions assume that eligible discovered records bound the relevant inventory; unknown tombstone field removal remains unresolved. The single inferred archive-risk finding is in `case_55`, which the organizer replies relayed by the user confirm is excluded. The cited archive evidence establishes existence, not current subject-specific restore authorization. Its ACTIVE risk is a disclosed forecast, not a newly established setting or historical event. Original observations are unchanged.

Only `case_39` and `case_55` are confirmed exclusions. Excluding them leaves 516/516 predictions, with no directly unsupported factual steps but continued conditional completeness assumptions. No additional exclusion is presumed. Keep all 518 rows pending explicit row-format clarification.

## Public samples: all 32 remain in accuracy denominators

| Measure | Selected prediction |
| --- | ---: |
| Coverage | 29/32 (90.625%) |
| Status accuracy | 29/32 (90.625%) |
| Exact ordered sequence | 8/32 (25%) |
| Exact case accuracy (status and sequence) | 8/32 (25%) |
| Step precision / recall / F1 | 97.53% / 81.87% / 89.01% |
| Matched / predicted / expected content steps | 158 / 162 / 193 |
| Aligned field accuracy | 76.87% |

The three missing sample predictions are case_01, case_02 and case_04. They lack eligible owned keys for nonempty supported verification plans. They count as errors, rather than disappearing from the accuracy denominator. The full request set has different cases/cutoffs and does have 518 output rows. Public examples are development data; no hidden-test accuracy or probability calibration is claimed.

| Field | Correct / aligned slots | Accuracy |
| --- | ---: | ---: |
| step_no | 112/197 | 56.85% |
| phase | 158/197 | 80.20% |
| system_id | 158/197 | 80.20% |
| resource_id | 158/197 | 80.20% |
| operation | 158/197 | 80.20% |
| state | 158/197 | 80.20% |
| evidence_id | 158/197 | 80.20% |

Step precision/recall/F1 compare multisets of six content fields, including citations but excluding step_no. Exact sequence checks full arrays, numbering and order. Fields align by phase/system/resource/operation, with missing/extra slots penalized for all seven fields. Missing case rows count as incorrect in primary metrics.

## Historical strict baseline and rejected fallback

The historical strict auditor returned 419/518 full rows (99 holds), and 23/32 public rows. Its all32 status accuracy was 71.875%, step F1 82.99%, exact sequence 8/32 (25%). These are baseline measurements, not the selected candidate results.

The blanket fallback returned 518 labels but 99 invalid empty INCOMPLETE plans. Missing confirmation is not automatically a policy violation and does not supply a finding, remediation or verification key. This strategy is not selected.

## Independent regression cases, failures and improvements

1. Synthetic historical/future evidence fixtures ensure that future capture or catalog availability cannot establish an earlier audit state.
2. Synthetic stable-reference tombstones distinguish permitted user_id from prohibited direct identifiers; unshown fields do not become proof of removal.
3. A synthetic archive with attested existence and unknown permission remains UNKNOWN in the source store; only the named prediction policy can forecast ACTIVE risk, and the independent support checker flags the claim.
4. Synthetic missing-account-confirmation fixtures distinguish strict abstention, invalid conservative fallback and conditional prediction without inventing a resource key.
5. Wrong citations, missing cases, reordered arrays, retention failures and report-destination protection exercise evaluation/serialization independently of sample labels.

Earlier general fixes corrected finance-register retention constraints, uploaded-document versus live-ticket scope, cutoff-aware aliases and negative-scope handling. The final bounded investigation is recorded in [finalization_investigation.md](finalization_investigation.md). No change is accepted merely to match an expected sample resource or operation. See [approach_comparison.md](approach_comparison.md) for all policy comparisons and affected case IDs.

The retained prediction is not conclusive certification of uncertain deletions. Strict blockers and the original source/assumption ledgers remain available. Full-set label accuracy is unmeasured; exact-sequence performance remains 25% on the public development samples.
