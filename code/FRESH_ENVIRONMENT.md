# Fresh environment and genuine response regeneration

The archive contains code, prompts (in source), requirements, and evaluation/interview documentation. It deliberately contains no dataset, response caches, virtual environment, API credentials or final predictions. Preserved partial predictions are separate review artifacts, not bootstrap inputs to the predictor.

## Extract and install

Extract `code.zip` into an empty directory. The archive has a root `README.md` and a `code/` directory. Supply the original participant `dataset/` alongside `code/`; copy it from the repository without modifying its bytes. Then, from that extracted root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r code/requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s code/tests -v
node --check code/process_model_jobs.mjs
```

Python 3.11+ is required; the clean-install verification used Python 3.12.14 and pypdf 6.10.0. Node is optional for normal Python execution; the helper uses Node 18+ native fetch. Windows uses `.venv\Scripts\python.exe`. Windows and Python 3.11 were documented but not exercised in this finalization.

## No-cache preparation is not model generation

```sh
.venv/bin/python code/main.py --prepare
```

This reads participant inputs, constructs hashed structured model requests, and writes `.cache/model_jobs.json`. It makes no API calls and produces no verdicts or final CSV. In the tested empty-cache full run, it queued 43 initial jobs: 13 intent batches, 15 first-pass media extractions and 15 source-fact reviews. It may discover additional alias or corrective jobs after genuine first responses arrive. This is not a fixed total or a quota guarantee. Queues contain evidence content and absolute local cache paths; regenerate them after moving the extracted directory.

```sh
.venv/bin/python code/main.py --offline
```

Without genuine responses this exits 2, records missing extraction/intent diagnostics in `.cache/run_full.json`, and leaves `output.csv` unwritten. Preparation cannot substitute for inference. A missing API key is also a diagnostic failure; it does not trigger another provider or invented model facts.

## Generate genuine results on the configured free project

Use the existing `GEMINI_API_KEY` environment binding or an ignored root `.env`. Keep that project's billing disabled. Do not place the credential in command arguments, reports or the archive. The fixed application model is `gemini-3.5-flash-lite`; availability and quotas must be checked for the actual account. The application does not verify the project's billing setting and cannot enforce a dollar spending cap on a billed account. The $0 configuration depends on maintaining the existing free-tier project; no paid fallback or credential/billing change is performed.

The ordinary Python path generates missing responses and reuses valid existing ones:

```sh
.venv/bin/python code/main.py --samples --partial --output .cache/sample_predictions_partial.csv
.venv/bin/python code/main.py --partial --output .cache/full_predictions_partial.csv --usage-report .cache/full_usage.md
```

These commands are **documented live procedures, not executed in this finalization**. They make real requests when genuine caches are absent. Partial outputs remain development artifacts; current evidence holds still make the commands exit 2. A 518-row success is not promised after model regeneration. New valid responses can differ from the recorded development responses.

If Python cannot reach the provider but the optional Node runtime can, prepare jobs and use its transport:

```sh
.venv/bin/python code/main.py --prepare
node code/process_model_jobs.mjs
.venv/bin/python code/main.py --prepare
```

The Node helper processes the queue sequentially, validates signatures/schemas, and saves genuine responses. It stops on a failure and preserves completed responses. Repeat preparation after completion or a quota reset to discover remaining work; the Python online path can also resume. Both implementations use the same fixed model and compatible cache signatures. Do not manually create envelopes, alter provider content, or reuse prepared absolute paths from another machine. Node live processing was not exercised in this finalization.

## Free-tier limits and failures

There is no universal requests-per-minute, tokens-per-minute or requests-per-day allowance documented for this account. Limits depend on model, project and provider policy. Check the actual project in AI Studio and the provider's [rate-limit documentation](https://ai.google.dev/gemini-api/docs/rate-limits). This finalization did not inspect current remaining quota, billing or model availability. Earlier genuine development usage and quota failures are recorded in `evaluation/usage_report.md`.

| Condition | Implemented handling |
| --- | --- |
| Daily quota exhausted | Stop immediately; do not retry that request or switch to paid service. Resume only after quota is available. |
| HTTP 429 or 500/502/503/504 | At most three attempts for that transport request. Honor sanitized server retry timing; a delay over 60 seconds stops instead of sleeping. Defaults are bounded and differ slightly between Python and Node. |
| Missing key, authentication, unsupported model, other HTTP errors | Stop missing generation and retain valid prior work. No model/provider fallback. |
| Network error or timeout | Each HTTP request has a 90-second timeout; network failures stop the affected stage. No fabricated response. |
| Truncated, malformed or semantically invalid response | Reject/quarantine it; never publish it as a valid extraction. Certain source-review role/coverage errors permit one bounded source-only corrective extraction with usage/provenance retained. |
| Unreadable or mismatched cache | Diagnostic failure; no silent replacement call. Inspect the failure without editing content into a valid answer. |
| Valid extraction but missing ownership/state/scope proof | Retain the unresolved case in diagnostics. Do not force a status or guess an ID. |

Transport retries do not cap the total number of jobs in a full run; an optional corrective extraction is a separate request. Unknown failed-attempt token usage remains unknown. Cached production work counts in usage even when replay makes zero new calls. Neither an estimated free-tier $0 cost nor temperature zero guarantees future availability or identical new results.

## Offline replay and analysis after real extraction

```sh
.venv/bin/python code/main.py --samples --offline --partial --output .cache/sample_predictions_partial.csv
.venv/bin/python code/main.py --offline --partial --output .cache/full_predictions_partial.csv --usage-report .cache/full_usage.md
.venv/bin/python code/evaluation/main.py --predictions .cache/sample_predictions_partial.csv --report .cache/evaluation_summary.md --json .cache/sample_metrics.json
.venv/bin/python code/investigate.py --reinspect-media --report .cache/blocker_report.md --json .cache/blocker_report.json
.venv/bin/python code/evaluation/coverage_report.py --report .cache/organizer_guidance.md
.venv/bin/python code/evaluation/review_mismatches.py --report .cache/sample_mismatch_review.md
.venv/bin/python code/evaluation/review_mismatches.py --mre-case01 --report .cache/case01_mre.md
```

Currently both partial audits exit 2 and public evaluation exits 1 because coverage is incomplete. The other analysis commands exit 0 with all required inputs. The normal final command remains `.venv/bin/python code/main.py --offline`; it publishes root `output.csv` only when every requested case validates. The original 518-row requirement is still pending clarification about excluded/unsupported rows. No uncertainty status is invented.

See `evaluation/archive_verification.md` for what was actually exercised from an extracted archive, and `INTERVIEW_NOTES.md` for design explanations and limitations.
