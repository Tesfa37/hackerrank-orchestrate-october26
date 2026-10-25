"""Build the mandatory reports for the explicitly selected prediction candidate.

Expected public answers are read only here in evaluation. Neither this report
builder nor its inputs supplies verdicts or resource identifiers to prediction.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import read_csv, validate_output, validate_citations
from evaluation.main import evaluate, load_predictions

ROOT = Path(__file__).resolve().parents[2]


def validate_ledger(csv_path, rows, ledger):
    if ledger['csv_sha256'] != hashlib.sha256(csv_path.read_bytes()).hexdigest():
        raise ValueError('Assumptions ledger does not match the selected CSV checksum')
    by_id = {row['case_id']: row for row in rows}
    cases = ledger['cases']
    ids = [case['case_id'] for case in cases]
    if len(ids) != len(set(ids)) or ledger['assumption_cases'] != len(cases):
        raise ValueError('Assumption cases are duplicated or miscounted')
    for case in cases:
        if not case['assumptions'] or by_id.get(case['case_id']) != case['row']:
            raise ValueError('An assumption record differs from its selected prediction row')
    return Counter(case['row']['deletion_status'] for case in cases)


def evaluation_report(rows, ledger, sample, strict, support):
    labels = Counter(row['deletion_status'] for row in rows)
    assumed = Counter(case['row']['deletion_status'] for case in ledger['cases'])
    inferred = [case for case in ledger['cases'] if case['inferred_states']]
    lines = ['# Selected submission evaluation', '',
             '**Selected strategy: evidence-based prediction.** The strict auditor is retained as a historical evidence-certification baseline. The blanket INCOMPLETE fallback is rejected because its unsupported fallback rows lack required plans.', '',
             f"Selected file: root `output.csv`; SHA256 `{ledger['csv_sha256']}`. The checksum-bound `output.assumptions.json` preserves source facts, unresolved obligations and explicit predictions. Public expected answers are consumed only inside evaluation, never by prediction code.", '',
             '## Selected full-dataset candidate', '', '| Measure | Result |', '| --- | ---: |',
             f'| Predictions / expected cases | {len(rows)} / {ledger["requested_cases"]} |',
             f'| Structurally valid / invalid rows | {support["valid_rows"]} / {support["invalid_rows"]} |',
             f'| Reported structural validation failures | {support["invalid_rows"]} |',
             f'| COMPLETE / INCOMPLETE / NOT_APPLICABLE | {labels["COMPLETE"]} / {labels["INCOMPLETE"]} / {labels["NOT_APPLICABLE"]} |',
             f'| INCOMPLETE plans with all three ordered phases | {support["phase_compliance"]["incomplete_three_phase_compliant"]}/{labels["INCOMPLETE"]} |',
             f'| Citation-ID/capture availability errors | {len(support["citation_errors"])} |',
             f'| Novel unsupported resource references | {len(support["unsupported_record_references"])} |',
             f'| Assumption-dependent cases | {len(ledger["cases"])} |',
             f'| Conditional COMPLETE predictions | {assumed["COMPLETE"]} |',
             f'| Inferred archive-risk cases / directly unsupported factual steps | {len(inferred)} / {len(support["unsupported_factual_step_claims"])} |', '',
             'All original 518 requested case IDs remain in the candidate, exactly once in lexicographic order. Structural validity means the specified CSV/JSON fields, numbering, phases, operation/state pairs, plan relationships and citation availability pass validation. It does not mean every conditional conclusion is entailed by complete evidence.', '',
             'The 98 conditional COMPLETE predictions assume that eligible discovered records bound the relevant inventory; unknown tombstone field removal remains unresolved. The single inferred archive-risk finding is in `case_55`, which the organizer replies relayed by the user confirm is excluded. The cited archive evidence establishes existence, not current subject-specific restore authorization. Its ACTIVE risk is a disclosed forecast, not a newly established setting or historical event. Original observations are unchanged.', '',
             'Only `case_39` and `case_55` are confirmed exclusions. Excluding them leaves 516/516 predictions, with no directly unsupported factual steps but continued conditional completeness assumptions. No additional exclusion is presumed. Keep all 518 rows pending explicit row-format clarification.', '',
             '## Public samples: all 32 remain in accuracy denominators', '',
             '| Measure | Selected prediction |', '| --- | ---: |',
             f'| Coverage | {sample["covered_cases"]}/{sample["expected_cases"]} ({sample["coverage_rate"]:.3%}) |',
             f'| Status accuracy | {sample["status_correct"]}/{sample["expected_cases"]} ({sample["status_accuracy"]:.3%}) |',
             f'| Exact ordered sequence | {sample["sequence_correct"]}/{sample["expected_cases"]} ({sample["sequence_accuracy"]:.0%}) |',
             f'| Exact case accuracy (status and sequence) | {sample["exact_case_correct"]}/{sample["expected_cases"]} ({sample["exact_case_accuracy"]:.0%}) |',
             f'| Step precision / recall / F1 | {sample["step_precision"]:.2%} / {sample["step_recall"]:.2%} / {sample["step_f1"]:.2%} |',
             f'| Matched / predicted / expected content steps | {sample["matching_steps"]} / {sample["predicted_steps"]} / {sample["expected_steps"]} |',
             f'| Aligned field accuracy | {sample["field_accuracy"]:.2%} |', '',
             'The three missing sample predictions are case_01, case_02 and case_04. They lack eligible owned keys for nonempty supported verification plans. They count as errors, rather than disappearing from the accuracy denominator. The full request set has different cases/cutoffs and does have 518 output rows. Public examples are development data; no hidden-test accuracy or probability calibration is claimed.', '',
             '| Field | Correct / aligned slots | Accuracy |', '| --- | ---: | ---: |']
    for field, count in sample['field_correct_by_name'].items():
        lines.append(f'| {field} | {count}/{sample["aligned_step_slots"]} | {sample["field_accuracy_by_name"][field]:.2%} |')
    lines += ['', 'Step precision/recall/F1 compare multisets of six content fields, including citations but excluding step_no. Exact sequence checks full arrays, numbering and order. Fields align by phase/system/resource/operation, with missing/extra slots penalized for all seven fields. Missing case rows count as incorrect in primary metrics.', '',
              '## Historical strict baseline and rejected fallback', '',
              f'The historical strict auditor returned 419/518 full rows (99 holds), and {strict["covered_cases"]}/32 public rows. Its all32 status accuracy was {strict["status_accuracy"]:.3%}, step F1 {strict["step_f1"]:.2%}, exact sequence {strict["sequence_correct"]}/32 ({strict["sequence_accuracy"]:.0%}). These are baseline measurements, not the selected candidate results.', '',
              'The blanket fallback returned 518 labels but 99 invalid empty INCOMPLETE plans. Missing confirmation is not automatically a policy violation and does not supply a finding, remediation or verification key. This strategy is not selected.', '',
              '## Independent regression cases, failures and improvements', '',
              '1. Synthetic historical/future evidence fixtures ensure that future capture or catalog availability cannot establish an earlier audit state.',
              '2. Synthetic stable-reference tombstones distinguish permitted user_id from prohibited direct identifiers; unshown fields do not become proof of removal.',
              '3. A synthetic archive with attested existence and unknown permission remains UNKNOWN in the source store; only the named prediction policy can forecast ACTIVE risk, and the independent support checker flags the claim.',
              '4. Synthetic missing-account-confirmation fixtures distinguish strict abstention, invalid conservative fallback and conditional prediction without inventing a resource key.',
              '5. Wrong citations, missing cases, reordered arrays, retention failures and report-destination protection exercise evaluation/serialization independently of sample labels.', '',
              'Earlier general fixes corrected finance-register retention constraints, uploaded-document versus live-ticket scope, cutoff-aware aliases and negative-scope handling. The final bounded investigation is recorded in [finalization_investigation.md](finalization_investigation.md). No change is accepted merely to match an expected sample resource or operation. See [approach_comparison.md](approach_comparison.md) for all policy comparisons and affected case IDs.', '',
              'The retained prediction is not conclusive certification of uncertain deletions. Strict blockers and the original source/assumption ledgers remain available. Full-set label accuracy is unmeasured; exact-sequence performance remains 25% on the public development samples.', '']
    return '\n'.join(lines)


def usage_report(rows, ledger):
    u = ledger['usage_summary']
    labels = Counter(row['deletion_status'] for row in rows)
    assumed = Counter(case['row']['deletion_status'] for case in ledger['cases'])
    lines = ['# Selected submission model usage and cost', '',
             f'**Selected output: {len(rows)}/{ledger["requested_cases"]} evidence-based predictions**, not the historical 419-row strict audit. Root `output.csv` is bound to its assumptions/usage ledger by SHA256 '+f'`{ledger["csv_sha256"]}`. It contains {labels["COMPLETE"]} COMPLETE, {labels["INCOMPLETE"]} INCOMPLETE and {labels["NOT_APPLICABLE"]} NOT_APPLICABLE, with {len(ledger["cases"])} assumption-dependent cases ({assumed["COMPLETE"]} conditional COMPLETE and {assumed["INCOMPLETE"]} inferred archive-risk case).', '',
             f'Provider: {u["provider"]}. Application model: `{u["model"]}`. All application extraction calls use this model; no paid fallback or model switch is used.', '',
             '| Final full-dataset attribution | Value |', '| --- | ---: |',
             f'| Requested / predicted cases | {ledger["requested_cases"]} / {ledger["requested_cases"]} |',
             f'| Unique referenced genuine extraction responses | {u["referenced_calls"]} |',
             f'| Reused cached responses | {u["cached_results_reused"]} |',
             f'| New model calls in the candidate publication process | {u["new_calls_this_process"]} |',
             f'| Attributed production attempts, including retries/repairs | {u["production_attempts"]} |',
             f'| Attempts with unavailable provider token usage | {u["attempts_with_unavailable_usage"]} |',
             f'| Known input tokens | {u["input_tokens"]:,} |',
             f'| Known output tokens | {u["output_tokens"]:,} |',
             f'| Known thinking tokens | {u["thinking_tokens"]:,} |',
             f'| Known total tokens | {u["total_tokens"]:,} |',
             f'| Known tokens per requested/predicted case | {u["total_tokens"]/ledger["requested_cases"]:.3f} |',
             '| Configured paid API budget | $0 |', '| Estimated billed cost under the configured free project | $0 total / $0 per case |', '',
             'These totals include the original production work behind every genuine response reused by the final candidate, including attributable retry and corrective ancestry. Reusing a response means zero new generation, not zero historical production work. The same extraction work feeds strict and prediction policies; do not multiply it by three or add overlapping public-sample replay totals.', '',
             f'{u["attempts_with_unavailable_usage"]} attempts have no provider token usage. Their usage is unknown, not silently counted as zero. The {u["total_tokens"]:,} total is the known provider-reported attribution, not a claim that all failed-attempt work is measured. Invoices, current project billing state, remaining quota and provider-side charges were not independently inspected. The user configured a free-tier project with billing disabled; this configuration and the $0 paid budget were preserved. The application does not enforce a dollar cap on an already billed project. No new live calls or billing/credential changes were made during finalization.', '',
             '## Historical development and strict baseline', '',
             'The earlier strict run returned 419/518 rows using the same 44 referenced responses and known 145,605 production tokens. It was an incomplete audit baseline, not the selected final output. Its usage must not be added again to the candidate totals.', '',
             'The previously recorded cloud development ledger contains 69 attempts (64 received, 5 HTTP429), 116,262 known input tokens, 87,744 known output tokens and 204,006 known total tokens; five attempts have unavailable usage. This historical development work overlaps the production attribution and includes superseded prompts, rejected interpretations and corrections. These totals must not be summed with the production totals. The earlier local setup smoke test used 6 input and 1 output token separately.', '',
             'Current finalization, comparison, regression and archive-replay commands are offline or stop before a missing-key request; they add zero application-model calls. Dependency downloads are not generation calls. Exact coding-assistant runtime model metadata and coding-assistant token/cost accounting are not exposed by this session; they are not invented or conflated with the application model.', '',
             'Original genuine response envelopes and attempt ledgers remain private local provenance. They are excluded from Git/code.zip, together with credentials and caches. The selected candidate records its measured usage summary in output.assumptions.json. Uncertain predictions are not promoted into source facts or certified deletion events.', '']
    return '\n'.join(lines)


def main():
    rows = load_predictions(ROOT/'output.csv')
    ledger = json.loads((ROOT/'output.assumptions.json').read_text())
    validate_ledger(ROOT/'output.csv', rows, ledger)
    requests = read_csv(ROOT/'dataset/deletion_requests.csv')
    validate_output(rows, requests)
    validate_citations(rows, requests, read_csv(ROOT/'dataset/evidence_files.csv'),
                       read_csv(ROOT/'dataset/system_activity.csv'), read_csv(ROOT/'dataset/user_audit_log.csv'))
    expected = load_predictions(ROOT/'dataset/sample_output.csv')
    sample = evaluate(load_predictions(ROOT/'.cache/approach_comparison/samples/evidence_prediction.csv'), expected)
    strict = evaluate(load_predictions(ROOT/'.cache/approach_comparison/samples/strict_auditor.csv'), expected)
    comparison_rows = load_predictions(ROOT/'.cache/approach_comparison/full/evidence_prediction.csv')
    if comparison_rows != rows:
        raise ValueError('Selected CSV differs from the evaluated full prediction candidate; regenerate comparison first')
    support = json.loads((ROOT/'.cache/approach_comparison/metrics.json').read_text())['full']['evidence_prediction']
    directory = ROOT/'code/evaluation'
    (directory/'evaluation_report.md').write_text(evaluation_report(rows,ledger,sample,strict,support),encoding='utf-8')
    (directory/'usage_report.md').write_text(usage_report(rows,ledger),encoding='utf-8')
    print('Mandatory reports now describe the selected candidate:',len(rows),'rows;',sample['status_correct'],'/32 statuses')


if __name__=='__main__':
    main()
