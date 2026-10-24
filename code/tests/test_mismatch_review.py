import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('mismatch_review',Path(__file__).resolve().parents[1]/'evaluation/review_mismatches.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)

class MismatchReviewTests(unittest.TestCase):
    def test_wrong_citation_is_reported_as_missing_and_extra_content(self):
        expected=dict(phase='VERIFICATION',system_id='accounts',resource_id='record',operation='VERIFY_RECORD_ABSENT',state='ABSENT',evidence_id='proof',step_no=1)
        actual={**expected,'evidence_id':'different'}
        self.assertEqual([direction for direction,step in review.step_differences([actual],[expected])],['missing','extra'])

    def test_numbering_is_left_to_exact_sequence_scoring(self):
        expected=dict(phase='VERIFICATION',system_id='accounts',resource_id='record',operation='VERIFY_RECORD_ABSENT',state='ABSENT',evidence_id='proof',step_no=1)
        self.assertEqual(review.step_differences([{**expected,'step_no':2}],[expected]),[])
