import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.exclusions import coverage_view, run_views


class ExclusionCoverageTests(unittest.TestCase):
    def test_excluding_one_returned_and_one_blocked_request(self):
        blockers = {'request_count': 4, 'resolved_count': 2,
                    'cases': [{'case_id': 'c', 'group': 'missing_proof'},
                              {'case_id': 'd', 'group': 'cutoff'}]}
        views = run_views(['a', 'b', 'c', 'd'], ['a', 'b'], blockers, ['b', 'c'])
        self.assertEqual(views['original']['covered_cases'], 2)
        self.assertEqual(views['original']['requested_cases'], 4)
        adjusted = views['excluding_confirmed']
        self.assertEqual(adjusted['covered_cases'], 1)
        self.assertEqual(adjusted['requested_cases'], 2)
        self.assertEqual(adjusted['blocked_case_ids'], ['d'])
        self.assertEqual(adjusted['blocker_group_counts'], {'cutoff': 1})
        self.assertEqual(views['original']['blocker_group_counts'], {'missing_proof': 1, 'cutoff': 1})

    def test_stale_diagnostics_cannot_silently_subtract_blockers(self):
        with self.assertRaisesRegex(ValueError, 'same run'):
            run_views(['a', 'b'], ['a'], {'request_count': 2, 'resolved_count': 1, 'cases': []}, ['b'])

    def test_unknown_exclusions_do_not_invent_requests_or_answers(self):
        view = coverage_view(['a', 'b'], ['a'], ['other'])
        self.assertEqual(view['coverage_rate'], 1/2)
        self.assertEqual(view['blocked_case_ids'], ['b'])
        self.assertEqual(view['excluded_request_ids'], [])

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            coverage_view(['a', 'a'], ['a'])
