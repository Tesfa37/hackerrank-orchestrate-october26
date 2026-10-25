# Decision-policy comparison

The same participant evidence and genuine offline model interpretations feed all policies. Public expected answers are read only by this evaluator. No new API calls, resource IDs or historical events are created. The existing strict CLI stays unchanged by default. These are prediction-policy experiments, not newly discovered evidence.

## Facts, deductions and predictions

Structured states and model-interpreted media facts retain source/time provenance. Exhaustive scoped absence is a logical deduction for an already grounded key. A COMPLETE case label is a policy conclusion about discovered coverage, not a directly observed global fact. Media interpretation itself remains fallible.

- **Strict auditor:** current discovery, all known treatment checks and a primary-account/tombstone completion anchor; abstains on missing proof. Its returned rows are supported relative to that discovery policy, not an independent guarantee of exhaustive truth.
- **Conservative fallback:** retains strict rows, predicts INCOMPLETE for every strict hold, and emits no invented findings. These empty plans are deliberately preserved as invalid experimental rows. Missing confirmation does not establish a violation; this is a rejected baseline, not a submission option.
- **Evidence-based prediction:** retains strict decisions; otherwise predicts from eligible known treatments without an extra mandatory account anchor. Unknown tombstone treatment remains unknown, with conditional compliance recorded externally. For a literally present retained archive with unknown restore permission, it forecasts potential restore risk; that ACTIVE finding is explicitly inferred and is counted as unsupported by direct current-state evidence. The source itself is never rewritten. Missing all eligible resources still yields abstention.

## Full-run structure and integrity

| Approach | Coverage | Valid / invalid rows | Labels C / I / N | Phase-compliant / noncompliant | Novel resource references | Unsupported factual step claims | I labels without observed violation | Assumption cases | Full file schema/citations |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| strict_auditor | 419/518 (80.89%) | 419 / 0 | 55 / 354 / 10 | 419 / 0 | 0 | 0 | 0 | 0 | Fail |
| conservative_fallback | 518/518 (100.00%) | 419 / 99 | 55 / 453 / 10 | 419 / 99 | 0 | 0 | 99 | 99 | Fail |
| evidence_prediction | 518/518 (100.00%) | 518 / 0 | 153 / 355 / 10 | 518 / 0 | 0 | 1 | 1 | 99 | Pass |

C=COMPLETE, I=INCOMPLETE, N=NOT_APPLICABLE. INCOMPLETE requires all three phases; COMPLETE correctly has verification only; NOT_APPLICABLE has no plan. Valid row/file counts measure serialization, phase/operation requirements and citation availability, not entailment of every prediction. Assumption-dependent completeness claims are counted separately from individual step claims; zero unsupported steps does not mean zero uncertainty.

| Approach | Coverage excluding confirmed cases | Valid / invalid | Unsupported factual steps | Assumption cases | Remaining missing |
| --- | ---: | ---: | ---: | ---: | ---: |
| strict_auditor | 418/516 (81.01%) | 418 / 0 | 0 | 0 | 98 |
| conservative_fallback | 516/516 (100.00%) | 418 / 98 | 0 | 98 | 0 |
| evidence_prediction | 516/516 (100.00%) | 516 / 0 | 0 | 98 | 0 |

Only case_39 and case_55 are excluded in this separate view. Exclusions do not enter decision logic; the original file contract still requires all518 rows pending clarification.

INCOMPLETE three-phase compliance: strict_auditor: 354/354; conservative_fallback: 354/453; evidence_prediction: 355/355.

## All 32 public samples

| Approach | Coverage | Valid / invalid rows | Status accuracy | Exact sequence | Step P / R / F1 | Fields |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict_auditor | 23/32 | 23 / 0 | 71.88% (23/32) | 25.00% (8/32) | 97.89% / 72.02% / 82.99% | 68.73% |
| conservative_fallback | 32/32 | 23 / 9 | 75.00% (24/32) | 25.00% (8/32) | 97.89% / 72.02% / 82.99% | 68.73% |
| evidence_prediction | 29/32 | 29 / 0 | 90.62% (29/32) | 25.00% (8/32) | 97.53% / 81.87% / 89.01% | 76.87% |

Missing rows remain incorrect in every primary case metric. Prediction policy selection and debugging use these development samples, so this is not hidden-set accuracy or a held-out estimate. Full-set label accuracy cannot be measured without prohibited hidden truth. Exact sequences remain limited by missing eligible account keys, independent additional evidence, and document/policy interpretation gaps.

## Assumption ledger and unsupported claims

### full

**strict_auditor:** 0 cases affected. None.

Assumption counts: {}.

Still abstained: case_103, case_107, case_108, case_111, case_112, case_126, case_127, case_150, case_151, case_152, case_155, case_157, case_162, case_175, case_178, case_183, case_190, case_191, case_204, case_206, case_213, case_215, case_218, case_219, case_221, case_225, case_226, case_231, case_243, case_244, case_253, case_257, case_260, case_274, case_276, case_277, case_294, case_295, case_297, case_299, case_304, case_308, case_309, case_313, case_314, case_319, case_322, case_335, case_336, case_339, case_343, case_345, case_346, case_351, case_354, case_362, case_393, case_395, case_398, case_403, case_408, case_409, case_411, case_412, case_423, case_424, case_427, case_430, case_448, case_45, case_452, case_456, case_457, case_458, case_46, case_462, case_463, case_464, case_467, case_470, case_480, case_493, case_494, case_497, case_502, case_506, case_512, case_524, case_530, case_532, case_55, case_57, case_58, case_59, case_60, case_64, case_69, case_70, case_97.

**conservative_fallback:** 99 cases affected. case_103, case_107, case_108, case_111, case_112, case_126, case_127, case_150, case_151, case_152, case_155, case_157, case_162, case_175, case_178, case_183, case_190, case_191, case_204, case_206, case_213, case_215, case_218, case_219, case_221, case_225, case_226, case_231, case_243, case_244, case_253, case_257, case_260, case_274, case_276, case_277, case_294, case_295, case_297, case_299, case_304, case_308, case_309, case_313, case_314, case_319, case_322, case_335, case_336, case_339, case_343, case_345, case_346, case_351, case_354, case_362, case_393, case_395, case_398, case_403, case_408, case_409, case_411, case_412, case_423, case_424, case_427, case_430, case_448, case_45, case_452, case_456, case_457, case_458, case_46, case_462, case_463, case_464, case_467, case_470, case_480, case_493, case_494, case_497, case_502, case_506, case_512, case_524, case_530, case_532, case_55, case_57, case_58, case_59, case_60, case_64, case_69, case_70, case_97.

Assumption counts: {"missing_confirmation_implies_failure": 99}.

Still abstained: none.

**evidence_prediction:** 99 cases affected. case_103, case_107, case_108, case_111, case_112, case_126, case_127, case_150, case_151, case_152, case_155, case_157, case_162, case_175, case_178, case_183, case_190, case_191, case_204, case_206, case_213, case_215, case_218, case_219, case_221, case_225, case_226, case_231, case_243, case_244, case_253, case_257, case_260, case_274, case_276, case_277, case_294, case_295, case_297, case_299, case_304, case_308, case_309, case_313, case_314, case_319, case_322, case_335, case_336, case_339, case_343, case_345, case_346, case_351, case_354, case_362, case_393, case_395, case_398, case_403, case_408, case_409, case_411, case_412, case_423, case_424, case_427, case_430, case_448, case_45, case_452, case_456, case_457, case_458, case_46, case_462, case_463, case_464, case_467, case_470, case_480, case_493, case_494, case_497, case_502, case_506, case_512, case_524, case_530, case_532, case_55, case_57, case_58, case_59, case_60, case_64, case_69, case_70, case_97.

Assumption counts: {"discovered_evidence_bounds_resource_inventory": 99, "existing_archive_may_restore_without_confirmed_block": 1, "unknown_treatment_not_assumed_a_violation": 1}.

Still abstained: none.

- `case_55`: `REPORT_RESTORE_RISK` on `backup_service/backup_9287`, citing `evidence_32`. The source establishes existence, not current restore authorization. This is a forecast, not a proven ACTIVE setting.
### samples

**strict_auditor:** 0 cases affected. None.

Assumption counts: {}.

Still abstained: case_01, case_02, case_04, case_17, case_21, case_25, case_26, case_27, case_28.

**conservative_fallback:** 9 cases affected. case_01, case_02, case_04, case_17, case_21, case_25, case_26, case_27, case_28.

Assumption counts: {"missing_confirmation_implies_failure": 9}.

Still abstained: none.

**evidence_prediction:** 6 cases affected. case_17, case_21, case_25, case_26, case_27, case_28.

Assumption counts: {"discovered_evidence_bounds_resource_inventory": 6, "unknown_treatment_not_assumed_a_violation": 1}.

Still abstained: case_01, case_02, case_04.


## Recommendation and limits

The evidence-based prediction policy is the strongest schema-valid full-file candidate among these three approaches. It improves measured public status coverage/accuracy while retaining known violations, cutoff rules, required retention, resource IDs and genuine citations. The strict auditor remains the strongest evidence-certification baseline. The conservative fallback fails required plan structure and should not be submitted.

This recommendation is conditional: the prediction file is not a certificate that every deletion is complete. Added COMPLETE labels rely on discovered evidence bounding relevant copies; unknown tombstone removal is not proven. One explicit archive-risk finding is inferred from existence and lacks direct authorization proof. The report counts that claim even though its case is among the two confirmed exclusions. No probability calibration or hidden-set benefit is claimed, and exact-sequence performance must be considered alongside status gains.

Sensitivity check: withholding the forecast row leaves 517/518 rows, while covering 516/516 cases after confirmed exclusions. The status gains on public samples do not depend on the archive forecast. If organizers authorize omitting excluded rows, this unconfirmed claim is unnecessary for evaluated coverage; until then the full candidate keeps it explicitly labeled as a prediction in the sidecar.

The three public requests with no eligible owned resource remain absent from the prediction candidate rather than gaining made-up verification keys. The full dataset has different evidence/cutoffs; a full-file candidate does not establish full public-sample coverage. Keep strict blockers, source facts and per-case assumptions alongside any prediction CSV. Do not present the prediction policy as having resolved the underlying97 account-proof gaps or the tombstone uncertainty.

Reproduce with `code/compare_approaches.py` for full/sample candidates, then `code/evaluation/compare_approaches.py`. All comparison inference is offline. Existing genuine model extraction work is reused once across policies; production token attribution must not be tripled. Paid API budget remains$0.
