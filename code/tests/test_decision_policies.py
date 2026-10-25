import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import Observation, Subject, validate_output
from decision_policies import decide
from evidence import EvidenceStore

NOW = '2026-09-10T12:00:00Z'
REQUEST = {'case_id': 'synthetic', 'audit_at': NOW}
SUBJECT = Subject('user_custom', {'user_custom'})
RULES = [{'data_category': 'SECURITY_AUDIT_LOG', 'required_action': 'RETAIN'},
         {'data_category': 'USER_PROFILE', 'required_action': 'DELETE'},
         {'data_category': 'BACKUP_ARCHIVE', 'required_action': 'RETAIN'},
         {'data_category': 'ACCOUNT_TOMBSTONE', 'required_action': 'REDACT'}]


def obs(resource='audit_custom', category='SECURITY_AUDIT_LOG', state='PRESENT', **updates):
    values = dict(system='security_service', resource=resource, category=category, state=state,
                  evidence_id='source', captured_at=NOW, observed_at=NOW, identifiers={'user_custom'}, data={})
    return Observation(**{**values, **updates})


class DecisionPolicyTests(unittest.TestCase):
    def decide(self, approach, observations):
        return decide(REQUEST, SUBJECT, EvidenceStore(observations), RULES, True, approach)

    def test_policies_expose_absence_of_primary_confirmation_without_inventing_a_record(self):
        observations = [obs()]
        strict = self.decide('strict_auditor', observations)
        conservative = self.decide('conservative_fallback', observations)
        predicted = self.decide('evidence_prediction', observations)
        self.assertIsNone(strict['row'])
        self.assertEqual(conservative['row']['deletion_status'], 'INCOMPLETE')
        with self.assertRaises(ValueError):
            validate_output([conservative['row']], [REQUEST])
        self.assertEqual(predicted['row']['deletion_status'], 'COMPLETE')
        steps = json.loads(predicted['row']['steps_json'])
        self.assertEqual([step['resource_id'] for step in steps], ['audit_custom'])
        self.assertEqual(steps[0]['evidence_id'], 'source')
        self.assertTrue(predicted['assumptions'])
        self.assertEqual(observations[0].state, 'PRESENT')

    def test_unknown_tombstone_never_becomes_a_redacted_fact(self):
        result = self.decide('evidence_prediction', [obs(), obs('tombstone_custom', 'ACCOUNT_TOMBSTONE', 'UNKNOWN')])
        self.assertEqual(result['row']['deletion_status'], 'COMPLETE')
        self.assertNotIn('VERIFY_RECORD_REDACTED', result['row']['steps_json'])
        self.assertEqual(result['unresolved_records'][0]['state'], 'UNKNOWN')
        self.assertEqual(len(result['assumptions']), 2)

    def test_observed_violation_has_same_three_phase_plan_in_all_policies(self):
        observations = [obs('account_custom', 'USER_PROFILE', system='account_service')]
        rows = [self.decide(approach, observations)['row'] for approach in ('strict_auditor', 'conservative_fallback', 'evidence_prediction')]
        self.assertEqual(rows[0], rows[1]); self.assertEqual(rows[1], rows[2])
        self.assertEqual([step['phase'] for step in json.loads(rows[0]['steps_json'])], ['FINDING','REMEDIATION','VERIFICATION'])

    def test_prediction_never_uses_future_capture_or_invents_verification_without_known_states(self):
        future = obs('account_custom', 'USER_PROFILE', 'ABSENT', system='account_service', captured_at='2026-09-11T00:00:00Z')
        self.assertIsNone(self.decide('evidence_prediction', [future])['row'])
        result = self.decide('evidence_prediction', [obs(), future])
        self.assertNotIn('account_custom', result['row']['steps_json'])

    def test_required_retention_failure_still_blocks_prediction(self):
        self.assertIsNone(self.decide('evidence_prediction', [obs(state='ABSENT')])['row'])

    def test_archive_risk_forecast_is_explicit_and_does_not_rewrite_actual_state(self):
        archive = obs('backup_custom', 'BACKUP_ARCHIVE', 'UNKNOWN', system='backup_service',
                      data={'_source_fact_record': {'state': 'PRESENT'}})
        result = self.decide('evidence_prediction', [archive])
        self.assertEqual(result['row']['deletion_status'], 'INCOMPLETE')
        self.assertEqual(json.loads(result['row']['steps_json'])[0]['operation'], 'REPORT_RESTORE_RISK')
        self.assertEqual(result['inferred_states'][0]['predicted_state'], 'ACTIVE')
        self.assertEqual(archive.state, 'UNKNOWN')
        self.assertIsNone(self.decide('strict_auditor', [archive])['row'])
        self.assertIsNone(self.decide('evidence_prediction', [obs('backup_custom','BACKUP_ARCHIVE','UNKNOWN')])['row'])

    def test_non_deletion_is_not_an_uncertainty_fallback(self):
        for approach in ('strict_auditor', 'conservative_fallback', 'evidence_prediction'):
            result = decide(REQUEST, None, EvidenceStore(), RULES, False, approach)
            self.assertEqual(result['row']['deletion_status'], 'NOT_APPLICABLE')
            self.assertEqual(result['assumptions'], [])
