"""Explicit decision policies over the same evidence; no public expected answers.

Predicted completeness is distinct from proved individual resource state. Only
the strict policy is used by the existing main CLI. Comparison candidates carry
an external assumptions ledger because the required CSV has no uncertainty field.
"""
from dataclasses import replace
from audit_core import validate_output
from reasoning import InsufficientEvidence, audit_request, plan_observations, select_states

APPROACHES = ('strict_auditor', 'conservative_fallback', 'evidence_prediction')


def fact(observation):
    data = observation.data
    basis = ('model_interpreted_media' if data.get('_media') else
             'entailed_scoped_absence' if data.get('_negative_scope') else 'structured_source_state')
    return {'system_id': observation.system, 'resource_id': observation.resource,
            'category': observation.category, 'state': observation.state,
            'evidence_id': observation.evidence_id, 'captured_at': observation.captured_at,
            'observed_at': observation.observed_at, 'available_at': observation.available_at.isoformat(),
            'scope': observation.scope, 'basis': basis}


def decide(request, subject, store, rules, intent, approach):
    if type(intent) is not bool:
        raise ValueError('Intent must be validated before a decision policy runs')
    if approach not in APPROACHES:
        raise ValueError('Unknown decision approach')
    record = {'case_id': request['case_id'], 'approach': approach, 'assumptions': [],
              'facts': [], 'unresolved_records': [], 'strict_error': None,
              'inferred_states': [],
              'decision_basis': None, 'row': None}
    try:
        strict = audit_request(request, subject, store, rules, intent, full_subject_audit=True)
    except (InsufficientEvidence, ValueError) as error:
        record['strict_error'] = str(error)
    else:
        record['row'] = strict
        record['decision_basis'] = ('interpreted_non_deletion_intent' if not intent else
                                    'observed_policy_violation' if strict['deletion_status'] == 'INCOMPLETE'
                                    else 'compliant_discovered_resources_with_primary_anchor')
    if intent and subject is not None:
        try:
            observations = select_states(subject, store, request['audit_at'])
        except (InsufficientEvidence, ValueError) as error:
            record['selection_error'] = str(error)
            observations = []
        record['facts'] = [fact(o) for o in observations if o.state != 'UNKNOWN']
        unknown = [o for o in observations if o.state == 'UNKNOWN']
        record['unresolved_records'] = [{**fact(o), 'reason': o.data.get('_uncertainty', 'Unknown treatment')}
                                        for o in unknown]
    else:
        observations, unknown = [], []
    if record['row'] is not None or approach == 'strict_auditor':
        return record
    if approach == 'conservative_fallback':
        # Deliberately expose the failure of a blanket conservative label under
        # this schema. Never invent a finding or resource to make it validate.
        record['row'] = {'case_id': request['case_id'], 'deletion_status': 'INCOMPLETE', 'steps_json': '[]'}
        record['decision_basis'] = 'fallback_prediction_without_demonstrated_violation'
        record['assumptions'] = [{'kind': 'missing_confirmation_implies_failure',
                                  'reason': 'Assume unresolved evidence means INCOMPLETE; not entailed by the specification'}]
        return record
    known = [o for o in observations if o.state != 'UNKNOWN']
    inferred = []
    for observation in unknown:
        # A forecast of potential restore risk is separate from a source-proven
        # current authorization setting. Require literal archive existence, not
        # a model guess that an archive might exist. Never alter the store.
        source = observation.data.get('_source_fact_record', {})
        if observation.category == 'BACKUP_ARCHIVE' and source.get('state') == 'PRESENT':
            assumption = {'kind': 'existing_archive_may_restore_without_confirmed_block',
                          'system_id': observation.system, 'resource_id': observation.resource,
                          'reason': 'Predict potential restore risk from attested archive existence; current subject-specific authorization remains unknown, so ACTIVE is inferred, not source-proven'}
            inferred.append(replace(observation, state='ACTIVE', data={**observation.data, '_prediction': assumption}))
            record['inferred_states'].append({**fact(observation), 'predicted_state': 'ACTIVE', 'assumption': assumption})
            record['assumptions'].append(assumption)
    try:
        # Missing or contradictory policy, temporal leakage and required
        # retention failures still stop this policy. No state is rewritten.
        row = plan_observations(request, subject, [*known, *inferred], rules, full_subject_audit=False)
    except (InsufficientEvidence, ValueError) as error:
        record['prediction_error'] = str(error)
        return record
    record['row'] = row
    record['decision_basis'] = ('decision_with_inferred_restore_risk' if inferred else
                               'observed_violation_with_partial_inventory' if row['deletion_status'] == 'INCOMPLETE'
                                else 'conditional_completeness_prediction')
    record['assumptions'].append({'kind': 'discovered_evidence_bounds_resource_inventory',
                                  'reason': 'Predict from eligible discovered states without requiring an additional primary-account anchor; missing proof is not a demonstrated violation'})
    for observation in unknown:
        if any(item.resource == observation.resource and item.system == observation.system for item in inferred):
            continue
        record['assumptions'].append({'kind': 'unknown_treatment_not_assumed_a_violation',
                                      'system_id': observation.system, 'resource_id': observation.resource,
                                      'reason': 'Omit an unknown state from factual verification; predicted completeness depends on this unresolved obligation being compliant'})
    validate_output([row], [request])
    return record
