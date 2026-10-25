# Extracted-archive verification

## Selected submission finalization

The selected evidence-based candidate is retained byte for byte from07aa568.
Mandatory evaluation/usage reports now describe518/518 predictions, the153/355/10
labels,99assumption cases and the disclosed case_55 forecast; older strict
measurements below are historical. The final source includes201passing regression
tests, checksum/ledger validation and protected selected-report generation.
Current extracted-archive installation, replay, candidate publication, report
regeneration and source-validation command records are preserved in
review_artifacts/finalization/archive_verification.json. The two mandatory reports
are reproduced from the extracted copy and checked against the packaged originals.
Root output.csv and log.txt remain separate upload artifacts. No live generation,
billing verification or paid API changes are claimed by these offline checks.

## Current decision-policy version

The optional prediction-policy comparison adds196-test coverage and a separately
published518-row prediction candidate with99 explicitly recorded assumptions.
The default strict pipeline and its419 supported rows remain unchanged. The
archive is re-extracted and checked with the same installation/replay procedure
after these additions; updated command records are preserved as
review_artifacts/approach_comparison/archive_verification.json. This code archive
still contains neither root output.csv nor model caches. The candidate and its
assumptions are separate deliverables, not a claim that the strict blockers were
resolved. The186-test verification below is the historical initial checkpoint.

Verified October 24, 2026 (America/Chicago). The runtime source was extracted from the b242f64 review archive into an empty temporary directory. The finalization archive adds documentation; its extracted runtime is checked again before publication. A machine-readable command/exit-code record and exact archive checksum are preserved separately in review_artifacts/archive_verification.json.

## Actually tested

| Check | Result |
| --- | --- |
| Fresh virtual environment | Created with Python 3.12.14; no existing site packages reused |
| Install requirements | pypdf 6.10.0 installed with pip --no-cache-dir from public PyPI |
| Dependency consistency | pip check passed |
| Regression suite | All 186 tests passed from the extracted copy |
| Optional Node helper | Syntax check passed with Node 24.19.0 |
| CLI entry points | Main, evaluator, investigator, mismatch reviewer and exclusion reporter --help commands passed from outside the extracted root |
| Empty-cache full preparation | Exit 0; 43 initial jobs: 13 intent, 15 extraction, 15 source review; no responses or predictions created |
| Empty-cache offline run | Exit 2; 0/518 supported; zero API calls; no output.csv |
| Missing-key online mode | Exit 2 before any API attempt; zero supported rows; no output.csv |
| Genuine-cache sample replay | Exit 2; 23/32 supported; zero new calls |
| Genuine-cache full replay | Exit 2; 419/518 supported; 99 holds; zero new calls |
| Public evaluator | Exit 1 for incomplete coverage; status71.875%, sequence25%, precision97.89%, recall72.02%, F1 82.99%, fields68.73% |
| Full blocker investigation | Exit 0; original groups69/25/3/2 reproduced |
| Confirmed-exclusion report | Exit 0; 418/516 supported,98holds |
| Mismatch table and case_01 MRE | Both exit 0; expected answers confined to evaluation |
| Partial run usage command | Exit 2; usage Markdown written to an explicit diagnostic path |
| Preservation | Replayed sample/full CSV bytes identical to preserved supported predictions; participant dataset bytes unchanged |

The verification child process had no GEMINI_API_KEY and no .env. No key was changed in the shared environment. Only after the empty-cache checks, original genuine response envelopes, rejection provenance and the attempt ledger were copied into the temporary cache for a separate offline replay. This tests portability of existing results; it is not fresh model generation. The code archive itself contains no caches or dataset. Dependency installation used the network; no generation request was made.

Mock-provider regressions exercise rate/daily quota behavior, retry bounds, authentication/network failures, malformed responses and cache validation. They are not a test of the account's current live quota.

## Documented, not exercised here

- Live cache regeneration from an empty environment using the existing free-tier account, including optional Node live job processing.
- Current model availability, actual RPM/TPM/daily allowances, remaining quota, or project billing status.
- Windows installation, Python 3.11 compatibility, large-load throughput, concurrent writers or distributed execution.
- A successful final518-row CSV. The current schema/exclusion ambiguity and missing participant proof remain unresolved.

The first replay used a freshly installed dependency, not the workspace virtual environment. Later final-archive checks use the same documented procedure in another extracted directory. Individual command timings in the external record are single-machine checks, not a throughput benchmark. Read FRESH_ENVIRONMENT.md for reproducible commands and ARCHITECTURE.md for implemented boundaries.

Paid API budget remains$0. Current production attribution remains145,605 known tokens from reused genuine work; this finalization adds zero model calls. Usage from the partial run is not represented as a completed submission.
