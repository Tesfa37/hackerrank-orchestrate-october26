# Deletion Audit Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a runnable evidence-grounded baseline, evaluate all 32 public requests, and prepare the same pipeline for the 518 evaluation requests.

**Architecture:** Python loads shared observations from every supplied format and resolves identity and state at each cutoff. Gemini Free Tier handles multilingual intent and visual/document interpretation through content-addressed requests; policy and serialization remain deterministic. Expected sample answers are read only by the evaluator.

**Tech Stack:** Python 3.11+, standard library, PyMuPDF, Gemini REST API.

**Spec:** `docs/superpowers/specs/2026-10-24-deletion-audit-design.md`; official contract in `AGENTS.md` and `problem_statement.md`.

## Global Constraints

- $0 billed API budget; no paid fallback or billing changes.
- Use participant-facing `dataset/` evidence only; do not infer labels from case IDs or filenames.
- Exact CSV columns: `case_id,deletion_status,steps_json`.
- Exact seven step fields, canonical phase/operation/system/resource ordering, consecutive numbering.
- No evidence captured or observed after `audit_at`; preserve required retained data and permitted tombstone references.
- Read `.env` locally and never print or commit credentials.
- Keep append-only root `log.txt`; maintain model usage reports even for free calls.

## Review Focus

1. Historical emails and phones must resolve without merging people on names alone (Task 1 tests).
2. A later compliant snapshot must not erase a pre-cutoff violation (Task 3 tests).
3. Replica absence must not override a present copy in another replica (Task 2/3 tests).
4. Quota/network failures must stop incomplete extraction rather than inventing answers (Task 4 tests).
5. Non-deletion intent and retained/tombstone records must preserve their correct treatment (Task 3/4 tests).

### Task 1: Contract and identity primitives

**Files:** `code/audit_core.py`, `code/tests/test_core.py`.
**Interfaces:** `read_csv(Path)->list[dict]`; `IdentityIndex(snapshots,history).resolve(email,cutoff)->Subject`; `serialize_steps(list[dict])->list[dict]`; `validate_output(rows,requests)->None`.

- [ ] Write tests for canonical ordering, exact fields, case-insensitive historical email resolution, and future identity rollback.
- [ ] Run `python -m unittest discover -s code/tests -v`; expect missing module/functions to fail.
- [ ] Implement the interfaces and run the same command; expect all tests green.
- [ ] Commit the tested primitives.

### Task 2: Evidence observations

**Files:** `code/evidence.py`, `code/tests/test_evidence.py`.
**Interfaces:** `load_evidence(dataset,model_client)->EvidenceStore`; observations carry evidence/capture/observation timestamps, system/resource/category, identifiers, state, and provenance.

- [ ] Write temporary-fixture tests for trace correlation, JSON snapshots, SQLite primary/replica drift, and cutoff filtering.
- [ ] Watch those tests fail, implement generic adapters, then require the suite to pass.
- [ ] Extract PDF text with page boundaries and enqueue image/ambiguous-document extraction through Task 4's client.
- [ ] Validate ingestion counts and inspect representative observations; commit.

### Task 3: Policy, state, and step planning

**Files:** `code/reasoning.py`, `code/tests/test_reasoning.py`.
**Interfaces:** `audit_request(request,subject,store,rules,intent)->dict` returns one exact output row; missing evidence is a diagnostic error, not a fourth status.

- [ ] Write independent fixtures for non-deletion, historical-ID replica exposure, future deletion, active sync, retained backup, and compliant tombstones.
- [ ] Observe failures, implement state selection and policy actions, and verify all fixtures.
- [ ] Ensure flows/restores precede record changes and complete cases cite evidence; commit.

### Task 4: Free model client and intent/media extraction

**Files:** `code/model_client.py`, `code/tests/test_model_client.py`.
**Interfaces:** `GeminiClient.request(task,parts,schema)->dict`; `prepare` mode writes reproducible missing-request jobs; caches include original response/usage and hashes of model/prompt/content.

- [ ] Write tests for cache key changes, unavailable quota/network errors, and refusal to silently return missing extraction.
- [ ] Implement bounded REST calls, strict structured outputs, extraction-only prompts, usage metering, and no paid fallback.
- [ ] Test a small multilingual request batch and representative image; validate IDs and complete response coverage before expanding.
- [ ] If terminal networking is restricted, execute the exact prepared REST jobs through the available Node runtime and reuse their genuine responses; the submitted CLI must remain independently runnable through normal REST.
- [ ] Commit after the suite passes.

### Task 5: CLI, evaluation, and baseline review

**Files:** `code/main.py`, `code/evaluation/main.py`, `code/README.md`, `code/requirements.txt`, `code/evaluation/evaluation_report.md`, `code/evaluation/usage_report.md`.
**Interfaces:** `python code/main.py --samples` writes `sample_predictions.csv`; `python code/main.py` writes root `output.csv`; `python code/evaluation/main.py` evaluates samples without feeding expected answers into prediction code.

- [ ] Run the pipeline against 32 public cases, reporting status accuracy, exact sequence match, field accuracy, and step precision/recall/F1 with explicit alignment rules.
- [ ] Diagnose errors by evidence/identity/time/policy class and fix general behavior with reproducing tests.
- [ ] Write metrics and at least three independent cases directly in Markdown; include measured usage and limitations.
- [ ] Run all unit tests, validate CSV/JSON/citations, and obtain a fresh whole-branch review.
- [ ] Commit the baseline and report measured results. Process the full set only with the same general pipeline; do not claim hidden accuracy.

## Execution rulings

The user explicitly said "Okay let's go" after reviewing the design and configuring the free key. Continue inline without another approval round. Use the dedicated challenge checkout on `feat/deletion-audit-baseline` to preserve the user's configured `.env` location; no unrelated project files are modified. The initial Python entry points are empty and have no starter tests.
