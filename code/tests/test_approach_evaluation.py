import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_core import Observation
from evaluation.compare_approaches import factual_support

class ApproachSupportTests(unittest.TestCase):
    def test_restore_prediction_is_not_mislabeled_as_observed_configuration(self):
        step=dict(step_no=1,phase='FINDING',system_id='backup_service',resource_id='backup_custom',
                  operation='REPORT_RESTORE_RISK',state='ACTIVE',evidence_id='source')
        row=dict(case_id='synthetic',deletion_status='INCOMPLETE',steps_json=json.dumps([step]))
        observation=Observation('backup_service','backup_custom','BACKUP_ARCHIVE','UNKNOWN','source',
                                '2026-09-10T00:00:00Z','2026-09-10T00:00:00Z')
        unsupported,novel=factual_support(row,[observation],[], '2026-09-10T00:00:00Z')
        self.assertEqual(unsupported,[step]);self.assertEqual(novel,[])
        observation.state='ACTIVE'
        self.assertEqual(factual_support(row,[observation],[],'2026-09-10T00:00:00Z'),([],[]))

    def test_future_state_cannot_validate_a_finding(self):
        step=dict(step_no=1,phase='FINDING',system_id='account_service',resource_id='account_custom',
                  operation='REPORT_REMAINING_RECORD',state='PRESENT',evidence_id='source')
        row=dict(case_id='synthetic',deletion_status='INCOMPLETE',steps_json=json.dumps([step]))
        observation=Observation('account_service','account_custom','USER_PROFILE','PRESENT','source',
                                '2026-09-11T00:00:00Z','2026-09-09T00:00:00Z')
        unsupported,novel=factual_support(row,[observation],[{'data_category':'USER_PROFILE','required_action':'DELETE'}], '2026-09-10T00:00:00Z')
        self.assertEqual(unsupported,[step]);self.assertEqual(novel,[step])

    def test_retention_evidence_does_not_support_deletion_verification(self):
        step=dict(step_no=1,phase='VERIFICATION',system_id='security_service',resource_id='audit_custom',
                  operation='VERIFY_RECORD_ABSENT',state='ABSENT',evidence_id='source')
        row=dict(case_id='synthetic',deletion_status='COMPLETE',steps_json=json.dumps([step]))
        observation=Observation('security_service','audit_custom','SECURITY_AUDIT_LOG','PRESENT','source',
                                '2026-09-09T00:00:00Z','2026-09-09T00:00:00Z')
        unsupported,novel=factual_support(row,[observation],[{'data_category':'SECURITY_AUDIT_LOG','required_action':'RETAIN'}], '2026-09-10T00:00:00Z')
        self.assertEqual(unsupported,[step]);self.assertEqual(novel,[])
