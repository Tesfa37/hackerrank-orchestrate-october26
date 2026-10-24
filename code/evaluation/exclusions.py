"""Evaluation-only coverage accounting; never imported by the predictor."""
from collections import Counter
import json
from pathlib import Path


def load_guidance():
    return json.loads(Path(__file__).with_name('organizer_guidance.json').read_text(encoding='utf-8'))


def coverage_view(request_ids, predicted_ids, excluded_ids=()):
    requested, predicted = list(request_ids), list(predicted_ids)
    if len(set(requested)) != len(requested) or len(set(predicted)) != len(predicted):
        raise ValueError('Coverage inputs contain duplicate case IDs')
    excluded = set(excluded_ids)
    eligible = set(requested) - excluded
    covered = eligible & set(predicted)
    return {'requested_cases': len(eligible), 'covered_cases': len(covered),
            'coverage_rate': len(covered) / len(eligible) if eligible else None,
            'blocked_case_ids': sorted(eligible - set(predicted)),
            'excluded_request_ids': sorted(set(requested) & excluded),
            'excluded_returned_ids': sorted(set(requested) & set(predicted) & excluded),
            'unexpected_prediction_ids': sorted(set(predicted) - set(requested))}


def run_views(request_ids, predicted_ids, blocker_report, excluded_ids):
    original = coverage_view(request_ids, predicted_ids)
    adjusted = coverage_view(request_ids, predicted_ids, excluded_ids)
    cases = blocker_report['cases']
    blocked_ids = [case['case_id'] for case in cases]
    if (len(blocked_ids) != len(set(blocked_ids))
            or set(blocked_ids) != set(original['blocked_case_ids'])
            or blocker_report['request_count'] != original['requested_cases']
            or blocker_report['resolved_count'] != original['covered_cases']
            or original['unexpected_prediction_ids']):
        raise ValueError('Predictions, request IDs and blocker diagnostics do not describe the same run')
    original['blocker_group_counts'] = dict(Counter(case['group'] for case in cases))
    remaining = [case for case in cases if case['case_id'] not in set(excluded_ids)]
    adjusted['blocker_group_counts'] = dict(Counter(case['group'] for case in remaining))
    return {'original': original, 'excluding_confirmed': adjusted}
