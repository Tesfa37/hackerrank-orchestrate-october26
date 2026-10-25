# Deletion audit baseline

## Decision-policy comparison and submission candidate

The strict auditor remains the default. An explicit evidence-based prediction
policy is now available for a competitive candidate; its assumptions are not
source facts. See [evaluation/approach_comparison.md](evaluation/approach_comparison.md)
for full/sample coverage, valid/invalid rows, label distributions, phase checks,
unsupported claims and all affected case IDs.

```sh
python3 code/compare_approaches.py --samples --output-dir .cache/approach_comparison/samples
python3 code/compare_approaches.py --output-dir .cache/approach_comparison/full --write-prediction-candidate output.csv
python3 code/evaluation/compare_approaches.py
```

These commands require genuine cached interpretations and make no API calls.
The comparison always includes the rejected conservative fallback with invalid
empty INCOMPLETE plans; that file is not a submission option. Candidate publication
is only for the evidence-prediction approach and still validates full coverage,
schema, phases and citation availability. It writes `output.assumptions.json` with
source facts, unresolved records and explicit forecast assumptions. It does not
claim that uncertainty has become proof. No sample answers or exclusion list
enter prediction logic. Root `output.csv`, when published this way, is a prediction
candidate rather than a completed strict audit. Keep the sidecar and comparison
report with it; preserve all518 rows pending organizer clarification.

This Python CLI joins current and historical identities to participant evidence,
selects eligible observations at `audit_at`, applies the supplied policies, and
serializes the required findings, remediation, and verification steps. It never
reads sample answers while making predictions. The evaluator reads those answers
separately.

AI interprets requests and media. Deterministic code reconstructs eligible
evidence, applies policy, and orders proposed remediation. The program does not
execute those actions. See [ARCHITECTURE.md](ARCHITECTURE.md) for responsibilities,
scalability limits and design tradeoffs, and [INTERVIEW_NOTES.md](INTERVIEW_NOTES.md)
for the current results and interview preparation. The organizer screenshot
recommends an agent and scalability/robustness; it does not establish a mandatory
API requirement.

This is a development baseline. Source-fact reinspection is enabled by default for every PDF and image; it separates stored identifiers, stable references, visible field coverage, and observation versus lifecycle times. Missing ownership or state evidence produces a
diagnostic error, not a guessed verdict. Public-sample results and remaining gaps
are recorded in `evaluation/evaluation_report.md`.

## Install

Use Python 3.11 or newer. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r code/requirements.txt
```

On Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.
The only third-party runtime dependency is pypdf for document text. CSV, JSON,
SQLite, hashing, HTTP requests, policy reasoning, and evaluation use the standard
library. No service, database server, GPU, or local model is needed.

For an extracted archive, supply the original `dataset/` alongside `code/`.
[FRESH_ENVIRONMENT.md](FRESH_ENVIRONMENT.md) documents the complete empty-cache
workflow, quota limits, failure handling and offline analysis commands.
[evaluation/archive_verification.md](evaluation/archive_verification.md) separates
actual extracted-archive checks from documented live regeneration procedures.

## Model access and budget

Use the existing `GEMINI_API_KEY` environment binding or an ignored root `.env`
containing that variable. Environment injection takes precedence over `.env`.
Never put credentials in source, command arguments, archives, or reports.

The selected provider is the Gemini Developer API Free Tier, model
`gemini-3.5-flash-lite`. The paid API budget is **$0**. Keep project billing
disabled. The program does not enable billing, change credentials, or switch
providers/models when quota is exhausted. Quota/network failures stop missing
extraction. Availability and quota depend on the participant's account.
The program does not inspect project billing or enforce a spending cap on a
billed account. Preserve the existing billing-disabled free project. Live
no-cache regeneration was not performed during finalization.

## Run

All paths default relative to the repository, so invocation from another working
directory is supported. The existing checkout is sufficient; cloud tasks already
have an isolated workspace and do not need another Git worktree.

Prepare reproducible model requests without making API calls:

```sh
python3 code/main.py --samples --prepare
```

Run the 32 public requests, allowing calls to the configured free project:

```sh
python3 code/main.py --samples
```

Model responses are cached under `.cache/gemini/` by model, prompt version, schema,
and exact request content. They contain genuine provider responses and usage.
They are not answer labels. After extraction is complete, replay without API calls:

```sh
python3 code/main.py --samples --offline
```

Successful sample runs write root `sample_predictions.csv`. A complete final run
uses the same pipeline and writes root `output.csv`:

```sh
python3 code/main.py
python3 code/main.py --offline --usage-report code/evaluation/usage_report.md
```

Those strict-auditor success paths are conditional. Current participant evidence
leaves unresolved cases. A separately published prediction candidate can have
518 rows while retaining assumptions; it is not a completed strict audit.

The full dataset requires 518 unique rows sorted by case ID. If any requested case
cannot be grounded, the program exits 2 and preserves any existing output.
Diagnostics and measured usage go to `.cache/run_samples.json` or
`.cache/run_full.json`. For debugging only, explicitly save completed cases:

```sh
python3 code/main.py --samples --offline --partial --output .cache/sample_predictions_partial.csv
```

A partial run still exits 2 when cases are unresolved. Partial results and selected
cases cannot replace root `output.csv`; sample runs cannot replace it either.
`--case CASE_ID` may be repeated for development and requires an explicit output.

An optional portable Node transport can process the exact prepared jobs using the
same environment credential or ignored `.env`:

```sh
node code/process_model_jobs.mjs
```

Python remains the normal transport. The Node helper is optional and needs Node
18+ with native fetch. Both validate structured responses and content hashes
before publishing reusable caches.

## Evaluate and test

```sh
python3 -m unittest discover -s code/tests -v
node --check code/process_model_jobs.mjs
python3 code/evaluation/main.py --predictions sample_predictions.csv
```

For a partial development output, pass its explicit path to the evaluator.
Missing cases count against metrics; missing prediction files cannot overwrite
reports. Step precision/recall compares content including citations, while exact
sequence scoring preserves array order. Aligned field metrics penalize missing
and extra steps. See the generated evaluation report for exact definitions.

## Reasoning and remaining limitations

Only evidence captured and observed by the cutoff is eligible. Activity results
do not prove deletion; explicit catalog links can establish resource ownership.
Current/historical emails, phones, hashes, and stable subject references are used
for joins; names alone never merge people. Explicit resource dependencies extend
the evidence search. Replica states remain separate, so primary absence cannot
hide a present replica. Unscoped missing search hits cannot establish absence.

Policy planning preserves retained records and the stable reference in an account
tombstone. It disables flows and blocks restores before record changes. Conflicts,
missing state, unknown policy actions, and missing tombstone references stop that
case. The CLI also holds an otherwise complete account audit when it lacks linked primary-account absence or a compliant deletion tombstone. This conservative minimum proof does not establish exhaustive discovery. Some policy conditions and business-document aliases may still need richer
extraction or evidence; do not interpret a partial baseline as a completed audit.

Per-run usage includes the production cost of reused extraction caches and labels
new calls separately. The persistent attempt ledger records available retry usage;
unavailable usage remains marked unknown. Development calls and an interrupted
attempt are separate from a successful final-dataset run. No hidden accuracy is
claimed.

## Submission layout

When the full run and review are complete, package `code/` with this README,
`requirements.txt`, prompts, and both `evaluation/` Markdown reports. Do not include
the dataset, `.env`, caches, virtual environments, nested archives, or credentials.
Keep root `output.csv` and root `log.txt` separate from `code.zip`.

## Investigate unresolved requests

```sh
python3 code/investigate.py --reinspect-media --report code/evaluation/blocker_report.md --json .cache/blocker_report.json
```

This read-only diagnostic uses genuine offline responses and participant evidence, never expected answers. It counts missing ownership links, source-capture exclusions, incomplete scope proof, parser/history leads, and image/PDF uncertainty separately. A complete negative snapshot may establish absence for an explicitly owned resource even without an earlier positive row. It cannot supply an unknown resource ID.

A permitted stable subject reference alone is never exposed PII in a tombstone. A partial reference view also cannot prove that unshown direct identifiers were removed. Archive existence does not establish current restore permission. Date-only retention values use an interval over possible source times and timezones; only comparisons unambiguous across that interval are accepted.

Received model responses rejected by validation remain in ignored `.cache/rejected/`. A genuine response may be recovered only after its original request, response, attempt ledger and current validation all agree; provider content is unchanged. At most one source-only corrective extraction is allowed for specific validation-role errors. Original, rejected and corrective usage remains attributed. Credentials, caches and rejected responses are excluded from the review archive and Git commits.

## Organizer exclusions and evaluation coverage

Organizer replies relayed on October 24 confirm only `case_39` and `case_55` as excluded from evaluation. Other invalid cases have no complete exclusion list. Evaluation uses only repository evidence; no dataset change was announced. The original **518-row CSV requirement remains pending explicit clarification about excluded rows**.

Confirmed exclusions live exclusively under `evaluation/` and are never loaded by the predictor. After the full offline run and investigation, reproduce both coverage views with:

```sh
python3 code/evaluation/coverage_report.py
```

The report validates that the predictions and blocker diagnostics describe the same request set, then reports original and adjusted coverage separately. Full-set coverage is not accuracy. Public sample evaluation likewise retains original scores and adds a separate exclusion view; neither confirmed exclusion is among the 32 public samples. Do not treat the remaining blockers as excluded or supply invented predictions for them.

For uploaded customer PDFs, a uniquely quoted continued attachment-properties section can establish that the request body belongs to that file. A printed ticket reference alone does not prove a separate live ticket's current state. Source facts and any deterministic scope correction remain auditable; independent physical objects are not merged without proof.
