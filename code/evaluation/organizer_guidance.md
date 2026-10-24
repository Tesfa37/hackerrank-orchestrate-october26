# Organizer guidance and full-run coverage

Recorded 2026-10-24. Source: Organizer replies relayed by the user in this chat; not independently fetched.

- Confirmed evaluation exclusions: `case_39`, `case_55`.
- Other invalid cases will be excluded, but no complete list was provided. No other exclusion is assumed.
- Evaluation uses only the evidence supplied in the repository. No dataset change was announced.
- The existing 518-row CSV requirement remains pending explicit clarification about excluded rows.

Exclusions affect this evaluation view only. The predictor still processes all 518 requests, applies the same cutoff and policy checks, and neither reads this guidance nor assigns answers to excluded cases. No final output.csv has been produced.

| View | Returned / requests | Coverage | Blocked |
| --- | ---: | ---: | ---: |
| Original contract | 419/518 | 80.8880% | 99 |
| Excluding confirmed cases only | 418/516 | 81.0078% | 98 |

Excluded returned requests: case_39. Excluded blocked requests: case_55. Both numerator and denominator are recomputed from case IDs. An exclusion is not evidence of the correct deletion status.

| Root cause | Original blockers | Blockers excluding confirmed cases |
| --- | ---: | ---: |
| Unresolved image/PDF field or configuration proof | 2 | 1 |
| Missing eligible account ownership edge despite negative scopes | 69 | 69 |
| Missing eligible direct primary proof or complete scope | 3 | 3 |
| Primary evidence excluded by capture/observation cutoff | 25 | 25 |

The media group originally contains two distinct cases: `case_46` lacks explicit tombstone direct-field removal proof; `case_55` lacks current subject-specific restore authorization. Only the latter has a confirmed exclusion. Permitted stable user_id alone is not exposed PII.

After confirmed exclusions, 98 blockers remain, grouped above. The unspecified invalid-case guidance does not establish that these are all invalid.

## Remaining blocked request IDs after confirmed exclusions

case_103, case_107, case_108, case_111, case_112, case_126, case_127, case_150, case_151, case_152, case_155, case_157, case_162, case_175, case_178, case_183, case_190, case_191, case_204, case_206, case_213, case_215, case_218, case_219, case_221, case_225, case_226, case_231, case_243, case_244, case_253, case_257, case_260, case_274, case_276, case_277, case_294, case_295, case_297, case_299, case_304, case_308, case_309, case_313, case_314, case_319, case_322, case_335, case_336, case_339, case_343, case_345, case_346, case_351, case_354, case_362, case_393, case_395, case_398, case_403, case_408, case_409, case_411, case_412, case_423, case_424, case_427, case_430, case_448, case_45, case_452, case_456, case_457, case_458, case_46, case_462, case_463, case_464, case_467, case_470, case_480, case_493, case_494, case_497, case_502, case_506, case_512, case_524, case_530, case_532, case_57, case_58, case_59, case_60, case_64, case_69, case_70, case_97.

See [blocker_report.md](blocker_report.md) for original diagnostics and representative exact missing proofs. Full-run coverage is not accuracy: no full-set expected answers were used. Neither exclusion appears among the 32 public sample IDs, so their scoring denominator remains 32.

Reproduce offline after regenerating the partial full run and blocker diagnostics:

```sh
.venv/bin/python code/evaluation/coverage_report.py
```

Paid API budget: $0. This report performs no API calls and changes no credentials, participant data or predictions.
