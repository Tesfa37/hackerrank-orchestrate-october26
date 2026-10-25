"""Validate the selected CSV/ledger; optional source audit reuses genuine caches offline."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_core import read_csv, validate_output, validate_citations
from evaluation.main import load_predictions
from evaluation.finalize_reports import validate_ledger

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-context',action='store_true',help='Check source support against genuine offline interpretations')
    parser.add_argument('--report',type=Path,default=ROOT/'review_artifacts/finalization/validation.json')
    args=parser.parse_args()
    report=args.report.resolve()
    if (report.suffix!='.json' or report.is_relative_to(ROOT/'dataset') or report.is_relative_to(ROOT/'code')
            or report in {ROOT/'output.assumptions.json'}):
        parser.error('Validation must not overwrite input data, code or the assumptions ledger')
    rows=load_predictions(ROOT/'output.csv')
    ledger=json.loads((ROOT/'output.assumptions.json').read_text())
    requests=read_csv(ROOT/'dataset/deletion_requests.csv')
    manifest=read_csv(ROOT/'dataset/evidence_files.csv')
    activities=read_csv(ROOT/'dataset/system_activity.csv')
    history=read_csv(ROOT/'dataset/user_audit_log.csv')
    validate_output(rows,requests)
    validate_citations(rows,requests,manifest,activities,history)
    assumed=validate_ledger(ROOT/'output.csv',rows,ledger)
    if ledger['requested_cases']!=len(requests):
        raise ValueError('Ledger requested-case count differs from the actual dataset')
    result={'created_at':datetime.now(timezone.utc).isoformat(),
            'strategy':'selected evidence-based prediction; not conclusive deletion certification',
            'prediction_count':len(rows),'expected_count':len(requests),'labels':dict(Counter(r['deletion_status'] for r in rows)),
            'structural_validation_failures':0,'citation_id_or_capture_errors':0,
            'exact_case_id_set':True,'sorted_unique_case_ids':True,'csv_json_and_phase_requirements_valid':True,
            'csv_sha256':hashlib.sha256((ROOT/'output.csv').read_bytes()).hexdigest(),
            'ledger_sha256':hashlib.sha256((ROOT/'output.assumptions.json').read_bytes()).hexdigest(),
            'ledger_matches_all_affected_rows':True,'assumption_cases':len(ledger['cases']),
            'assumption_label_distribution':dict(assumed),
            'inferred_state_cases':[r['case_id'] for r in ledger['cases'] if r['inferred_states']]}
    if args.with_context:
        from investigate import load_context
        from reasoning import select_states, InsufficientEvidence
        from evaluation.compare_approaches import factual_support
        _,store,identities,_,rules,intents,usage=load_context(ROOT,ROOT/'dataset',False,True,with_usage=True)
        by_id={r['case_id']:r for r in requests};unsupported=[];novel=[]
        for row in rows:
            request=by_id[row['case_id']]
            if not intents[row['case_id']]:observations=[]
            else:
                subject=identities.resolve(request['email'],request['audit_at'])
                try:observations=select_states(subject,store,request['audit_at'])
                except (InsufficientEvidence,ValueError):observations=[]
            validate_citations([row],[request],manifest,activities,history,observations)
            failures,new_keys=factual_support(row,observations,rules,request['audit_at'])
            unsupported += [{'case_id':row['case_id'],'step':step} for step in failures]
            novel += [{'case_id':row['case_id'],'step':step} for step in new_keys]
        result['source_audit']={'new_model_calls':usage['new_calls_this_process'],
                                'unsupported_factual_step_claims':unsupported,'novel_resource_references':novel,
                                'usage_summary':{k:v for k,v in usage.items() if k!='records'},
                                'note':'Source support is relative to validated interpretations; it does not establish inventory completeness or hidden accuracy.'}
        declared={(case['case_id'],state['system_id'],state['resource_id'],state['predicted_state'])
                  for case in ledger['cases'] for state in case['inferred_states']}
        if novel or any((failure['case_id'],failure['step']['system_id'],failure['step']['resource_id'],failure['step']['state']) not in declared
                        for failure in unsupported):
            raise ValueError('Source audit found a novel resource or an undeclared unsupported factual claim')
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Validated selected candidate:',len(rows),'rows; structural failures:0; assumption cases:',len(ledger['cases']))
    if args.with_context:print('Direct source-support exceptions:',len(unsupported),'(disclosed forecast; not a structural error)')


if __name__=='__main__':main()
