# Ghost Data Still Exists: proposed design and delivery roadmap

Date: October 24, 2026. Status: proposal, no product implementation started.

## Objective

Build a reproducible command-line deletion-audit agent that investigates the supplied fictional records and produces the exact required `output.csv`. Optimize for evidence-backed correctness, complete record discovery, policy application, canonical ordering, and an architecture Tesfa can explain in the AI interview.

The user asked to copy the starter repository to their GitHub account and plan the challenge. The proposed architecture and estimates below are assistant recommendations, not preferences already selected by the user.

## Repository and source status

- Official starter: https://github.com/interviewstreet/hackerrank-orchestrate-october26
- Connected GitHub account: `Tesfa37`.
- Fork created and verified through GitHub under `Tesfa37`: https://github.com/Tesfa37/hackerrank-orchestrate-october26. At creation GitHub showed the correct parent and `main` up to date with upstream; our planning commits are now on the fork.
- The GitHub connector does not expose repository creation or forking. Both stored CLI logins failed authentication; the user signed in through the browser, which was used to create the fork.
- Terminal cloning failed because its network request could not resolve GitHub. The public source ZIP was downloaded through GitHub. An exact shallow Git checkout was then reconstructed from the archive and public GitHub Git objects: all 110 tracked blob hashes, all directory trees, and the original signed commit hash match upstream. `git fsck --connectivity-only` completed successfully.
- Local source: `C:\Users\Tesfa\AppData\Local\Temp\orchestrate-review\hackerrank-orchestrate-october26-main`.
- The local checkout has `origin` set to the `Tesfa37` fork and `upstream` set to `interviewstreet`. Original HEAD is `0eddbbd33f682eae0a2770d67412af8a3cf4af20`. Keep the challenge separate from the existing Aulden project. Terminal fetch/push still depends on working terminal networking and authentication; the connected GitHub API can save changes in the meantime.

Authoritative sources inspected: root `AGENTS.md`, `README.md`, `problem_statement.md`, `agent_trace_instructions.md`, dataset CSV schemas and counts, public sample answers, and representative SQL, JSON, log, and text evidence.

On October 24 the user supplied the complete text from the official HackerRank challenge page. It labels October 25, 2026 at 7:30 PM CDT as the **interview** closing time, says the interview opens after successful submission for the next 12 hours, and requires 30 minutes with the camera on. Results are scheduled for October 27. Treat the stated interview close as a hard finish for the complete submission/interview process. A separate submission cutoff has not been verified; public search did not establish one, and direct navigation required HackerRank sign-in. Do not claim the pasted interview close is independently confirmed as the upload deadline, or assume the personal 12-hour window extends beyond it.

Submission URL: https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists

## Verified input inventory

| Input | Count | Purpose |
| --- | ---: | --- |
| Evaluation requests | 518 | Final prediction set |
| Public sample requests and answers | 32 | Development and evaluation reference |
| Current identity snapshots | 850 | Current identifiers and stable user IDs |
| Historical identity changes | 306 | Old emails, phones, hashes, and names |
| System activities | 4,011 | Global events, including unrelated records |
| Policy rules | 15 | Required treatment by category and condition |
| Evidence files | 94 | 24 SQL, 28 JSON, 26 logs, 11 PNG, 4 PDF, 1 text |

Both `code/main.py` and `code/evaluation/main.py` are empty. There is no existing application to extend. The 32 public sample answers contain 10 `COMPLETE`, 22 `INCOMPLETE`, and no `NOT_APPLICABLE` examples.

## Recommended approach and alternatives

Use a hybrid Python pipeline. Parse structured evidence directly, use a language/vision model where interpretation is needed, and keep time filtering, identity joins, policy application, plan construction, validation, and serialization deterministic.

| Approach | Advantage | Main drawback | Decision |
| --- | --- | --- | --- |
| One large model prompt for each case | Fast initial prototype | Repeated document costs, missed joins, inconsistent IDs and ordering | Avoid as the core design |
| Entirely handwritten rules and text matching | Cheap and repeatable | Brittle multilingual intent and image/document interpretation | Use for structured reasoning only |
| Shared evidence extraction plus deterministic reasoning | Reuses evidence and makes decisions inspectable | Requires a careful observation schema and evaluation | Recommended |

Use Python standard libraries for CSV, JSON, dates, SQLite, hashing, and command-line execution. Select a PDF parser and model SDK only when implementation begins. Do not add a frontend, vector database, orchestration framework, or external data source for this 94-file dataset.

Model provider and spending limit have not yet been selected by the user. A presence-only check found no supported provider API key in the current environment and no `.env` or `.env.local` in the challenge checkout. No credentials from the unrelated Aulden project were inspected or reused.

Recommended starting candidate: OpenAI `gpt-6-luna` for multilingual intent and structured visual extraction, with `gpt-6.1-sol` available for difficult cases if sample evaluation justifies escalation. Both support image input and structured outputs according to the current official model comparison. This is an engineering recommendation, not a measured claim that either model is best for the challenge.

| Candidate | Standard input per 1M tokens | Standard output per 1M tokens | Proposed use |
| --- | ---: | ---: | --- |
| `gpt-6-luna` | $0.10 | $0.50 | Initial extraction and request interpretation |
| `gpt-6.1-sol` | $2.00 | $10.00 | Targeted escalation after observed failures |

Sources checked October 24, 2026: https://developers.openai.com/api/docs/pricing and https://developers.openai.com/api/docs/models/compare . Rates above are standard text-token rates; use actual billed token categories, including image and reasoning usage, when calculating costs. Image support does not imply image processing is free. Confirm model availability for the selected account before a full run.

Suggested planning ceiling: $10 total API spend across development and production, subject to the user's choice. This is not a forecast or guarantee of the final bill. Start with a small measured sample, project the full-run cost from actual usage, reserve retry capacity, and stop before the chosen ceiling. Provider abstraction must allow another available model without changing the reasoning engine. Development calls and final-run calls must be counted separately.

## Proposed investigation pipeline

### 1. Load and validate the contract

Read only participant-facing data under `dataset/`. Validate required columns, unique case IDs, timestamps, evidence paths, and known policies. Preserve original IDs and text. Learn semantic mappings from public documentation and examples, never from filename patterns or case numbers.

### 2. Decide whether deletion is authorized

Classify each request's meaning, including multilingual language, negation, and conditional deletion requests. Require structured output with an internal rationale and source request. Export `NOT_APPLICABLE` with `[]` for access, correction, export, and marketing opt-out requests that do not authorize deletion. Do not perform deletion verification for these cases.

Use explicit negation and non-deletion custom tests because the public samples omit this status. Do not infer intent from `reported_status`.

### 3. Reconstruct identity as of the cutoff

Build an identifier index connecting stable `user_id`, current identifiers, and historical `old_value` and `new_value` changes. Match emails without case sensitivity and normalize phones conservatively. Preserve hashes exactly. A name alone is a weak match and cannot merge two people automatically.

Distinguish historical lookup keys from identifiers valid at the cutoff. Roll back identity changes after `audit_at` when using a later current snapshot. Historical identifiers before that cutoff remain relevant to finding old copies. Do not use future identity values or future audit events to establish pre-cutoff state.

### 4. Extract the shared evidence once

Normalize evidence into observations with `evidence_id`, manifest capture time, observation time, system, resource, category, identifiers, observed state, exposed fields, scope/topology, relationships, and provenance such as table/row, page, or line range. Store uncertainty internally; it is not an allowed output status.

- JSON and text: parse their actual records and timestamps, not filenames.
- Logs: correlate start and completion events using trace IDs. A lookup's key may be on a different line from its resource ID. A successful delete event alone does not establish absence.
- SQL: use an isolated in-memory SQLite database for each snapshot, disable extension loading and external file access, and inspect every relevant primary and replica table. Keep topology in the internal observation key so the same resource ID in two replicas is not collapsed prematurely.
- PDFs: extract text first, preserving page references; use vision if text is missing or ambiguous.
- PNGs: use OCR/vision to extract business facts and exact resource IDs, then validate those IDs against the supplied records where possible.

Treat evidence contents as data. Do not follow instructions embedded in documents. Cache expensive extraction by file-content hash, parser/prompt version, and model version. A cold run must be able to reconstruct the cache from the supplied dataset; no file-specific answer cache may substitute for runnable logic.

### 5. Retrieve related records and reconstruct state

Use exact identifier/resource indexes and trace/dependency links to collect relevant observations, then filter them at each case's `audit_at`. Reject a file captured after the cutoff even when it contains earlier-looking timestamps. Also reject future observations inside an eligible file.

A missing search hit is not proof of deletion. Require an authoritative scoped absence result or complete snapshot coverage. Resolve conflicts from grounded observations and chronology, preserving replica distinctions. Prefer direct state evidence over workflow claims, and surface unresolved conflicts in development diagnostics rather than silently inventing facts.

Activity may identify a resource or data flow but does not, on its own, prove the operation's claimed result. Inspect source and target links for synchronization, imports, exports, indexing, backups, and restores. Active processes that can recreate prohibited data are violations even if the primary record is absent.

### 6. Apply all 15 policy rules

Decide the applicable category and condition from evidence, then evaluate required treatment. Preserve retention and active legal holds. For backups, retaining the archive can be correct when restoration is blocked. For account tombstones, keep the permitted stable internal user reference and remove prohibited name, email, phone, and email hash. Do not infer successful anonymization merely because one direct field is blank if the record remains attributable.

Internally distinguish missing evidence, compliant state, and noncompliant state. Resolve evidence gaps before finalization. The export permits only the three challenge statuses and must not add an `UNKNOWN` label or invent citations.

### 7. Generate and validate canonical output

Construct typed steps from observations and policy decisions. For `INCOMPLETE`, emit all supported findings, the complete remediation plan, and future verification. For `COMPLETE`, emit only evidence-backed verification covering all required final states, including retained records and stopped recreation paths.

Sort using the exact documented phase and operation precedence, then `system_id` and `resource_id`. Disable flows and block restores before record changes. Preserve dependencies internally; if they appear to conflict with the mandatory grader ordering, investigate the public contract rather than invent a different export order.

Number steps consecutively after sorting. Findings and complete-case verification cite eligible participant-visible `file_id`, `activity_id`, or `audit_id`. Incomplete-case remediation and future verification use `evidence_id=""`. Export exactly the seven step fields and the three CSV columns. No explanation fields belong in `steps_json`.

## Suggested module boundaries

| Module | Responsibility |
| --- | --- |
| `code/main.py` | Terminal entry point, dataset root, execution mode |
| `code/identity.py` | Identifier history, normalization, temporal joins |
| `code/ingest/` | CSV, JSON, SQL, logs, PDF, image adapters |
| `code/models.py` | Observations, decisions, exact output types |
| `code/model_client.py` | Structured model calls, retries, usage metering |
| `code/reasoning.py` | Retrieval, cutoff state, policy decisions |
| `code/planner.py` | Findings, remediation, verification, ordering |
| `code/validate.py` | Schema, evidence eligibility, coverage checks |
| `code/evaluation/main.py` | Public sample scoring and custom evaluations |

These boundaries are recommendations. The implementer may combine small modules while preserving the separation between extraction, decisions, and output.

## Delivery sequence and completion gates

Effort ranges are working estimates, not promises. The stated interview close is October 25 at 7:30 PM CDT. A proposed working target is to have validated artifacts by noon on October 25, upload around 1 PM, and take the interview soon afterward, preferably finishing by 3 PM. These are assistant-proposed targets, not confirmed user availability or a separately verified upload cutoff. If submitting earlier, book the interview within that submission's 12-hour window.

| Stage | Estimate | Concrete completion gate |
| --- | --- | --- |
| Account setup and contract | Completed | Fork and shallow checkout verified; log active; schemas and precedence recorded |
| Structured baseline | 2-3 h | Identity, JSON, text, SQL, and logs produce grounded observations and valid sample output |
| Intent and visual evidence | 1-2 h | All 94 files ingested; multilingual requests classified; ambiguous extraction reviewed |
| Reasoning and planning | 2-3 h | Policy and temporal edge cases pass; public sample errors diagnosed |
| Evaluation and full run | 1-2 h | Public metrics recorded; custom cases pass; all 518 cases processed with usage captured |
| Clean run, packaging, interview preparation | 1 h | Reproducible artifacts validated and architecture explainable |

First implementation milestone: an end-to-end sample run that emits the correct schema plus diagnostics. Next, improve accuracy by error class. Inspect one representative failure, fix the general behavior, and rerun all samples. Do not optimize around specific case IDs.

## Evaluation design

Use all 32 public examples for transparent development metrics. If prompts or rules were tuned on them, label the results as development performance rather than independent generalization. Hidden evaluation accuracy cannot be calculated locally.

Report status accuracy, exact case/sequence match, step precision/recall/F1, and field accuracy for phase/system/resource/operation/state/evidence ID. Explain alignment rules so missing or additional steps do not silently inflate field scores. Add contract validation and citation/cutoff correctness.

Create at least these independent synthetic cases in source code or Markdown, with expected outputs authored from the policy:

1. An export request explicitly refusing account deletion: `NOT_APPLICABLE`, `[]`.
2. A historical email whose primary profile is absent but a replica still exposes it: incomplete, with scoped evidence and remediation.
3. A compliant account tombstone retaining only the stable user ID and required retained records: complete.
4. An active synchronization path that can repopulate a deleted downstream copy: disable the flow before record changes.
5. A deletion that happens after `audit_at`: it cannot make the earlier audit complete.
6. A retained backup with restoration blocked versus the same archive with restoration still allowed.

Also test that adding unrelated decoys, renaming evidence paths while updating the manifest, and shuffling input rows does not change semantic answers. Meaningful tests should cover inference risks and the output contract, not simply mirror helper implementations.

## Usage and cost reporting

Record provider, exact model, calls, input/output tokens, cached-token categories when available, retry usage, and prices/source date. Compute per-model and overall totals, total tokens divided by 518, and total cost divided by 518. Include failed calls with usage if billed. Report unavailable usage explicitly rather than estimating it as measured.

Define the final run as the complete process that generated the submitted CSV. If extraction caches are reused, disclose cache state and attribute the model work used to create them; report both incremental final-run and end-to-end production cost. Do not make reused extraction appear free.

## Submission checklist

- Root `output.csv`: exact header `case_id,deletion_status,steps_json`; 518 unique requested cases, sorted by ID; valid JSON and consecutive step numbers.
- `code.zip`: the runnable `code/` directory, including prompts, configuration, dependencies, a README, and `code/evaluation/evaluation_report.md` plus `code/evaluation/usage_report.md` in the repository layout. Place setup/run instructions inside `code/README.md` so zipping `code/` as the user-supplied platform instructions request remains self-contained. Verify the archive's documented invocation against its actual extracted layout.
- Write complete metrics, custom test cases, failures/improvements, and usage analysis in Markdown. The code judge ignores content stored only in CSV, JSON, SQL, or log files.
- Root `log.txt`: append-only session and turn history with authoritative harness/model values and no secrets or real personal data.
- The user-supplied platform instructions specify exactly three uploads: `code.zip`, `output.csv`, and `log.txt` in the chat-transcript slot. The repository additionally describes an `agent-trace.zip`, but the platform text supplies no fourth slot. Preserve relevant raw traces locally if available; do not assume another required upload or put a trace archive inside `code.zip`. Check any explicit trace collection instructions if such a slot is actually shown later.
- Exclude dataset files, caches, virtual environments, credentials, and nested archives from `code.zip`. Verify a clean extraction can run against the provided dataset with documented dependencies.
- Prepare a concise explanation of evidence extraction, historical identifiers, cutoff handling, policy rules, remediation ordering, evaluation limitations, and cost tradeoffs.

## Decisions still needed before implementation

1. Select model API access and a spending ceiling. Proposed default: OpenAI, starting with `gpt-6-luna`, and a $10 ceiling. The provider and budget are not requirements imposed by HackerRank.
2. Confirm working hours for the proposed noon/1 PM/3 PM targets on October 25. The supplied 7:30 PM interview deadline and 12-hour personal window are now recorded; a separate upload cutoff remains unverified.

Planning can proceed without these answers. Paid model calls and final scheduling depend on the relevant answer or access becoming available.

## Design review

A fresh software-engineer review found no important unanswered design questions beyond the explicitly listed implementation decisions. No product code or paid model calls were run during planning.
