import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence import EvidenceStore, hydrate_media, hydrate_media_reinspection, infer_state, parse_json, parse_log, parse_sql, retention_date_bounds, stored_identifiers
from audit_core import Observation


META = {"file_id": "evidence_test", "captured_at": "2026-09-10T12:00:00Z"}


def reviewed_record(**updates):
    record = {'resource_id': '', 'literal_reference': 'user_custom', 'reference_kind': 'STABLE_SUBJECT_REFERENCE',
              'category': 'account_reference', 'record_type': 'UNKNOWN', 'system_id': '',
              'source_system_label': 'Customer Reference Registry', 'state': 'PRESENT',
              'stable_reference': 'user_custom',
              'stored_fields': [{'field_name': 'user_id', 'value': 'user_custom', 'identifier_role': 'STABLE_REFERENCE', 'visibility': 'VALUE', 'source_quote': 'Customer key user_custom'}],
              'direct_identifiers_visible': [], 'context_identifiers': [], 'field_coverage': 'PARTIAL',
              'direct_fields_coverage': 'partial_view', 'observed_at': META['captured_at'],
              'time_basis': 'CAPTURE_TIME', 'observation_time_label': '', 'last_modified_at': '',
              'last_modified_label': '', 'last_modified_quote': '', 'events': [],
              'scope': {'kind': 'SINGLE_RECORD', 'label': 'Customer reference', 'completeness': 'PARTIAL', 'subject_bound': True, 'source_quote': 'Customer key user_custom'},
              'related_references': [], 'uncertainties': []}
    return {**record, **updates}


def reviewed_result(*records):
    return {'captured_at': META['captured_at'], 'source_summary': 'Reviewed business record',
            'records': list(records), 'uncertainties': [], 'review_complete': True}


CATALOG = [{'activity_id': 'activity_test', 'event_type': 'LINK_RESOURCE_IDENTITY',
            'event_time': '2026-09-10T12:01:00Z', 'source_system': 'data_catalog',
            'target_system': 'identity_service', 'resource_id': 'tombstone_custom',
            'details': 'Catalog linked tombstone_custom (user_custom) to user_custom.'}]


class EvidenceTests(unittest.TestCase):
    def test_quoted_technical_record_key_binds_business_view_alias(self):
        record = reviewed_record(resource_id='CS-99', literal_reference='CS-99', reference_kind='BUSINESS_ALIAS',
                                 category='record', record_type='SUPPORT_MESSAGE',
                                 related_references=[{'literal_reference': 'support_custom', 'relationship': 'Internal ticket reference',
                                                      'system_label': 'Support', 'source_quote': 'support_custom'}])
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'support_platform'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.resource, 'support_custom')
        self.assertEqual(observed.data['_source_resource_alias'], 'CS-99')

    def test_explicit_text_utc_retention_preserves_exact_time(self):
        from evidence import retention_timestamp
        self.assertEqual(retention_timestamp('25 Aug 2027 0403 UTC').isoformat(), '2027-08-25T04:03:00+00:00')
        with self.assertRaises(ValueError):
            retention_timestamp('25 Aug 2027 0403')
    def test_trace_lookup_key_is_joined_to_completion(self):
        text = '2026-09-10T10:00:00Z service=account_service trace_id=x event=profile_lookup_started lookup_key=OLD@EXAMPLE.ORG\n2026-09-10T10:00:01Z service=account_service trace_id=x event=profile_lookup_completed resource_id=account_x rows=0 http_status=404'
        records, _ = parse_log(text, META)
        self.assertEqual(records[-1].state, "ABSENT")
        self.assertIn("old@example.org", records[-1].identifiers)
        self.assertFalse(records[-1].eligible("2026-09-10T11:00:00Z"))

    def test_nested_json_anonymized_record_is_not_attributable(self):
        obj = {"snapshots": [{"captured_at": META["captured_at"], "data_store": "analytics_platform", "collection": "customer_analytics_reports", "records": [{"resource_id": "analytics_x", "user_id": None, "email": None, "phone": None, "email_hash": None}]}]}
        records, scopes = parse_json(obj, META)
        self.assertEqual(records[0].state, "ANONYMIZED")
        self.assertEqual(records[0].identifiers, set())
        self.assertTrue(scopes)

    def test_sql_primary_absence_preserves_replica_presence(self):
        sql = 'CREATE TABLE customer_profiles_primary(resource_id TEXT,user_id TEXT,email TEXT); CREATE TABLE customer_profiles_failover_replica(resource_id TEXT,user_id TEXT,email TEXT); INSERT INTO customer_profiles_failover_replica VALUES("account_x","user_x","old@example.org");'
        records, scopes = parse_sql(sql, META)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].state, "PRESENT")
        self.assertEqual(len(scopes), 2)
        self.assertNotEqual(scopes[0]["scope"], scopes[1]["scope"])

    def test_cache_miss_does_not_override_primary_lookup(self):
        text = '\n'.join([
            '2026-09-10T10:00:00Z service=account_service trace_id=x event=profile_lookup_started lookup_key=old@example.org',
            '2026-09-10T10:00:01Z service=account_service trace_id=x event=cache_lookup result=miss',
            '2026-09-10T10:00:02Z service=account_service trace_id=x event=profile_lookup_completed resource_id=account_x rows=1 http_status=200',
        ])
        records, _ = parse_log(text, META)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].state, 'PRESENT')
        self.assertIn('old@example.org', records[0].identifiers)

    def test_trace_subject_reference_does_not_reattribute_anonymized_payload(self):
        text = '\n'.join([
            '2026-09-10T10:00:00Z service=analytics_platform trace_id=x event=analytics_profile_scan_started subject_ref=user_custom',
            '2026-09-10T10:00:01Z service=analytics_platform trace_id=x event=analytics_profile_read resource_id=analytics_custom direct_identifiers=0 email=null phone=null',
        ])
        records, _ = parse_log(text, META)
        self.assertEqual(records[0].state, 'ANONYMIZED')
        self.assertIn('user_custom', records[0].identifiers)

    def test_pipe_trace_and_backup_denial_are_observations(self):
        text = '\n'.join([
            '2026-09-10T10:00:00Z | DEBUG | backup_service | trace-x | restore_policy_check_started | subject_key="user_x"',
            '2026-09-10T10:00:01Z | INFO | backup_service | trace-x | restore_authorization_completed | resource_id="backup_x" decision="deny"',
        ])
        records, _ = parse_log(text, META)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].state, 'BLOCKED')
        self.assertIn('user_x', records[0].identifiers)

    def test_lookup_metadata_does_not_make_anonymous_payload_identifiable(self):
        self.assertEqual(infer_state({'lookup_key': 'old@example.org', 'email': None, 'customer_reference': None}, 'ANALYTICS_PROFILE'), 'ANONYMIZED')
        self.assertEqual(infer_state({'query': 'old@example.org', 'requester_email': None}, 'SUPPORT_MESSAGE'), 'REDACTED')

    def test_compliance_labels_do_not_override_stored_pii(self):
        self.assertEqual(infer_state({'state': 'REDACTED', 'subject_reference': 'user_custom', 'email': 'person@example.test'}, 'ACCOUNT_TOMBSTONE'), 'PRESENT')
        self.assertEqual(infer_state({'result': 'ANONYMIZED', 'user_id': 'user_custom', 'email': 'person@example.test'}, 'ANALYTICS_PROFILE'), 'PRESENT')
        self.assertEqual(infer_state({'state': 'REDACTED', 'profile': {'email': 'person@example.test'}}, 'SUPPORT_MESSAGE'), 'PRESENT')

    def test_compliance_label_with_search_inputs_is_not_exposed_pii(self):
        context = {'lookup_key': 'person@example.test', 'query': 'person@example.test', 'correlation_key': 'user_custom'}
        self.assertEqual(infer_state({'state': 'REDACTED', **context}, 'ACCOUNT_TOMBSTONE'), 'REDACTED')
        self.assertEqual(infer_state({'state': 'ANONYMIZED', **context}, 'ANALYTICS_PROFILE'), 'ANONYMIZED')

    def test_actual_flow_and_restore_configuration_overrides_status_labels(self):
        self.assertEqual(infer_state({'state': 'DISABLED', 'enabled': True}, 'DATA_FLOW'), 'ACTIVE')
        self.assertEqual(infer_state({'state': 'ACTIVE', 'enabled': False}, 'DATA_FLOW'), 'DISABLED')
        self.assertEqual(infer_state({'state': 'BLOCKED', 'restore_allowed': True}, 'BACKUP_ARCHIVE'), 'ACTIVE')
        self.assertEqual(infer_state({'result': 'ACTIVE', 'restore_allowed': False}, 'BACKUP_ARCHIVE'), 'BLOCKED')
        self.assertEqual(infer_state({'decision': 'deny', 'restore_allowed': True}, 'BACKUP_ARCHIVE'), 'ACTIVE')

    def test_record_business_lifecycle_does_not_become_process_state(self):
        self.assertEqual(infer_state({'state': 'ACTIVE'}, 'USER_EXPORT'), 'PRESENT')
        self.assertEqual(infer_state({'result': 'ENABLED'}, 'MARKETING_PROFILE'), 'PRESENT')
        self.assertEqual(infer_state({'state': 'RESTORABLE'}, 'USER_PROFILE'), 'PRESENT')
        self.assertEqual(infer_state({'state': 'ACTIVE'}, 'DATA_FLOW'), 'ACTIVE')
        self.assertEqual(infer_state({'state': 'RESTORABLE'}, 'BACKUP_ARCHIVE'), 'ACTIVE')

    def test_empty_snapshot_keeps_category_and_capture_scope(self):
        obj = {'snapshots': [{'captured_at': '2026-09-10T10:00:00Z', 'data_store': 'account_service', 'collection': 'customer_profiles', 'complete': True, 'records': []}]}
        records, scopes = parse_json(obj, META)
        self.assertEqual(records, [])
        self.assertEqual(scopes[0]['resources'], set())
        self.assertEqual(scopes[0]['category'], 'USER_PROFILE')
        self.assertEqual(scopes[0]['observed_at'], '2026-09-10T10:00:00Z')
        self.assertTrue(scopes[0]['complete'])

    def test_snapshot_wrapper_without_explicit_coverage_is_not_exhaustive(self):
        obj = {'snapshots': [{'captured_at': '2026-09-10T10:00:00Z', 'data_store': 'account_service', 'collection': 'customer_profiles_subset', 'records': []}]}
        records, scopes = parse_json(obj, META)
        self.assertEqual(records, [])
        self.assertEqual(len(scopes), 1)
        self.assertFalse(scopes[0]['complete'])

    def test_snapshot_explicit_exhaustive_declaration_is_preserved(self):
        obj = {'data_store': 'account_service', 'collection': 'customer_profiles', 'exhaustive': True, 'records': []}
        _, scopes = parse_json(obj, META)
        self.assertTrue(scopes[0]['complete'])

    def test_unlisted_inventory_system_is_not_authoritative_absence(self):
        sql = 'CREATE TABLE snapshot_scope(origin_system TEXT,captured_at TEXT); INSERT INTO snapshot_scope VALUES("account_service","2026-09-10T10:00:00Z"); CREATE TABLE customer_profiles(resource_id TEXT); CREATE TABLE customer_exports(resource_id TEXT);'
        records, scopes = parse_sql(sql, META)
        self.assertEqual(records, [])
        self.assertEqual([s['system'] for s in scopes], ['account_service'])
        self.assertEqual(scopes[0]['observed_at'], '2026-09-10T10:00:00Z')

    def test_generic_replica_empty_category_has_scope(self):
        sql = '''CREATE TABLE customer_data_primary(resource_id TEXT,origin_system TEXT,collection_name TEXT,record_json TEXT);
        CREATE TABLE customer_data_read_replica(resource_id TEXT,origin_system TEXT,collection_name TEXT,record_json TEXT);
        INSERT INTO customer_data_read_replica VALUES('search_x','search_service','search_documents','{"resource_id":"search_x","email":"old@example.org"}');'''
        records, scopes = parse_sql(sql, META)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(scopes), 2)
        primary = next(s for s in scopes if s['scope'] == 'customer_data_primary')
        self.assertEqual(primary['resources'], set())

    def test_media_hydration_keeps_explicit_provenance(self):
        store = EvidenceStore()
        result = {'records': [{'system_id': 'identity_service', 'resource_id': 'tombstone_custom', 'record_type': 'ACCOUNT_TOMBSTONE', 'observed_at': '2026-09-10T10:00:00Z', 'state': 'REDACTED', 'identifiers': ['user_custom'], 'notes': 'Only stable reference remains.'}]}
        hydrated = hydrate_media(store, META, result)
        self.assertEqual(hydrated[0].resource, 'tombstone_custom')
        self.assertEqual(hydrated[0].identifiers, {'user_custom'})
        self.assertEqual(store.by_resource['tombstone_custom'][0].evidence_id, 'evidence_test')
        self.assertEqual(hydrated[0].captured_at, META['captured_at'])

    def test_media_hydration_rejects_unknown_categories_and_timestamps(self):
        result = {'records': [{'system_id': 'identity_service', 'resource_id': 'custom', 'record_type': 'INVENTED', 'observed_at': 'yesterday', 'state': 'PRESENT', 'identifiers': [], 'notes': ''}]}
        with self.assertRaises(ValueError):
            hydrate_media(EvidenceStore(), META, result)

    def test_media_friendly_service_title_uses_grounded_resource_system(self):
        record = {'system_id': 'Customer Operations', 'resource_id': 'account_custom', 'record_type': 'USER_PROFILE', 'observed_at': '2026-09-10T10:00:00Z', 'state': 'PRESENT', 'identifiers': ['user_custom'], 'notes': 'Profile exists.'}
        observations = hydrate_media(EvidenceStore(), META, {'records': [record]})
        self.assertEqual(observations[0].system, 'account_service')
        self.assertEqual(observations[0].data['source_system_title'], 'Customer Operations')

    def test_media_friendly_service_title_with_conflicting_category_fails(self):
        record = {'system_id': 'Customer Operations', 'resource_id': 'account_custom', 'record_type': 'SEARCH_INDEX_ENTRY', 'observed_at': '2026-09-10T10:00:00Z', 'state': 'PRESENT', 'identifiers': [], 'notes': ''}
        with self.assertRaises(ValueError):
            hydrate_media(EvidenceStore(), META, {'records': [record]})

    def test_media_single_word_brand_uses_canonical_service(self):
        record = {'system_id': 'BridgeOps', 'resource_id': 'data_flow_custom', 'record_type': 'DATA_FLOW', 'observed_at': '2026-09-10T10:00:00Z', 'state': 'ACTIVE', 'identifiers': ['user_custom'], 'notes': ''}
        observation = hydrate_media(EvidenceStore(), META, {'records': [record]})[0]
        self.assertEqual(observation.system, 'integration_service')
        self.assertEqual(observation.data['source_system_title'], 'BridgeOps')

    def test_media_manifest_origin_precedes_brand_category_fallback(self):
        record = {'system_id': 'Nimbus Object Storage', 'resource_id': 'delivery_custom.pdf', 'record_type': 'SUPPORT_ATTACHMENT', 'observed_at': '2026-09-10T10:00:00Z', 'state': 'PRESENT', 'identifiers': [], 'notes': ''}
        observation = hydrate_media(EvidenceStore(), {**META, 'origin': 'object_storage'}, {'records': [record]})[0]
        self.assertEqual(observation.system, 'object_storage')
        self.assertEqual(observation.data['_manifest_origin'], 'object_storage')

    def test_known_explicit_service_is_not_replaced_by_manifest_origin(self):
        record = {'system_id': 'object_storage', 'resource_id': 'delivery_custom.pdf', 'record_type': 'SUPPORT_ATTACHMENT', 'observed_at': '2026-09-10T10:00:00Z', 'state': 'PRESENT', 'identifiers': [], 'notes': ''}
        observation = hydrate_media(EvidenceStore(), {**META, 'origin': 'support_platform'}, {'records': [record]})[0]
        self.assertEqual(observation.system, 'object_storage')

    def test_media_record_active_business_state_is_present(self):
        record = {'system_id': 'marketing_platform', 'resource_id': 'marketing_custom', 'record_type': 'MARKETING_PROFILE', 'observed_at': '2026-09-10T10:00:00Z', 'state': 'ACTIVE', 'identifiers': ['user_custom'], 'notes': 'Active marketing audience membership.'}
        observation = hydrate_media(EvidenceStore(), META, {'records': [record]})[0]
        self.assertEqual(observation.state, 'PRESENT')
        self.assertEqual(observation.data['state'], 'ACTIVE')

    def test_stored_identifiers_exclude_query_only_tombstone_context(self):
        record = {'state': 'REDACTED', 'lookup_key': 'user_custom', 'query': 'user_custom', 'subject_selector': 'user_custom', 'email': None, 'subject_reference': None}
        self.assertEqual(stored_identifiers(record), set())
        self.assertEqual(stored_identifiers({**record, 'subject_reference': 'user_custom'}), {'user_custom'})

    def test_stored_identifiers_do_not_include_joined_trace_context(self):
        text = '\n'.join([
            '2026-09-10T10:00:00Z service=identity_service trace_id=x event=tombstone_read_started subject_ref=user_custom',
            '2026-09-10T10:00:01Z service=identity_service trace_id=x event=tombstone_read_completed resource_id=tombstone_custom result=REDACTED',
        ])
        records, _ = parse_log(text, META)
        self.assertIn('user_custom', records[0].identifiers)
        self.assertEqual(stored_identifiers(records[0].data), set())

    def test_stored_identifiers_accept_explicit_media_record_identifiers(self):
        self.assertEqual(stored_identifiers({'_media': True, 'identifiers': ['user_custom'], 'notes': 'query user_other'}), {'user_custom'})

    def test_review_stable_reference_alone_is_unknown_not_exposed_pii(self):
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'identity_service'}, reviewed_result(reviewed_record()), CATALOG)[0]
        self.assertEqual(observed.resource, 'tombstone_custom')
        self.assertEqual(observed.category, 'ACCOUNT_TOMBSTONE')
        self.assertEqual(observed.state, 'UNKNOWN')
        self.assertEqual(stored_identifiers(observed.data), {'user_custom'})
        self.assertIn('not redaction proof', observed.data['_uncertainty'])
        self.assertEqual(observed.data['_catalog_event_time'], CATALOG[0]['event_time'])
        self.assertFalse(observed.eligible('2026-09-10T12:00:30Z'))

    def test_review_visible_stored_email_establishes_exposure(self):
        record = reviewed_record()
        field = {'field_name': 'email', 'value': 'person@example.test', 'identifier_role': 'DIRECT_IDENTIFIER', 'visibility': 'VALUE', 'source_quote': 'Email person@example.test'}
        record['stored_fields'].append(field)
        record['direct_identifiers_visible'] = [{k: field[k] for k in ('field_name', 'value', 'source_quote')}]
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'identity_service'}, reviewed_result(record), CATALOG)[0]
        self.assertEqual(observed.state, 'PRESENT')

    def test_review_complete_explicit_empty_direct_fields_preserve_reference(self):
        record = reviewed_record(field_coverage='COMPLETE', direct_fields_coverage='explicitly_redacted')
        record['stored_fields'].extend({'field_name': key, 'value': '', 'identifier_role': 'DIRECT_IDENTIFIER', 'visibility': 'BLANK', 'source_quote': key + ': empty'} for key in ('name', 'email', 'phone', 'email_hash'))
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'identity_service'}, reviewed_result(record), CATALOG)[0]
        self.assertEqual(observed.state, 'REDACTED')

    def test_review_context_query_does_not_prove_stored_stable_reference(self):
        record = reviewed_record(stored_fields=[], context_identifiers=[{'field_name': 'query', 'value': 'user_custom', 'source_quote': 'Search user_custom'}])
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'identity_service'}, reviewed_result(record), CATALOG)[0]
        self.assertEqual(observed.state, 'UNKNOWN')
        self.assertEqual(stored_identifiers(observed.data), set())
        self.assertIn('user_custom', observed.identifiers)

    def test_review_update_clock_is_event_not_observation_time(self):
        later = '2026-09-10T13:18:00Z'
        record = reviewed_record(last_modified_at=later, last_modified_label='Most recent update', last_modified_quote='Most recent update 13:18 UTC',
                                 events=[{'kind': 'MODIFIED', 'timestamp': later, 'raw': '13:18 UTC', 'source_quote': 'Most recent update 13:18 UTC'}])
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'identity_service'}, reviewed_result(record), CATALOG)[0]
        self.assertEqual(observed.observed_at, META['captured_at'])
        self.assertEqual(observed.captured_at, META['captured_at'])
        self.assertEqual(observed.data['last_modified_at'], later)
        self.assertIn('later than manifest capture', observed.data['_uncertainty'])
        self.assertEqual(observed.state, 'UNKNOWN')

    def test_review_explicit_future_snapshot_remains_ineligible(self):
        later = '2026-09-11T13:18:00Z'
        record = reviewed_record(observed_at=later, time_basis='EXPLICIT_SNAPSHOT_TIME', observation_time_label='Snapshot as of')
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'identity_service'}, reviewed_result(record), CATALOG)[0]
        self.assertFalse(observed.eligible('2026-09-10T23:59:00Z'))
        self.assertEqual(observed.observed_at, later)

    def test_review_replaces_matching_primary_and_link_pseudorows_only(self):
        primary = Observation('account_service', 'user_custom', 'USER_PROFILE', 'PRESENT', META['file_id'], META['captured_at'], META['captured_at'], {'user_custom'}, {'_media': True})
        linked = Observation('export_service', 'ORDER-9', 'USER_EXPORT', 'PRESENT', META['file_id'], META['captured_at'], META['captured_at'], {'user_custom'}, {'_media': True})
        unrelated = Observation('account_service', 'account_other', 'USER_PROFILE', 'PRESENT', META['file_id'], META['captured_at'], META['captured_at'], {'user_other'}, {'_media': True})
        other_file = Observation('export_service', 'ORDER-9', 'USER_EXPORT', 'PRESENT', 'other_file', META['captured_at'], META['captured_at'], {'user_other'}, {'_media': True})
        store = EvidenceStore([primary, linked, unrelated, other_file])
        link = reviewed_record(resource_id='ORDER-9', literal_reference='ORDER-9', reference_kind='BUSINESS_ALIAS', category='linked_reference', stable_reference='', stored_fields=[], record_type='UNKNOWN', state='UNKNOWN')
        hydrate_media_reinspection(store, {**META, 'origin': 'identity_service'}, reviewed_result(reviewed_record(), link), CATALOG)
        self.assertIn(unrelated, store.observations)
        self.assertIn(other_file, store.observations)
        self.assertNotIn(primary, store.observations)
        self.assertNotIn(linked, store.observations)
        self.assertEqual(len(store.observations), 3)
        self.assertEqual(len(store.media_reinspection_facts[META['file_id']]['superseded_rows']), 2)

    def test_review_nested_related_references_supersede_same_file_pseudorows(self):
        primary = Observation('account_service', 'user_custom', 'USER_PROFILE', 'PRESENT', META['file_id'], META['captured_at'], META['captured_at'], {'user_custom'}, {'_media': True})
        pseudo = Observation('export_service', 'ORDER-9', 'USER_EXPORT', 'PRESENT', META['file_id'], META['captured_at'], META['captured_at'], {'user_custom'}, {'_media': True})
        unrelated = Observation('account_service', 'account_other', 'USER_PROFILE', 'PRESENT', META['file_id'], META['captured_at'], META['captured_at'], {'user_other'}, {'_media': True})
        other_file = Observation('export_service', 'ORDER-9', 'USER_EXPORT', 'PRESENT', 'other_file', META['captured_at'], META['captured_at'], {'user_other'}, {'_media': True})
        store = EvidenceStore([primary, pseudo, unrelated, other_file])
        record = reviewed_record(related_references=[{'literal_reference': 'ORDER-9', 'relationship': 'Linked to customer', 'system_label': 'Orders', 'source_quote': 'Orders ORDER-9 Linked to customer'}])
        hydrate_media_reinspection(store, {**META, 'origin': 'identity_service'}, reviewed_result(record), CATALOG)
        self.assertNotIn(pseudo, store.observations)
        self.assertIn(unrelated, store.observations)
        self.assertIn(other_file, store.observations)
        self.assertEqual(len(store.observations), 3)
        audit = store.media_reinspection_facts[META['file_id']]['superseded_rows']
        self.assertTrue(any(row['literal_reference'] == 'ORDER-9' and row['role'] == 'linked_reference' for row in audit))

    def test_review_nested_reference_cannot_erase_separately_reviewed_contents(self):
        actual = Observation('support_platform', 'support_custom', 'SUPPORT_MESSAGE', 'PRESENT', META['file_id'], META['captured_at'], META['captured_at'], {'user_custom'}, {'_media': True, '_media_reinspection': True})
        store = EvidenceStore([actual])
        record = reviewed_record(related_references=[{'literal_reference': 'support_custom', 'relationship': 'Related support record', 'system_label': 'Support', 'source_quote': 'Support support_custom'}])
        hydrate_media_reinspection(store, {**META, 'origin': 'identity_service'}, reviewed_result(record), CATALOG)
        self.assertIn(actual, store.observations)

    def test_review_new_primary_contents_survive_a_nested_reference(self):
        pseudo = Observation('export_service', 'ORDER-9', 'USER_EXPORT', 'PRESENT', META['file_id'], META['captured_at'], META['captured_at'], {'user_custom'}, {'_media': True})
        store = EvidenceStore([pseudo])
        parent = reviewed_record(related_references=[{'literal_reference': 'ORDER-9', 'relationship': 'Linked to customer', 'system_label': 'Orders', 'source_quote': 'Orders ORDER-9'}])
        actual = reviewed_record(resource_id='ORDER-9', literal_reference='ORDER-9', reference_kind='BUSINESS_ALIAS', category='record', record_type='LEGAL_HOLD_RECORD')
        hydrated = hydrate_media_reinspection(store, {**META, 'origin': 'identity_service'}, reviewed_result(parent, actual), CATALOG)
        self.assertNotIn(pseudo, store.observations)
        self.assertTrue(any(o.resource == 'ORDER-9' and o.category == 'LEGAL_HOLD_RECORD' for o in hydrated))

    def test_review_stable_reference_is_still_analytics_attribution(self):
        record = reviewed_record(resource_id='analytics_custom', literal_reference='analytics_custom', reference_kind='RESOURCE_ID', category='record', record_type='ANALYTICS_PROFILE')
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'analytics_platform'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.state, 'PRESENT')

    def test_review_producing_portal_is_not_a_distinct_profile_service(self):
        record = reviewed_record(resource_id='account_custom', literal_reference='account_custom', reference_kind='RESOURCE_ID', category='record', record_type='USER_PROFILE', source_system_label='Customer Operations')
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'account_admin_portal'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.system, 'account_service')
        self.assertEqual(observed.data['_manifest_origin'], 'account_admin_portal')
        self.assertEqual(observed.data['source_system_label'], 'Customer Operations')

    def test_review_unknown_process_brand_is_normalized(self):
        record = reviewed_record(resource_id='data_flow_custom', literal_reference='data_flow_custom', reference_kind='RESOURCE_ID', category='process', record_type='DATA_FLOW', system_id='BridgeOps', source_system_label='BridgeOps', state='ACTIVE')
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'connector_admin'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.system, 'integration_service')
        self.assertEqual(observed.data['source_system_title'], 'BridgeOps')

    def test_review_retention_metadata_remains_available_to_policy(self):
        record = reviewed_record(resource_id='audit_record_custom', literal_reference='audit_record_custom', reference_kind='RESOURCE_ID', category='record', record_type='SECURITY_AUDIT_LOG')
        record['stored_fields'].append({'field_name': 'retention_until', 'value': '2033-05-04T23:59:59Z', 'identifier_role': 'OTHER', 'visibility': 'VALUE', 'source_quote': 'Retain until 2033-05-04T23:59:59Z'})
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'security_retention_service'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.system, 'security_service')
        self.assertEqual(observed.data['retention_until'], '2033-05-04T23:59:59Z')
        self.assertEqual(observed.data['_source_fact_record']['stored_fields'], record['stored_fields'])

    def test_review_partial_retention_date_is_not_repaired_into_a_timestamp(self):
        record = reviewed_record(resource_id='audit_record_custom', literal_reference='audit_record_custom', reference_kind='RESOURCE_ID', category='record', record_type='SECURITY_AUDIT_LOG')
        record['stored_fields'].append({'field_name': 'retention_until', 'value': '2033', 'identifier_role': 'OTHER', 'visibility': 'VALUE', 'source_quote': 'Retain until 2033'})
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'security_retention_service'}, reviewed_result(record), [])[0]
        self.assertNotIn('retention_until', observed.data)
        self.assertEqual(observed.data['retention_until_raw'], '2033')
        self.assertEqual(observed.state, 'UNKNOWN')

    def test_retention_date_only_parser_preserves_bounded_precision(self):
        bounds = retention_date_bounds('04 May 2033')
        self.assertEqual(bounds, retention_date_bounds('2033-05-04'))
        self.assertEqual(bounds['date'], '2033-05-04')
        self.assertEqual(bounds['lower'], '2033-05-03T10:00:00Z')
        self.assertEqual(bounds['upper'], '2033-05-05T11:59:59.999999Z')
        self.assertIsNone(retention_date_bounds('31 Feb 2033'))
        self.assertIsNone(retention_date_bounds('2033'))

    def test_review_future_date_only_retention_is_not_unknown(self):
        record = reviewed_record(resource_id='audit_record_custom', literal_reference='audit_record_custom', reference_kind='RESOURCE_ID', category='record', record_type='SECURITY_AUDIT_LOG')
        record['stored_fields'].append({'field_name': 'retention_until', 'value': '04 May 2033', 'identifier_role': 'OTHER', 'visibility': 'VALUE', 'source_quote': 'Retain until 04 May 2033'})
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'security_service'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.state, 'PRESENT')
        self.assertNotIn('retention_until', observed.data)
        self.assertEqual(observed.data['retention_until_raw'], '04 May 2033')
        self.assertEqual(observed.data['retention_until_date'], '2033-05-04')
        self.assertEqual(observed.data['retention_until_bounds']['lower'], '2033-05-03T10:00:00Z')
        from reasoning import _policy
        self.assertEqual(_policy(observed, [{'data_category': 'SECURITY_AUDIT_LOG', 'required_action': 'RETAIN'}], '2026-09-10T12:00:00Z'), 'RETAIN')

    def test_date_only_retention_boundary_and_expiry_never_authorize_delete(self):
        from reasoning import InsufficientEvidence, _policy
        observed = Observation('security_service', 'audit_record_custom', 'SECURITY_AUDIT_LOG', 'PRESENT', META['file_id'], META['captured_at'], META['captured_at'], {'user_custom'},
                               {'retention_until_raw': '04 May 2033', 'retention_until_bounds': {'lower': '2033-05-03T10:00:00Z', 'upper': '2033-05-05T11:59:59.999999Z'}})
        rules = [{'data_category': 'SECURITY_AUDIT_LOG', 'required_action': 'RETAIN'}]
        with self.assertRaises(InsufficientEvidence):
            _policy(observed, rules, '2033-05-04T12:00:00Z')
        with self.assertRaises(InsufficientEvidence):
            _policy(observed, rules, '2033-05-07T12:00:00Z')

    def test_review_partial_support_view_is_not_exposed_pii_proof(self):
        record = reviewed_record(resource_id='support_custom', literal_reference='support_custom', reference_kind='RESOURCE_ID', category='record', record_type='SUPPORT_MESSAGE')
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'support_platform'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.state, 'UNKNOWN')
        self.assertIn('exposed PII', observed.data['_uncertainty'])

    def test_review_filtered_collection_cannot_prove_record_absence(self):
        record = reviewed_record(resource_id='account_custom', literal_reference='account_custom', reference_kind='RESOURCE_ID', category='record', record_type='USER_PROFILE', state='ABSENT')
        record['scope'] = {'kind': 'FILTERED_RESULTS', 'label': 'Recent customers', 'completeness': 'PARTIAL', 'subject_bound': False, 'source_quote': 'Recent customers'}
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'account_service'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.state, 'UNKNOWN')

    def test_review_archive_existence_does_not_prove_current_restore_risk(self):
        record = reviewed_record(resource_id='backup_custom', literal_reference='backup_custom', reference_kind='RESOURCE_ID', category='record', record_type='BACKUP_ARCHIVE', state='PRESENT')
        record['stored_fields'].append({'field_name': 'checksum', 'value': 'healthy', 'identifier_role': 'OTHER', 'visibility': 'VALUE', 'source_quote': 'Checksum verified; archive healthy'})
        store = EvidenceStore()
        observed = hydrate_media_reinspection(store, {**META, 'origin': 'backup_service'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.state, 'UNKNOWN')
        self.assertIn('current restore authorization', observed.data['_uncertainty'])
        from audit_core import Subject
        from reasoning import InsufficientEvidence, audit_request
        with self.assertRaises(InsufficientEvidence):
            audit_request({'case_id': 'synthetic_archive', 'audit_at': '2026-09-11T12:00:00Z'}, Subject('user_custom', {'user_custom'}), store,
                          [{'data_category': 'BACKUP_ARCHIVE', 'required_action': 'RETAIN'}], True)

    def test_review_connector_existence_does_not_prove_enabled_status(self):
        record = reviewed_record(resource_id='data_flow_custom', literal_reference='data_flow_custom', reference_kind='RESOURCE_ID', category='process', record_type='DATA_FLOW', state='PRESENT')
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'integration_service'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.state, 'UNKNOWN')
        self.assertIn('current enabled/disabled', observed.data['_uncertainty'])

    def test_review_explicit_restore_authorization_still_establishes_state(self):
        record = reviewed_record(resource_id='backup_custom', literal_reference='backup_custom', reference_kind='RESOURCE_ID', category='record', record_type='BACKUP_ARCHIVE', state='PRESENT')
        record['stored_fields'].append({'field_name': 'Restore allowed', 'value': 'false', 'identifier_role': 'OTHER', 'visibility': 'VALUE', 'source_quote': 'Restore allowed: false'})
        observed = hydrate_media_reinspection(EvidenceStore(), {**META, 'origin': 'backup_service'}, reviewed_result(record), [])[0]
        self.assertEqual(observed.state, 'BLOCKED')


if __name__ == "__main__":
    unittest.main()
