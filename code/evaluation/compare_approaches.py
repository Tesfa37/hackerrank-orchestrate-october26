"""Independently audit candidate support and compare public metrics only here."""
from collections import Counter
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import read_csv, timestamp, validate_output, validate_citations
from decision_policies import APPROACHES
from investigate import load_context
from reasoning import select_states, InsufficientEvidence
from evaluation.main import evaluate
from evaluation.exclusions import coverage_view, load_guidance

ROOT = Path(__file__).resolve().parents[2]
POLICY = {
    'DELETE': ('PRESENT','ABSENT','REPORT_REMAINING_RECORD','DELETE_RECORD','VERIFY_RECORD_ABSENT'),
    'REDACT': ('PRESENT','REDACTED','REPORT_EXPOSED_PII','REDACT_RECORD','VERIFY_RECORD_REDACTED'),
    'ANONYMIZE': ('PRESENT','ANONYMIZED','REPORT_EXPOSED_PII','ANONYMIZE_RECORD','VERIFY_RECORD_ANONYMIZED'),
    'DISABLE': ('ACTIVE','DISABLED','REPORT_ACTIVE_DATA_FLOW','DISABLE_DATA_FLOW','VERIFY_DATA_FLOW_DISABLED'),
    'BLOCK': ('ACTIVE','BLOCKED','REPORT_RESTORE_RISK','BLOCK_RESTORE','VERIFY_RESTORE_BLOCKED'),
    'RETAIN': ('','PRESENT','','','VERIFY_RECORD_PRESENT'),
}


def factual_support(row, observations, rules, cutoff):
    """Check individual current-state claims, not the closed-inventory premise.

    This checker reads original selected observations, not the policy's inferred
    state copies. Missing permission is not evidence of ACTIVE or BLOCKED.
    """
    eligible = [o for o in observations if o.eligible(cutoff)]
    keys = {(o.system,o.resource) for o in eligible}
    unsupported, novel = [], []
    for step in json.loads(row['steps_json']):
        key = (step['system_id'],step['resource_id'])
        if key not in keys:
            novel.append(step)
        if step['phase'] != 'FINDING' and row['deletion_status'] != 'COMPLETE':
            continue
        supported = False
        for observation in eligible:
            if (observation.system,observation.resource) != key or observation.evidence_id != step['evidence_id']:
                continue
            actions = {r['required_action'] for r in rules if r['data_category']==observation.category}
            action = ('DISABLE' if observation.category=='DATA_FLOW' else
                      'BLOCK' if observation.category=='BACKUP_ARCHIVE' else
                      next(iter(actions)) if len(actions)==1 else '')
            if action not in POLICY:
                continue
            bad, compliant, finding, remediation, verification = POLICY[action]
            if step['phase']=='FINDING':
                supported |= step['operation']==finding and observation.state==bad and step['state']==bad
            else:
                supported |= step['operation']==verification and observation.state==compliant and step['state']==compliant
        if not supported:
            unsupported.append(step)
    return unsupported, novel


def assess(rows, records, requests, observed, rules, manifest, activities, history, excluded_ids):
    request_map = {r['case_id']:r for r in requests}
    valid, invalid, bad_citations, unsupported, novel, unsubstantiated_failures = [], [], [], [], [], []
    phase_counts = Counter()
    labels = Counter(row['deletion_status'] for row in rows)
    for row in rows:
        cid = row['case_id'];request = request_map[cid]
        steps = json.loads(row['steps_json'])
        phases = {step['phase'] for step in steps}
        phase_ok = (phases == {'FINDING','REMEDIATION','VERIFICATION'} if row['deletion_status']=='INCOMPLETE' else
                    phases == {'VERIFICATION'} if row['deletion_status']=='COMPLETE' else not phases)
        order=[{'FINDING':0,'REMEDIATION':1,'VERIFICATION':2}.get(step['phase'],99) for step in steps]
        phase_ok = phase_ok and order==sorted(order)
        phase_counts['compliant' if phase_ok else 'noncompliant'] += 1
        if row['deletion_status']=='INCOMPLETE' and phase_ok:
            phase_counts['incomplete_three_phase_compliant'] += 1
        try:
            validate_output([row], [request])
        except ValueError as error:
            invalid.append({'case_id':cid,'error':str(error)})
        else:
            valid.append(cid)
            try:
                validate_citations([row],[request],manifest,activities,history,observed.get(cid,[]))
            except ValueError as error:
                bad_citations.append({'case_id':cid,'error':str(error)})
        failures, new_records = factual_support(row, observed.get(cid,[]), rules, request['audit_at'])
        findings=[step for step in steps if step['phase']=='FINDING']
        if row['deletion_status']=='INCOMPLETE' and not any(step not in failures for step in findings):
            unsubstantiated_failures.append(cid)
        unsupported += [{'case_id':cid, 'step':step} for step in failures]
        novel += [{'case_id':cid,'step':step} for step in new_records]
    coverage = coverage_view(list(request_map),[r['case_id'] for r in rows])
    adjusted = coverage_view(list(request_map),[r['case_id'] for r in rows],excluded_ids)
    affected = [record for record in records if record['assumptions']]
    inferred_ids={record['case_id'] for record in records if record['inferred_states']}
    without_forecasts=[row['case_id'] for row in rows if row['case_id'] not in inferred_ids]
    try:
        validate_output(rows, requests)
        file_error = None
    except ValueError as error:
        file_error = str(error)
    # Empty fallback plans cannot support an INCOMPLETE label; a nonempty
    # prediction can still depend on an unproved inventory/unknown-treatment assumption.
    return {'coverage':coverage, 'excluding_confirmed':adjusted,
            'excluding_confirmed_valid_rows':sum(cid not in excluded_ids for cid in valid),
            'excluding_confirmed_invalid_rows':sum(item['case_id'] not in excluded_ids for item in invalid),
            'excluding_confirmed_unsupported_steps':sum(item['case_id'] not in excluded_ids for item in unsupported),
            'excluding_confirmed_assumption_cases':sum(item['case_id'] not in excluded_ids for item in affected),
            'without_forecast_rows':coverage_view(list(request_map),without_forecasts),
            'without_forecast_rows_excluding_confirmed':coverage_view(list(request_map),without_forecasts,excluded_ids),
            'valid_rows':len(valid),'invalid_rows':len(invalid),'row_errors':invalid,
            'file_contract_valid':file_error is None and not bad_citations,'file_contract_error':file_error,
            'labels':dict(labels),'phase_compliance':dict(phase_counts),
            'unsupported_factual_step_claims':unsupported,'unsupported_record_references':novel,
            'citation_errors':bad_citations,'assumption_cases':len(affected),
            'incomplete_labels_without_observed_violation':unsubstantiated_failures,
            'assumption_case_ids':[r['case_id'] for r in affected],
            'assumption_kinds':dict(Counter(a['kind'] for r in affected for a in r['assumptions'])),
            'inferred_state_cases':[r['case_id'] for r in records if r['inferred_states']],
            'unresolved_case_ids':[r['case_id'] for r in records if r['row'] is None]}


def render(results):
    lines=['# Decision-policy comparison','',
           'The same participant evidence and genuine offline model interpretations feed all policies. Public expected answers are read only by this evaluator. No new API calls, resource IDs or historical events are created. The existing strict CLI stays unchanged by default. These are prediction-policy experiments, not newly discovered evidence.','',
           '## Facts, deductions and predictions','',
           'Structured states and model-interpreted media facts retain source/time provenance. Exhaustive scoped absence is a logical deduction for an already grounded key. A COMPLETE case label is a policy conclusion about discovered coverage, not a directly observed global fact. Media interpretation itself remains fallible.','',
           '- **Strict auditor:** current discovery, all known treatment checks and a primary-account/tombstone completion anchor; abstains on missing proof. Its returned rows are supported relative to that discovery policy, not an independent guarantee of exhaustive truth.',
           '- **Conservative fallback:** retains strict rows, predicts INCOMPLETE for every strict hold, and emits no invented findings. These empty plans are deliberately preserved as invalid experimental rows. Missing confirmation does not establish a violation; this is a rejected baseline, not a submission option.',
           '- **Evidence-based prediction:** retains strict decisions; otherwise predicts from eligible known treatments without an extra mandatory account anchor. Unknown tombstone treatment remains unknown, with conditional compliance recorded externally. For a literally present retained archive with unknown restore permission, it forecasts potential restore risk; that ACTIVE finding is explicitly inferred and is counted as unsupported by direct current-state evidence. The source itself is never rewritten. Missing all eligible resources still yields abstention.','',
           '## Full-run structure and integrity','',
           '| Approach | Coverage | Valid / invalid rows | Labels C / I / N | Phase-compliant / noncompliant | Novel resource references | Unsupported factual step claims | I labels without observed violation | Assumption cases | Full file schema/citations |',
           '| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for approach in APPROACHES:
        r=results['full'][approach];c=r['coverage'];l=r['labels'];p=r['phase_compliance']
        lines.append(f"| {approach} | {c['covered_cases']}/{c['requested_cases']} ({c['coverage_rate']:.2%}) | {r['valid_rows']} / {r['invalid_rows']} | {l.get('COMPLETE',0)} / {l.get('INCOMPLETE',0)} / {l.get('NOT_APPLICABLE',0)} | {p.get('compliant',0)} / {p.get('noncompliant',0)} | {len(r['unsupported_record_references'])} | {len(r['unsupported_factual_step_claims'])} | {len(r['incomplete_labels_without_observed_violation'])} | {r['assumption_cases']} | {'Pass' if r['file_contract_valid'] else 'Fail'} |")
    lines += ['', 'C=COMPLETE, I=INCOMPLETE, N=NOT_APPLICABLE. INCOMPLETE requires all three phases; COMPLETE correctly has verification only; NOT_APPLICABLE has no plan. Valid row/file counts measure serialization, phase/operation requirements and citation availability, not entailment of every prediction. Assumption-dependent completeness claims are counted separately from individual step claims; zero unsupported steps does not mean zero uncertainty.', '',
              '| Approach | Coverage excluding confirmed cases | Valid / invalid | Unsupported factual steps | Assumption cases | Remaining missing |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for approach in APPROACHES:
        full=results['full'][approach];r=full['excluding_confirmed']
        lines.append(f"| {approach} | {r['covered_cases']}/{r['requested_cases']} ({r['coverage_rate']:.2%}) | {full['excluding_confirmed_valid_rows']} / {full['excluding_confirmed_invalid_rows']} | {full['excluding_confirmed_unsupported_steps']} | {full['excluding_confirmed_assumption_cases']} | {len(r['blocked_case_ids'])} |")
    lines += ['', 'Only case_39 and case_55 are excluded in this separate view. Exclusions do not enter decision logic; the original file contract still requires all518 rows pending clarification.', '',
              'INCOMPLETE three-phase compliance: '+ '; '.join(f"{a}: {results['full'][a]['phase_compliance'].get('incomplete_three_phase_compliant',0)}/{results['full'][a]['labels'].get('INCOMPLETE',0)}" for a in APPROACHES)+'.', '',
              '## All 32 public samples', '',
              '| Approach | Coverage | Valid / invalid rows | Status accuracy | Exact sequence | Step P / R / F1 | Fields |', '| --- | ---: | ---: | ---: | ---: | --- | ---: |']
    for approach in APPROACHES:
        r=results['samples'][approach];m=r['accuracy'];c=r['coverage']
        lines.append(f"| {approach} | {c['covered_cases']}/32 | {r['valid_rows']} / {r['invalid_rows']} | {m['status_accuracy']:.2%} ({m['status_correct']}/32) | {m['sequence_accuracy']:.2%} ({m['sequence_correct']}/32) | {m['step_precision']:.2%} / {m['step_recall']:.2%} / {m['step_f1']:.2%} | {m['field_accuracy']:.2%} |")
    lines += ['', 'Missing rows remain incorrect in every primary case metric. Prediction policy selection and debugging use these development samples, so this is not hidden-set accuracy or a held-out estimate. Full-set label accuracy cannot be measured without prohibited hidden truth. Exact sequences remain limited by missing eligible account keys, independent additional evidence, and document/policy interpretation gaps.', '',
              '## Assumption ledger and unsupported claims','']
    for split in ('full','samples'):
        lines += [f'### {split}', '']
        for approach in APPROACHES:
            r=results[split][approach]
            lines += [f"**{approach}:** {r['assumption_cases']} cases affected. " + (', '.join(r['assumption_case_ids']) or 'None') + '.', '',
                      'Assumption counts: '+json.dumps(r['assumption_kinds'],sort_keys=True)+'.', '',
                      'Still abstained: '+(', '.join(r['unresolved_case_ids']) or 'none')+'.', '']
            for claim in r['unsupported_factual_step_claims']:
                step=claim['step']
                lines.append(f"- `{claim['case_id']}`: `{step['operation']}` on `{step['system_id']}/{step['resource_id']}`, citing `{step['evidence_id']}`. The source establishes existence, not current restore authorization. This is a forecast, not a proven ACTIVE setting.")
    lines += ['', '## Recommendation and limits','',
              'The evidence-based prediction policy is the strongest schema-valid full-file candidate among these three approaches. It improves measured public status coverage/accuracy while retaining known violations, cutoff rules, required retention, resource IDs and genuine citations. The strict auditor remains the strongest evidence-certification baseline. The conservative fallback fails required plan structure and should not be submitted.', '',
              'This recommendation is conditional: the prediction file is not a certificate that every deletion is complete. Added COMPLETE labels rely on discovered evidence bounding relevant copies; unknown tombstone removal is not proven. One explicit archive-risk finding is inferred from existence and lacks direct authorization proof. The report counts that claim even though its case is among the two confirmed exclusions. No probability calibration or hidden-set benefit is claimed, and exact-sequence performance must be considered alongside status gains.', '',
              'Sensitivity check: withholding the forecast row leaves '+str(results['full']['evidence_prediction']['without_forecast_rows']['covered_cases'])+'/518 rows, while covering '+str(results['full']['evidence_prediction']['without_forecast_rows_excluding_confirmed']['covered_cases'])+'/516 cases after confirmed exclusions. The status gains on public samples do not depend on the archive forecast. If organizers authorize omitting excluded rows, this unconfirmed claim is unnecessary for evaluated coverage; until then the full candidate keeps it explicitly labeled as a prediction in the sidecar.', '',
              'The three public requests with no eligible owned resource remain absent from the prediction candidate rather than gaining made-up verification keys. The full dataset has different evidence/cutoffs; a full-file candidate does not establish full public-sample coverage. Keep strict blockers, source facts and per-case assumptions alongside any prediction CSV. Do not present the prediction policy as having resolved the underlying97 account-proof gaps or the tombstone uncertainty.', '',
              'Reproduce with `code/compare_approaches.py` for full/sample candidates, then `code/evaluation/compare_approaches.py`. All comparison inference is offline. Existing genuine model extraction work is reused once across policies; production token attribution must not be tripled. Paid API budget remains$0.', '']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,default=ROOT/'.cache/approach_comparison')
    parser.add_argument('--report',type=Path,default=ROOT/'code/evaluation/approach_comparison.md')
    parser.add_argument('--json',type=Path,default=ROOT/'.cache/approach_comparison/metrics.json',dest='json_path')
    args=parser.parse_args()
    for path,suffix,allowed in [(args.report,'.md',ROOT/'code/evaluation/approach_comparison.md'),
                                (args.json_path,'.json',ROOT/'.cache/approach_comparison/metrics.json')]:
        target=path.resolve()
        if target.suffix!=suffix or target.is_relative_to(ROOT/'dataset') or (target.is_relative_to(ROOT) and target!=allowed and not target.is_relative_to(ROOT/'.cache')):
            parser.error('Use designated reports, .cache, or external destinations')
    results={};excluded=load_guidance()['confirmed_excluded_case_ids']
    for split in ('full','samples'):
        requests,store,identities,history,rules,intents=load_context(ROOT,ROOT/'dataset',split=='samples',True)
        observed={}
        for request in requests:
            cid=request['case_id']
            if not intents[cid]:
                observed[cid]=[];continue
            subject=identities.resolve(request['email'],request['audit_at'])
            try:observed[cid]=select_states(subject,store,request['audit_at'])
            except (InsufficientEvidence,ValueError):observed[cid]=[]
        results[split]={}
        for approach in APPROACHES:
            rows=read_csv(args.input_dir/split/f'{approach}.csv')
            records=json.loads((args.input_dir/split/f'{approach}.json').read_text())
            result=assess(rows,records,requests,observed,rules,read_csv(ROOT/'dataset/evidence_files.csv'),store.activities,history,excluded)
            if split=='samples':result['accuracy']=evaluate(rows,read_csv(ROOT/'dataset/sample_output.csv'))
            results[split][approach]=result
    args.report.parent.mkdir(parents=True,exist_ok=True);args.json_path.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(render(results),encoding='utf-8')
    args.json_path.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    for split,items in results.items():
        print(split,{a:{'covered':r['coverage']['covered_cases'],'valid':r['valid_rows'],'invalid':r['invalid_rows'],
                        'unsupported_factual_steps':len(r['unsupported_factual_step_claims'])} for a,r in items.items()})


if __name__=='__main__':main()
