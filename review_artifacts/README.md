# Preserved review results

The baseline snapshots below remain preserved. The newer `approach_comparison/`
directory compares strict, conservative fallback and evidence-based prediction.
Root `output.csv` is now a separately validated518-row **prediction candidate**,
with assumptions in `output.assumptions.json`; it is not a completed strict audit.
Do not confuse complete CSV coverage with evidence confirmation. The candidate
and updated comparison report identify99 assumption-dependent cases and one
unconfirmed archive-risk forecast. See code/evaluation/approach_comparison.md.

These are incomplete development artifacts. None is the required root output.csv. Do not submit a partial file as a completed 518-row prediction or use it as a source of evidence/model facts.

- `full_predictions_partial.csv`: 419 supported rows from the original 518-request run, including case_39. The other99 requests remain in diagnostics; no excluded/unsupported row is assigned a fabricated verdict.
- `sample_predictions_partial.csv`: 23 supported rows from the32public samples.
- `blocker_diagnostics.json`: original99holds, with grouped participant-visible proof diagnostics.
- `coverage_views.json`: original419/518 coverage and separate418/516 view excluding only confirmed case_39/case_55;98holds remain.
- `run_summaries.json`: original request counts, errors and usage summaries, with provider envelopes/prompt caches excluded.
- `sample_evaluation_summary.json`: measured scores; detailed expected-step comparisons remain under code/evaluation.
- `archive_verification.json`: actual command exit codes, environment versions, empty-cache checks, replay checks and the tested archive checksum. It contains no API response cache.
- `manifest.json`: hashes and sizes of preserved review files plus the root transcript. It identifies the source prediction checkpoint separately from finalization documentation.

The full/sample CSVs were reproduced byte for byte in an extracted archive using copies of the original genuine responses. This is an offline portability check, not independent regeneration or hidden-set accuracy. Existing private caches remain ignored and outside Git/code.zip. No credentials are stored here. The unchanged participant dataset is supplied separately.

The code/reports and interview notes are in code.zip. Root log.txt remains the append-only transcript; it is separate from the code archive. Exact coding-model runtime metadata is unavailable in this session and the log records that limitation without inventing an identifier.

The existing518-row submission requirement remains pending organizer clarification about excluded and unsupported rows. The only confirmed exclusions are case_39 and case_55. The organizer's recommendation to consider agent scalability and robustness does not establish a mandatory API requirement.
