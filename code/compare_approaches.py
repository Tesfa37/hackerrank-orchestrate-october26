"""Generate offline comparison candidates and fact/assumption ledgers, never labels from gold."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

from audit_core import read_csv, write_output, validate_citations
from decision_policies import APPROACHES, decide
from investigate import load_context

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', action='store_true')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--write-prediction-candidate', type=Path,
                        help='Explicitly publish the full evidence-prediction CSV with its external assumptions ledger')
    args = parser.parse_args()
    target = args.output_dir.resolve()
    if target.is_relative_to(ROOT/'dataset') or target == ROOT or target.is_relative_to(ROOT/'code'):
        parser.error('Use .cache, review_artifacts, or a separate directory for comparison candidates')
    candidate = args.write_prediction_candidate.resolve() if args.write_prediction_candidate else None
    if candidate and (args.samples or candidate.suffix.lower() != '.csv' or candidate.is_relative_to(ROOT/'dataset') or candidate.is_relative_to(ROOT/'code')):
        parser.error('Prediction publication requires the full request set and a CSV outside participant inputs/code')
    requests, store, identities, history, rules, intents, usage = load_context(ROOT, ROOT/'dataset', args.samples, True, with_usage=True)
    target.mkdir(parents=True, exist_ok=True)
    (target/'usage_summary.json').write_text(json.dumps({k:v for k,v in usage.items() if k!='records'},indent=2)+'\n',encoding='utf-8')
    summary = {}
    prediction_records, prediction_rows = [], []
    for approach in APPROACHES:
        records = []
        for request in requests:
            intent = intents[request['case_id']]
            subject = identities.resolve(request['email'], request['audit_at']) if intent else None
            records.append(decide(request, subject, store, rules, intent, approach))
        records.sort(key=lambda item: item['case_id'])
        rows = [item['row'] for item in records if item['row'] is not None]
        # This experimental writer also preserves invalid fallback candidates so
        # evaluation can count them. Production write_output remains unchanged.
        with (target/f'{approach}.csv').open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, ['case_id', 'deletion_status', 'steps_json'], lineterminator='\n')
            writer.writeheader(); writer.writerows(rows)
        (target/f'{approach}.json').write_text(json.dumps(records, indent=2)+'\n', encoding='utf-8')
        summary[approach] = {'returned': len(rows), 'requests': len(requests),
                             'assumption_cases': sum(bool(item['assumptions']) for item in records)}
        if approach == 'evidence_prediction':
            prediction_records, prediction_rows = records, rows
    if candidate:
        # This path still uses the exact production schema/citation validators.
        # Inferences are declared externally, not promoted to source facts.
        records, rows = prediction_records, prediction_rows
        validate_citations(rows, requests, read_csv(ROOT/'dataset/evidence_files.csv'),
                           store.activities, history, store.observations)
        candidate.parent.mkdir(parents=True, exist_ok=True)
        temporary = candidate.with_name(candidate.name+'.tmp')
        try:
            write_output(temporary,rows,requests)
            temporary.replace(candidate)
        finally:
            temporary.unlink(missing_ok=True)
        ledger = {'created_at':datetime.now(timezone.utc).isoformat(), 'approach':'evidence_prediction',
                  'kind':'prediction candidate, not strict audit certification', 'requested_cases':len(requests),
                  'csv_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
                  'new_model_calls':0, 'assumption_cases':sum(bool(r['assumptions']) for r in records),
                  'usage_summary':{k:v for k,v in usage.items() if k!='records'},
                  'cases':[r for r in records if r['assumptions']]}
        candidate.with_suffix('.assumptions.json').write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
        print('Published prediction candidate and assumptions ledger:',candidate)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
