# Latest focused review checkpoint

178 tests pass. Sample coverage23/32; all32 status accuracy71.875%; exact sequence8/32 (25%); step precision95.86%, recall72.02%, F1 82.25%; fields67.70%. Full419/518,99blocked unchanged. Finance-register ordinary business references are preserved as retention constraints, not invented privacy-resource categories; case21 still lacks independent account proof. Expected answers remain exclusively in evaluation.

Read code/evaluation/sample_mismatch_review.md (every missing/extra step) and case_01_mre.md (no-cache participant-file-only reproduction). Run `.venv/bin/python code/evaluation/review_mismatches.py` or add `--mre-case01 --report /tmp/case01.md`. No new API calls or credential changes in this review. The paid budget remains$0. No final output.csv exists.

The earlier checkpoint below is historical; its metrics are superseded by this section and the evaluation report.

# Deletion-audit handoff

Branch: feat/deletion-audit-baseline, based on 9b3e227757b2b04c949e9dbc95e6fdab3039ddfa. Existing checkout: /workspace/hackerrank-orchestrate-october26. Use it in place; no extra worktree.

The paid API budget remains $0. Preserve injected GEMINI_API_KEY and Free Tier billing-disabled configuration. No credentials or caches belong in commits/archives. Dataset bytes match official upstream. No source data, expected labels or hidden answers were used to fill missing identity links.

## Current result

175 tests pass; Node syntax passes. All 518 intents and all 15 source-fact media reviews are genuine cached responses. The final full offline run resolves 419/518; 99 remain uncertain. Sample coverage is 19/32 (59.375%); status accuracy across all32 is 59.375%, exact sequence7/32 (21.875%), step precision94.96%, recall58.55%, F1 72.44%, aligned-field accuracy54.99%. Returned-row status19/19 is supplementary, not all-case accuracy.

See code/evaluation/evaluation_report.md, usage_report.md and blocker_report.md for exact metrics, counts, source paths and representative missing proofs. The 99 groups are 69 missing eligible owned account keys despite negative scopes, 25 future-capture exclusions, 3 missing eligible primary scope/direct evidence, and 2 media uncertainties (tombstone field removal and archive restore permission). The original98 gained one legitimate archive-permission hold. No final output.csv exists; partial CSVs remain under .cache and must not be submitted as complete. code.zip is a review/development code bundle with these limitations, not a completed submission.

## Fixes and remaining work

Source-fact reinspection is enabled by default. Stable user_id alone is permitted in a tombstone and never exposed PII. Unshown fields are not proof of redaction. Modified/Created times stay events; manifest capture is preserved. Catalog availability gates joins. A known owned key may be proven absent in its first exhaustive snapshot; unknown keys cannot be manufactured. Replica listing without parsed state holds the audit. Exact UTC text and date-only retention intervals are supported without guessed timestamps. Archive presence alone does not imply restore access. Genuine rejected responses may be revalidated without editing source content; one bounded source-only corrective request is supported.

All identities resolve, including100 historical request emails; no missing valid historical identifiers or eligible raw-primary parser misses were found. A separate sample reasoning gap remains for finance-register business references with retention dates but uncertain mapping to the supplied policy category/condition. Do not hardcode sample labels or remove the completeness guard merely to emit518 rows.

## Reproduce

```sh
.venv/bin/python -m unittest discover -s code/tests -v
node --check code/process_model_jobs.mjs
.venv/bin/python code/main.py --samples --offline --partial --output .cache/sample_predictions_partial.csv
.venv/bin/python code/evaluation/main.py --predictions .cache/sample_predictions_partial.csv --report .cache/evaluation_summary.md --json .cache/sample_metrics.json
.venv/bin/python code/main.py --offline --partial --output .cache/full_predictions_partial.csv
.venv/bin/python code/investigate.py --reinspect-media --report code/evaluation/blocker_report.md --json .cache/blocker_report.json
```

Partial runs deliberately exit2; evaluator exits1 for incomplete coverage. Current caches are ignored; a new machine needs actual free-tier extraction using prepare/online mode. Never fabricate cache responses. code/README.md documents installation and runtime.

Append-only log.txt preserves conversation summaries. Exact coding-harness model metadata is not exposed in this session; the transcript explicitly records that limitation rather than inventing an identifier. Application-model usage is measured separately. Resolve harness metadata before treating the transcript as fully AGENTS-compliant.

The earlier user-provided interview close was October25,2026 at7:30PM CDT; separate upload cutoff unverified. Do not submit or take the interview for the user. Challenge: https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists
