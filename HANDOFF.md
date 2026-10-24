# Codex handoff: Ghost Data Still Exists

Prepared October 24, 2026. **Work in progress. No predictions or sample accuracy results exist yet.**

## Start here

Open Codex in this existing checkout, not in the unrelated Aulden project:

```text
C:\Users\Tesfa\AppData\Local\Temp\orchestrate-review\hackerrank-orchestrate-october26-main
```

Repository: https://github.com/Tesfa37/hackerrank-orchestrate-october26

Branch: `feat/deletion-audit-baseline`. Use this branch; `main` contains the earlier setup/design checkpoint. The handoff checkpoint includes the current source and tests.

Read these in order:

1. `AGENTS.md`, the binding challenge and append-only logging contract.
2. `problem_statement.md`, especially allowed operations and ordering.
3. This document.
4. `docs/superpowers/specs/2026-10-24-deletion-audit-design.md`.
5. `docs/superpowers/plans/2026-10-24-deletion-audit-baseline.md` and its `-progress.md` ledger.

The user approved implementation with **"Okay let's go"**, then requested this handoff before the baseline was complete. Continue implementation from this checkpoint. Do not restart repository setup or ask again about a paid API budget.

The checkout currently lives under Windows Temp. To continue immediately, use it in place. If moving to a persistent project folder or another computer, preserve the ignored local `.env` and genuine extraction caches separately and update the configured root paths. They are intentionally absent from GitHub.

## User decisions and boundaries

- No paid API usage. Treat the budget as **$0 in billed API costs**, with no automatic paid fallback or billing changes.
- Python is the primary implementation language. Use deterministic identity, temporal, policy, and output logic; use a model for multilingual intent and business-document/image extraction.
- Current model: `gemini-3.5-flash-lite`, using the Gemini Developer API Free Tier. Keep project billing disabled. Account-specific remaining quota has not been established.
- The local root `.env` is configured with `GEMINI_API_KEY` and is ignored by Git. Never print it, put it into tool arguments, commit it, or include it in an archive.
- Current user-facing requirements specify three uploads: `code.zip`, root `output.csv`, and root `log.txt`. Preserve raw agent traces if available, but do not assume a fourth upload slot or put another archive inside `code.zip`.
- Avoid em dashes in user-facing writing. Explain the design clearly enough for the user to defend it in the AI interview.

## Deadline and submission

The user pasted the full HackerRank page. It labels **October 25, 2026 at 7:30 PM CDT** as the interview closing time. The interview opens after successful submission for the next 12 hours, lasts 30 minutes, and requires the camera on. Results are scheduled for October 27.

A separate upload cutoff was not independently verified because the challenge page required sign-in. Treat the stated interview close as the hard finish for the whole submission/interview process, and do not assume the personal 12-hour window extends beyond it. An earlier proposed target was artifacts ready by noon October 25, upload around 1 PM, interview finished by 3 PM, all CDT; those were proposed targets, not confirmed user availability.

Exact challenge/submission URL:

https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists

Do not submit or take the user's interview on their behalf merely because implementation is authorized. Prepare and verify the artifacts for the user's submission.

## Verified dataset inventory

| Item | Count |
| --- | ---: |
| Evaluation requests | 518 |
| Public sample requests/answers | 32 |
| Identity snapshots | 850 |
| Historical identity changes | 306 |
| System activities | 4,011 |
| Policy rules | 15 |
| Evidence files | 94 |

Evidence comprises 24 SQL snapshots, 28 JSON files, 26 logs, 11 PNG screenshots, 4 PDFs, and 1 text file. Public sample statuses are 10 `COMPLETE`, 22 `INCOMPLETE`, and zero `NOT_APPLICABLE`, so independent non-deletion tests are essential.

Only participant-facing `dataset/` data may drive predictions. Do not inspect other people's solutions, organizer truth, generator internals, or hidden answers. `sample_output.csv` belongs only in the evaluator, never in prediction code.

## Current implementation

| File | Implemented | Status |
| --- | --- | --- |
| `code/audit_core.py` | CSV helpers, timestamps, normalization, historical identity resolution, observations, canonical serialization, output validation/writing | Three unit tests pass; not yet exercised end to end |
| `code/evidence.py` | Generic JSON, SQLite, log, and text adapters; observation/scope indexes; media inventory | Three fixture tests pass; semantic coverage needs evaluation |
| `code/model_client.py` | REST request preparation, content-addressed genuine response caches, bounded retries, usage aggregation, batched request intent, image/PDF extraction prompts | Three unit tests pass; new structured requests have not run |
| `code/process_model_jobs.mjs` | Optional Node transport for the exact REST jobs prepared by Python | Syntax check passes; this helper has not executed the prepared queue |
| `code/tests/test_core.py` | Identity cutoff, operation ordering, non-deletion output constraints | Passing |
| `code/tests/test_evidence.py` | Correlated lookup traces, anonymized JSON, primary/replica distinction | Passing |
| `code/tests/test_model_client.py` | Content-based cache signatures, missing offline results, prepare mode | Passing |
| `code/main.py` | Nothing | Still the empty starter file |
| `code/evaluation/main.py` | Nothing | Still the empty starter file |

Not yet created: reasoning/planning engine, complete CLI, evaluation metrics/reports, runtime README/requirements, sample predictions, final predictions, or submission archives. No whole-branch code review has occurred.

The initial core implementation was locally committed as `58d2449`. The handoff branch checkpoint consolidates the current source, documents, and tests for transfer; inspect `git log` for the saved handoff commit.

## Fresh verification at handoff

From the repository root:

```powershell
python -m unittest discover -s code/tests -v
node --check code/process_model_jobs.mjs
```

Observed: **9 tests passed**, zero test failures; Node syntax check exited successfully. These are unit/syntax checks, not proof of prediction accuracy or a completed agent.

A structured-only ingestion run produced 2,867 observations, 2,030 distinct resource IDs, 384 snapshot scopes, and 15 media files awaiting extraction. This is an inventory result, not a validated count of relevant case resources.

## Model access and pending queue

The user set up the local key. Before implementation, an authenticated model lookup returned HTTP 200 and one minimal generation returned `READY`:

- Development generation calls: 1.
- Input tokens: 6.
- Output tokens: 1.
- Total tokens: 7.

That smoke test is recorded in `log.txt` and `docs/free-api-setup.md`. It is not the final-dataset usage report and did not establish remaining quota.

Current local queue: `.cache/model_jobs.json`, encoded in UTF-8. It contains **16 unexecuted jobs**: one batch classifying the 32 sample requests and 15 business-artifact extractions. `.cache/gemini/` has **zero cached responses** at this checkpoint. No implementation model jobs have consumed quota yet.

Each cache key hashes the model, prompt version, task, and exact request content. Caches are genuine model responses with usage metadata, not hardcoded answers. Do not replace them with manual labels or ship them as a substitute for a reproducible cold run.

### Network behavior

The restricted PowerShell/Python tool environment could not resolve `generativelanguage.googleapis.com`. The available persistent Node runtime successfully reached the API using the same locally read key. This was a runtime-network difference, not an invalid credential.

The submitted Python code uses normal REST via `urllib` and must remain independently runnable in a terminal with ordinary network access. The optional Node helper is an alternate transport for prepared jobs, not a dependency on ChatGPT tools.

If normal terminal networking works in Codex:

```powershell
node code/process_model_jobs.mjs
```

If a persistent Node tool is available and terminal DNS remains blocked, import the written helper and run one job first:

```javascript
const transport = await import('file:///C:/Users/Tesfa/AppData/Local/Temp/orchestrate-review/hackerrank-orchestrate-october26-main/code/process_model_jobs.mjs');
const result = await transport.processJobs(
  'C:/Users/Tesfa/AppData/Local/Temp/orchestrate-review/hackerrank-orchestrate-october26-main',
  {limit: 1}
);
// Report only task names, statuses, and usage. Never print the key or .env.
```

Inspect the resulting structured response and account quota before running the remaining jobs. The code uses the current REST `generationConfig.responseFormat.text` schema and `thinkingLevel: MINIMAL`; this payload has not yet been validated live. If the API rejects it, debug against official Gemini API documentation, not by guessing a paid fallback.

The queue is ignored by Git and can be regenerated without expected answers:

```powershell
@'
from pathlib import Path
import sys
sys.path.insert(0, 'code')
from audit_core import read_csv
from evidence import load_evidence
from model_client import GeminiClient, classify_requests, extract_media
root = Path.cwd()
client = GeminiClient(root, prepare=True)
store = load_evidence(root / 'dataset')
classify_requests(client, read_csv(root / 'dataset/sample_deletion_requests.csv'))
for path, meta in store.media:
    extract_media(client, path, meta)
print(client.write_jobs())
'@ | python -
```

Use `encoding='utf-8'` for queue/cache reads. Windows' default cp1252 failed on a Unicode queue during a handoff inventory check; that check was corrected and the unit suite itself was green.

## Important code risks to address next

These are implementation observations, not measured sample failures:

1. **Trace state contamination:** `parse_log` merges all fields per trace. A prior `cache_lookup result=miss` can remain in the merged payload when a primary lookup later reports `rows=1`. `infer_state` may then incorrectly choose absence. Add a reproducing regression test and fix event-specific state handling before relying on log outcomes.
2. **State/ownership reconstruction is absent:** implement links from eligible current/historical identifiers, activity resource references, and data-catalog identity links. An anonymized or absent record may have no direct identifiers; do not drop it simply because it cannot match the current email.
3. **Negative scope semantics need review:** SQLite and JSON snapshot scopes exist, but proving absence from complete snapshot coverage is not implemented. Do not turn any missing search hit into absence. Preserve replica distinctions before aggregating a resource.
4. **Adapter inference is provisional:** collection/prefix category mappings, service aliases, and redaction/anonymization heuristics need evaluation against actual evidence and policy. Preserve explicit authoritative fields over inferred ones.
5. **Media hydration is absent:** convert model `records` into `Observation` objects with validated categories, exact resource IDs, normalized identifiers, and eligible timestamps. Do not let the model invent IDs from order/user numbers.
6. **Output validation is a baseline:** review incomplete-case phase coverage, evidence existence/cutoff checks, duplicate resource treatment, and nonempty supported verification for complete cases. Current tests do not establish all of these.
7. **Usage/caching needs end-to-end validation:** distinguish new calls from reused extraction cost, count retries where usage is available, and never report cached production work as zero total tokens. Quota/network failures must stop missing extraction rather than create guessed output.

## Next implementation sequence

1. Run the existing tests and verify the working branch and ignored key.
2. Fix the trace contamination issue with a failing-then-passing test.
3. Execute one prepared intent job; validate all 32 unique case IDs and boolean intent values. Then process and validate the media jobs within free quota.
4. Implement `code/reasoning.py`: eligible evidence retrieval, identity/resource graph, point-in-time state, retention rules, replica drift, data-flow and restore risks, and deterministic step planning.
5. Add independent fixtures for an export-only request, historical-email replica exposure, deletion after cutoff, active synchronization, retained backups with blocked restores, and compliant tombstones.
6. Implement `code/main.py` with sample and full-dataset modes. Read the dataset independently of expected answers and fail clearly when required extraction is missing.
7. Implement `code/evaluation/main.py` and run the 32 public samples. Report status accuracy, exact sequence match, field accuracy, step precision/recall/F1, and failures by cause. Public samples are development data, not an untouched test set.
8. Fix general behavior with reproducing tests. Do not branch on case IDs, file names, or sample expected labels.
9. Complete `code/README.md`, dependencies, `code/evaluation/evaluation_report.md`, and `code/evaluation/usage_report.md`. Put metrics, at least three custom cases, and usage analysis directly in Markdown because the judge ignores raw-data-only reports.
10. Run the same pipeline for all 518 requests, validate exact schema/citations/order, review the code, then package the three upload files. Do not claim hidden accuracy.

## Essential output rules

- Exact CSV header: `case_id,deletion_status,steps_json`.
- One row per evaluation case, exactly 518 data rows, sorted by `case_id`.
- `NOT_APPLICABLE` means no deletion was authorized and requires `steps_json=[]`.
- Each step has exactly `step_no`, `phase`, `system_id`, `resource_id`, `operation`, `state`, `evidence_id`.
- Sort by phase, the operation precedence in `problem_statement.md`, then ascending system/resource IDs. Disable flows and block restores before record changes.
- `COMPLETE`: only evidence-backed verification steps. `INCOMPLETE`: all findings, complete ordered remediation, and future verification.
- Findings and complete-case verification cite eligible `file_id`, `activity_id`, or `audit_id`. Incomplete-case remediation and future verification use an empty evidence ID.
- Filter both file capture and observation/event timestamps at `audit_at`. Workflow `reported_status` and activity `reported_result` are claims, not state proof.
- Preserve required retained records. A compliant account tombstone keeps the permitted stable subject reference but removes prohibited direct identifiers, including email hash.

## Logging and final delivery

Append each new user turn to root `log.txt` in the exact `AGENTS.md` format. Identify the new Codex harness and actual runtime model from authoritative runtime information; do not copy a model identifier just because this previous session used it. Never rewrite earlier log entries or add credentials.

The eventual `code.zip` must contain runnable code, prompts/configuration, setup/run instructions, and both Markdown evaluation reports, with no dataset, credentials, virtual environments, caches, or nested archives. Keep the root `output.csv` and `log.txt` as separate uploads. Prepare an architecture explanation and interview notes the user can understand.
