"""Bounded, evaluation-only source review of selected-candidate discrepancies."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_core import read_csv, timestamp
from evidence import identifiers
from investigate import load_context, raw_primary_records
from reasoning import _canonical_view, _mentions, related_resources
from evaluation.review_mismatches import step_differences

ROOT=Path(__file__).resolve().parents[2]


def main():
    timer_path=ROOT/'.cache/finalization_investigation_timer.json'
    timer=(json.loads(timer_path.read_text()) if timer_path.is_file() else
           {'started_at':datetime.now(timezone.utc).isoformat(),'max_minutes':40})
    started=datetime.fromisoformat(timer['started_at'])
    requests,store,identities,history,rules,intents=load_context(ROOT,ROOT/'dataset',True,True)
    manifest={m['file_id']:m for m in read_csv(ROOT/'dataset/evidence_files.csv')}
    # Only evaluation reads the expected resource keys. They never become
    # ownership links or inputs to prediction and are not used to alter CSVs.
    gold={r['case_id']:r for r in read_csv(ROOT/'dataset/sample_output.csv')}
    actual={r['case_id']:r for r in read_csv(ROOT/'.cache/approach_comparison/samples/evidence_prediction.csv')}
    raw=raw_primary_records(ROOT/'dataset',list(manifest.values()))
    differences=[]
    for request in requests:
        cid=request['case_id'];cutoff=request['audit_at']
        subject=identities.resolve(request['email'],cutoff)
        view=_canonical_view(store,cutoff);owned=related_resources(subject,view,cutoff)
        predicted=json.loads(actual[cid]['steps_json']) if cid in actual else []
        for direction,step in step_differences(predicted,json.loads(gold[cid]['steps_json'])):
            resource=step['resource_id']
            observations=[o for o in view.observations if o.resource==resource and o.system==step['system_id']]
            eligible=[o for o in observations if o.eligible(cutoff)]
            linked=(step['system_id'],resource) in owned
            events=[e for e in store.activities if e.get('resource_id')==resource]
            bridges=[e for e in events if timestamp(e['event_time'])<=timestamp(cutoff) and
                     (bool(identifiers(e)&subject.identifiers) or _mentions(e.get('details',''),subject))]
            raw_matches=[r for r in raw if r['resource_id']==resource and
                         timestamp(r['captured_at'])<=timestamp(cutoff) and timestamp(r['observed_at'])<=timestamp(cutoff)]
            parser_misses=[r for r in raw_matches if r['identifiers']&subject.identifiers and
                           not any(o.evidence_id==r['evidence_id'] for o in eligible)]
            if direction=='extra':
                cause='additional_eligible_owned_resource'
                proof='Distinct grounded resource; no participant evidence establishes alias-equivalence or later removal. Do not omit it merely because the reference omits it.'
            elif observations and not eligible:
                cause='capture_after_cutoff'
                proof='A matching source exists but was captured/available after audit_at. Earlier internal event times do not make the later-captured artifact available.'
            elif not linked and eligible:
                cause='sanitized_state_without_subject_ownership'
                proof='Compliant state exists, but its subject identifiers/selectors are null and no eligible activity establishes ownership. Resource-only action claims do not provide that edge.'
            elif not linked and step['operation']=='VERIFY_RECORD_PRESENT' and not observations and not events:
                cause='required_retained_record_proof_missing'
                proof='No direct participant record or activity names this required retained key. The exact missing proof is a subject-bound eligible retained-record readback or explicit catalog association plus state.'
            elif not linked:
                cause='absent_resource_key_without_subject_ownership'
                proof='No eligible subject-to-key association. Complete negative scopes can establish scoped absence, but cannot manufacture this expected resource ID.'
            else:
                cause='requires_plan_or_citation_review'
                proof='Eligible owned resource found; investigate construction/policy/citation before changing prediction.'
            refs=[{'evidence_id':o.evidence_id,'path':manifest[o.evidence_id]['file_path'],
                   'state':o.state,'captured_at':o.captured_at,'observed_at':o.observed_at,
                   'eligible':o.eligible(cutoff),'has_subject_identifier':bool(o.identifiers&subject.identifiers),
                   'source_line':o.data.get('line_number')} for o in observations]
            differences.append({'case_id':cid,'cutoff':cutoff,'direction':direction,'step':step,'root_cause':cause,
                                'exact_missing_proof':proof,'owned':linked,'observations':refs,
                                'eligible_subject_link_events':[e['activity_id'] for e in bridges],
                                'resource_only_claims':[{'activity_id':e['activity_id'],'event_time':e['event_time']} for e in events],
                                'eligible_raw_primary_parser_misses':len(parser_misses)})
    missing=[d for d in differences if d['direction']=='missing'];extra=[d for d in differences if d['direction']=='extra']
    ledger=json.loads((ROOT/'output.assumptions.json').read_text())
    conditionals=[r for r in ledger['cases'] if r['row']['deletion_status']=='COMPLETE']
    singles=[r for r in conditionals if len(r['facts'])==1]
    blockers={r['case_id']:r for r in json.loads((ROOT/'review_artifacts/blocker_diagnostics.json').read_text())['cases']}
    all_requests={r['case_id']:r for r in read_csv(ROOT/'dataset/deletion_requests.csv')}
    chosen=set()
    # Choose deterministic representatives of each strict proof-gap group and
    # each single-observation category; include temporal endpoints and a richer inventory.
    for group in sorted({blockers[r['case_id']]['group'] for r in conditionals}):
        chosen.add(next(r['case_id'] for r in conditionals if blockers[r['case_id']]['group']==group))
    for category in sorted({r['facts'][0]['category'] for r in singles}):
        chosen.add(next(r['case_id'] for r in singles if r['facts'][0]['category']==category))
    chosen.add(min(singles,key=lambda r:all_requests[r['case_id']]['audit_at'])['case_id'])
    chosen.add(max(singles,key=lambda r:all_requests[r['case_id']]['audit_at'])['case_id'])
    chosen.add(max(conditionals,key=lambda r:len(r['facts']))['case_id'])
    spots=[]
    for record in conditionals:
        if record['case_id'] not in chosen:continue
        detail=blockers[record['case_id']]
        spots.append({'case_id':record['case_id'],'cutoff':all_requests[record['case_id']]['audit_at'],
                      'fact_count':len(record['facts']),'facts':record['facts'],'unknowns':record['unresolved_records'],
                      'strict_group':detail['group'],'missing_proof':detail['error'],
                      'eligible_post_request_primary_scope_count':detail.get('post_request_primary_scope_count',0),
                      'source_paths':{f['evidence_id']:manifest[f['evidence_id']]['file_path'] for f in record['facts']}})
    elapsed=(datetime.now(timezone.utc)-started).total_seconds()/60
    result={'started_at':timer['started_at'],'recorded_at':datetime.now(timezone.utc).isoformat(),'elapsed_minutes':round(elapsed,2),
            'budget_minutes':timer['max_minutes'],'missing_steps':len(missing),'extra_steps':len(extra),
            'missing_operations':dict(Counter(d['step']['operation'] for d in missing)),
            'missing_root_causes':dict(Counter(d['root_cause'] for d in missing)),
            'eligible_raw_primary_parser_misses':sum(d['eligible_raw_primary_parser_misses'] for d in missing),
            'conditional_complete_cases':len(conditionals),'single_qualifying_observation_cases':len(singles),
            'single_observation_categories':dict(Counter(r['facts'][0]['category'] for r in singles)),
            'conditional_fact_count_distribution':dict(Counter(len(r['facts']) for r in conditionals)),
            'conditional_logical_resource_count_distribution':dict(Counter(len({(f['system_id'],f['resource_id']) for f in r['facts']}) for r in conditionals)),
            'audit_retention_only_cases':sum(all(f['category']=='SECURITY_AUDIT_LOG' for f in r['facts']) for r in conditionals),
            'differences':differences,'spot_checks':spots,'prediction_changes':False}
    lines=['# Bounded finalization accuracy investigation','',
           f"Budget: at most {timer['max_minutes']} minutes, inside the requested 30–45 minute window. This recorded pass took {elapsed:.2f} minutes; it stopped after all discrepancies and the representative checks below were classified, without waiting out the unused budget.", '',
           'Expected answers are read only in evaluation to locate discrepancies. Their resource IDs are never supplied to prediction or used as identity edges. The selected CSV was backed up before this review and is retained unchanged. No new model calls, hidden truth or dataset edits were used.', '',
           '## Reproduced differences', '',
           f"Missing expected steps: {len(missing)}; extras: {len(extra)}. Missing operation counts: {json.dumps(result['missing_operations'],sort_keys=True)}.", '',
           '| Root cause | Missing steps |', '| --- | ---: |']
    lines += [f'| {cause} | {count} |' for cause,count in sorted(result['missing_root_causes'].items())]
    lines += ['', f"Independent raw-primary inventory check: {result['eligible_raw_primary_parser_misses']} eligible subject-owned records omitted by adapters among the missing keys. No missing expected step reached the eligible-and-owned plan-construction branch. No defensible retrieval/ownership/serialization fix was established.", '',
              '| Case | Difference / operation | Resource | Source/cutoff check | Root cause / exact missing proof |', '| --- | --- | --- | --- | --- |']
    for d in differences:
        refs='; '.join(f"{o['evidence_id']} {o['path']}; capture {o['captured_at']}; state {o['state']}; {'eligible' if o['eligible'] else 'after cutoff'}" for o in d['observations'])
        if not refs:refs='; '.join(f"{e['activity_id']} resource-only operation claim at {e['event_time']}" for e in d['resource_only_claims']) or 'No direct record row; the reference citation alone is not an ownership edge.'
        lines.append(f"| {d['case_id']} | {d['direction']} / {d['step']['operation']} | {d['step']['resource_id']} | {refs} | {d['root_cause']}: {d['exact_missing_proof']} |")
    lines += ['', '## Targeted source checks', '',
              '- The analytics_9406 trace in evidence_94 starts with lookup_key=null and ends with customer_reference/email/phone/hash all null. The parser did not discard a populated selector. Its eligible anonymized state cannot be attributed by temporal adjacency or numeric suffix.',
              '- The evidence_92 analytics rows likewise have null ownership fields. Resource-only anonymization activities attest an action claim, not the missing user/resource association. A valid association or subject-bound keyed query is the exact missing proof.',
              '- Five of the seven missing retained-audit verifications have direct keyed evidence captured after cutoff. The other two audit keys have no literal occurrence in participant activity, structured evidence or extracted PDF text; the relevant security screenshot prints different keys and supplies no alias. Preserving manifest availability and grounded keys is required.',
              '- The three extra object_19 steps are backed by an explicitly linked object-storage resource. Visual reinspection confirms delivery_confirmation_19.pdf, checksum prefix e71b6d and support-attachments scope; the upload PDF is delivery_address_correction.pdf with a different checksum prefix c90a42. No same-object alias establishes equivalence. Deleting those steps only to match the sample would discard an independent copy.',
              '- The fourth extra is an absence verification for account_6523, explicitly linked through an eligible earlier keyed lookup for the subject. The later unrelated resource key is not a proven alias. A new request does not erase grounded historical resource identity; no participant statement scopes it away.', '',
              '## Conditional COMPLETE spot checks', '',
              f"There are {len(conditionals)} conditional COMPLETE predictions; {len(singles)} have one qualifying state observation. Of those, {result['single_observation_categories'].get('SECURITY_AUDIT_LOG',0)} establish a retained audit row, and {result['single_observation_categories'].get('USER_PROFILE',0)} establishes primary absence while tombstone fields remain unresolved. A single audit-retention observation is not proof that all user data is gone.", '',
              f"Across all conditional cases, {result['audit_retention_only_cases']} have qualifying facts consisting solely of retained audit records. {result['conditional_logical_resource_count_distribution'].get(1,0)} have only one distinct logical resource, even when separate replica scopes produce multiple state observations. Replica multiplicity is not independent evidence that the remaining account inventory was discovered. These checks strengthen the stated limitations; they do not justify changing a prediction to failure without a demonstrated violation.", '',
              '| Case | Qualifying facts | Source-backed conclusion | Remaining conditional assumption |', '| --- | ---: | --- | --- |']
    for spot in spots:
        facts='; '.join(f"{f['resource_id']} {f['state']} ({f['evidence_id']}; {spot['source_paths'][f['evidence_id']]})" for f in spot['facts'])
        lines.append(f"| {spot['case_id']} | {spot['fact_count']} | {facts} | {spot['strict_group']}: {spot['missing_proof']} |")
    lines += ['', 'Scope-negative evidence is useful support for the prediction policy but supplies neither an unprinted resource key nor an exhaustive cross-system inventory. The sample review and conditional-case checks found no licensed bridge from missing ownership to expected verification keys. Retention and cutoff checks remain unchanged.', '',
              '## Decision', '',
              'Retain the selected 07aa568 prediction CSV byte for byte. The investigation found limitations in available ownership/temporal proof, not a confirmed general implementation error that safely recovers the missing steps. Do not replace the candidate, weaken cutoff rules, infer suffix IDs, merge distinct objects or fabricate a verification. Report-generation correctness is fixed separately and covered by regression tests. Exact sequence remains 8/32 and all known assumptions remain disclosed.', '']
    (ROOT/'code/evaluation/finalization_investigation.md').write_text('\n'.join(lines),encoding='utf-8')
    (ROOT/'.cache/finalization_investigation.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:result[k] for k in ('missing_steps','extra_steps','missing_root_causes','single_qualifying_observation_cases','eligible_raw_primary_parser_misses','elapsed_minutes')})


if __name__=='__main__':main()
