# Independent finalization checkpoint

The organizer screenshot recommends an agent and scalability/robustness; it does not establish a mandatory API rule. The design is documented honestly in code/ARCHITECTURE.md: AI interprets intent/media, deterministic code reconstructs eligible evidence, applies policy and orders proposed actions. No live remediation is executed.

code.zip was extracted into an empty directory, a fresh Python3.12.14 virtual environment installed pypdf6.10.0 from public PyPI with no dependency-cache reuse, pip check passed, and all186tests plus Node syntax/CLI commands passed. Empty-cache preparation queued43initial jobs with no API calls; empty-cache offline and missing-key runs exited2 without output.csv. Copying existing genuine response provenance into that extracted copy then reproduced sample/full CSV bytes exactly. The refreshed documentation archive is checked with the same procedure; exact commands and checksum are preserved in review_artifacts/archive_verification.json. Live no-cache generation, current quota/billing checks, Windows/Python3.11 and larger-load throughput are documented, not newly tested. No runtime prediction logic changed in this finalization.

Read code/FRESH_ENVIRONMENT.md, code/evaluation/archive_verification.md and code/INTERVIEW_NOTES.md. Supported partial CSVs, full blocker JSON, usage/run summaries and coverage views are preserved under review_artifacts/, separately from the code archive. Root log.txt remains the append-only transcript, including the previously documented unavailable exact coding-model metadata. Preserve private genuine caches locally, but keep them and credentials out of Git/archives. The workspace packaging helper is `.venv/bin/python tools/build_review_archive.py`; it includes tracked code and root evaluation-report copies, so new intended code files must be staged first.

Metrics remain419/518 with99holds, or418/516 with98holds after only the two confirmed exclusions. Samples23/32 coverage, status71.875%, exactsequence8/32(25%), precision97.89%, recall72.02%, F1 82.99%, fields68.73%. Paid budget$0; all finalization model runs offline/without credentials and zero new model calls. Original518-row contract remains pending excluded/unsupported-row clarification. No final output.csv exists; code.zip is explicitly a review bundle.

# Organizer guidance and attachment correction checkpoint

Organizer replies relayed by the user on October24 confirm evaluation exclusions only for case_39 and case_55. Other invalid cases will be excluded, but no complete list was supplied. Evaluation uses only repository evidence; no dataset change was announced. **Keep the original 518-row CSV requirement pending explicit clarification about excluded rows.** Do not exclude all unresolved cases or hardcode answers. Machine-readable guidance and adjusted reports live only under code/evaluation and are never imported by prediction logic.

186 tests pass; Node syntax passes. Original full run:419/518 returned (80.8880%),99blocked. Excluding only the two confirmed cases:418/516 (81.0078%),98blocked. case_39 has a row; case_55 is a restore-authorization hold. Adjusted blocker groups:69 missing eligible account ownership edges despite negative scopes;25 capture/cutoff gaps;3 missing eligible direct primary/scope proofs;1 tombstone direct-field removal proof gap (case_46). Stable user_id alone remains permitted and is never exposed PII.

The case_07 PDF body now belongs to its explicitly continued customer-upload attachment, with its fully printed technical support key. No separate live-ticket state is inferred from that body. All source facts and scope corrections remain auditable. Three false steps disappear; the separately evidenced storage object and missing account verification remain. Sample coverage23/32, all32 status71.875%, exact sequence8/32(25%); precision97.8873%, recall72.0207%, F1 82.9851%, aligned fields68.7318%. Neither confirmed exclusion is in the 32 samples.

Read code/evaluation/organizer_guidance.md and case_07_attachment_review.md. Reproduce adjusted coverage with `.venv/bin/python code/evaluation/coverage_report.py` after the full run and investigator commands below. This review is entirely offline:zero new API calls, no credential/billing changes, paid budget$0. No final output.csv exists. Refresh code.zip only as a clearly identified review bundle until all required predictions are evidence-backed. The historical checkpoints below are superseded by this section.

# Previous focused review checkpoint

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
