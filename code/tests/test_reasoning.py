import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import Observation, Subject, norm, validate_output
from evidence import EvidenceStore, hydrate_media, identifiers
from reasoning import audit_request, InsufficientEvidence, _canonical_view, related_resources


NOW = "2026-09-10T12:00:00Z"
BEFORE = "2026-09-09T12:00:00Z"
AFTER = "2026-09-11T12:00:00Z"
REQUEST = {"case_id": "synthetic", "audit_at": NOW}
SUBJECT = Subject("subject", {"subject", "old@example.org"})
RULES = [{"data_category": category, "required_action": action} for category, action in
         [("USER_PROFILE", "DELETE"), ("SUPPORT_MESSAGE", "REDACT"), ("ANALYTICS_PROFILE", "ANONYMIZE"),
          ("ACCOUNT_TOMBSTONE", "REDACT"), ("BACKUP_ARCHIVE", "RETAIN"), ("SECURITY_AUDIT_LOG", "RETAIN")]]


def observation(resource="account_a", category="USER_PROFILE", state="PRESENT", when=BEFORE,
                captured=BEFORE, scope="", ids=None, system="account_service", **data):
    return Observation(system, resource, category, state, "fixture", captured, when,
                       {"old@example.org"} if ids is None else ids, data, scope)


class ReasoningTests(unittest.TestCase):
    def test_owned_known_key_absent_from_first_complete_snapshot(self):
        event = {"event_type": "LINK_RESOURCE_IDENTITY", "event_time": BEFORE, "details": "Linked subject to account_a", "resource_id": "account_a", "target_system": "account_service"}
        scope = {"system": "account_service", "category": "USER_PROFILE", "scope": "customer_profiles", "resources": set(), "captured_at": NOW, "observed_at": NOW, "evidence_id": "snapshot", "complete": True}
        row = audit_request(REQUEST, SUBJECT, EvidenceStore([], [scope], [event]), RULES, True, full_subject_audit=True)
        step = json.loads(row["steps_json"])[0]
        self.assertEqual((row["deletion_status"], step["resource_id"], step["evidence_id"]), ("COMPLETE", "account_a", "snapshot"))

    def test_unknown_owned_key_cannot_be_invented_from_negative_snapshot(self):
        scope = {"system": "account_service", "category": "USER_PROFILE", "scope": "customer_profiles", "resources": set(), "captured_at": NOW, "observed_at": NOW, "evidence_id": "snapshot", "complete": True}
        with self.assertRaises(InsufficientEvidence):
            audit_request(REQUEST, SUBJECT, EvidenceStore([], [scope], []), RULES, True, full_subject_audit=True)

    def test_known_key_absence_requires_eligible_complete_snapshot(self):
        event = {"event_type": "LINK_RESOURCE_IDENTITY", "event_time": BEFORE, "details": "Linked subject to account_a", "resource_id": "account_a", "target_system": "account_service"}
        base = {"system": "account_service", "category": "USER_PROFILE", "scope": "customer_profiles", "resources": set(), "captured_at": NOW, "observed_at": NOW, "evidence_id": "snapshot", "complete": True}
        for scope in ({**base, "complete": False}, {**base, "captured_at": AFTER}, {**base, "resources": {"account_a"}}):
            with self.subTest(scope=scope), self.assertRaises(InsufficientEvidence):
                audit_request(REQUEST, SUBJECT, EvidenceStore([], [scope], [event]), RULES, True, full_subject_audit=True)

    def test_negative_primary_does_not_hide_an_unparsed_listed_replica(self):
        event = {"event_type": "LINK_RESOURCE_IDENTITY", "event_time": BEFORE, "details": "Linked subject to account_a", "resource_id": "account_a", "target_system": "account_service"}
        scope = {"system": "account_service", "category": "USER_PROFILE", "scope": "profiles_primary", "resources": set(), "captured_at": NOW, "observed_at": NOW, "evidence_id": "snapshot", "complete": True}
        replica = {**scope, "scope": "profiles_replica", "resources": {"account_a"}}
        with self.assertRaisesRegex(InsufficientEvidence, "without parsed state"):
            audit_request(REQUEST, SUBJECT, EvidenceStore([], [scope, replica], [event]), RULES, True, full_subject_audit=True)

    def test_parsed_primary_does_not_hide_an_unparsed_listed_replica(self):
        primary = observation(state="ABSENT", scope="profiles_primary")
        replica = {"system": "account_service", "category": "USER_PROFILE", "scope": "profiles_replica", "resources": {"account_a"}, "captured_at": NOW, "observed_at": NOW, "evidence_id": "snapshot", "complete": True}
        with self.assertRaisesRegex(InsufficientEvidence, "without parsed state"):
            audit_request(REQUEST, SUBJECT, EvidenceStore([primary], [replica]), RULES, True, full_subject_audit=True)

    def test_full_subject_audit_cannot_complete_from_retention_alone(self):
        audit = observation("audit", "SECURITY_AUDIT_LOG", "PRESENT", system="security_service")
        with self.assertRaisesRegex(InsufficientEvidence, "deleted primary account"):
            audit_request(REQUEST, SUBJECT, EvidenceStore([audit]), RULES, True, full_subject_audit=True)

    def test_replica_only_absence_cannot_complete_full_subject_audit(self):
        replica = observation(state="ABSENT", scope="profiles_replica")
        with self.assertRaisesRegex(InsufficientEvidence, "deleted primary account"):
            audit_request(REQUEST, SUBJECT, EvidenceStore([replica]), RULES, True, full_subject_audit=True)

    def run_case(self, obs, intent=True, activities=None, scopes=None):
        row = audit_request(REQUEST, SUBJECT, EvidenceStore(obs, scopes, activities), RULES, intent)
        validate_output([row], [REQUEST])
        return row, json.loads(row["steps_json"])

    def test_export_only_has_no_destructive_or_verification_steps(self):
        row, steps = self.run_case([], False)
        self.assertEqual((row["deletion_status"], steps), ("NOT_APPLICABLE", []))

    def test_primary_absence_does_not_erase_historical_email_replica(self):
        row, steps = self.run_case([observation(state="ABSENT", when=NOW),
                                   observation(scope="customer_profiles_replica")])
        self.assertEqual(row["deletion_status"], "INCOMPLETE")
        self.assertEqual(steps[0]["operation"], "REPORT_REMAINING_RECORD")

    def test_later_deletion_cannot_change_prior_audit(self):
        row, _ = self.run_case([observation(), observation(state="ABSENT", when=AFTER, captured=AFTER)])
        self.assertEqual(row["deletion_status"], "INCOMPLETE")

    def test_future_capture_cannot_establish_past_state(self):
        with self.assertRaises(InsufficientEvidence):
            self.run_case([observation(captured=AFTER)])

    def test_active_sync_is_stopped_before_record_changes(self):
        row, steps = self.run_case([observation(), observation("flow", "DATA_FLOW", "ACTIVE", system="integration_service")])
        remediation = [s["operation"] for s in steps if s["phase"] == "REMEDIATION"]
        self.assertEqual(remediation, ["DISABLE_DATA_FLOW", "DELETE_RECORD"])

    def test_retained_backup_with_restore_blocked_is_complete(self):
        row, steps = self.run_case([observation("backup", "BACKUP_ARCHIVE", "BLOCKED", system="backup_service")])
        self.assertEqual(row["deletion_status"], "COMPLETE")
        self.assertEqual(steps[0]["operation"], "VERIFY_RESTORE_BLOCKED")

    def test_future_date_only_retention_does_not_need_invented_timezone(self):
        bounds = {"lower": "2033-05-03T10:00:00Z", "upper": "2033-05-05T11:59:59.999999Z"}
        row, steps = self.run_case([observation("audit", "SECURITY_AUDIT_LOG", "PRESENT", system="security_service", retention_until_bounds=bounds)])
        self.assertEqual(row["deletion_status"], "COMPLETE")
        self.assertEqual(steps[0]["operation"], "VERIFY_RECORD_PRESENT")

    def test_date_only_retention_boundary_and_expiry_are_uncertain_not_deleted(self):
        for bounds, message in [({"lower": BEFORE, "upper": AFTER}, "boundary"),
                                ({"lower": "2026-01-01T00:00:00Z", "upper": "2026-01-03T00:00:00Z"}, "Expired")]:
            with self.subTest(bounds=bounds), self.assertRaisesRegex(InsufficientEvidence, message):
                self.run_case([observation("audit", "SECURITY_AUDIT_LOG", "PRESENT", system="security_service", retention_until_bounds=bounds)])

    def test_archive_presence_alone_is_not_restore_permission(self):
        with self.assertRaisesRegex(InsufficientEvidence, "Archive existence"):
            self.run_case([observation("backup", "BACKUP_ARCHIVE", "PRESENT", system="backup_service")])

    def test_compliant_tombstone_preserves_internal_reference(self):
        row, steps = self.run_case([observation("tombstone", "ACCOUNT_TOMBSTONE", "REDACTED", ids={"subject"}, system="identity_service", subject_reference="subject")])
        self.assertEqual(row["deletion_status"], "COMPLETE")
        self.assertEqual(steps[0]["operation"], "VERIFY_RECORD_REDACTED")

    def test_workflow_success_alone_is_not_proof(self):
        event = {"event_time": BEFORE, "details": "Deletion for old@example.org", "resource_id": "account_a", "target_system": "account_service", "reported_result": "SUCCESS"}
        with self.assertRaises(InsufficientEvidence):
            self.run_case([], activities=[event])

    def test_catalog_link_restores_anonymized_record_ownership(self):
        event = {"event_time": BEFORE, "details": "Linked subject to analytics_a", "resource_id": "analytics_a", "target_system": "analytics_platform"}
        row, steps = self.run_case([observation("analytics_a", "ANALYTICS_PROFILE", "ANONYMIZED", ids=set(), system="analytics_platform")], activities=[event])
        self.assertEqual(row["deletion_status"], "COMPLETE")
        self.assertEqual(steps[0]["operation"], "VERIFY_RECORD_ANONYMIZED")

    def test_generic_missing_snapshot_row_cannot_prove_absence(self):
        scope = {"system": "account_service", "category": "USER_PROFILE", "scope": "profile_list", "resources": set(), "captured_at": NOW, "observed_at": NOW, "evidence_id": "snapshot"}
        row, _ = self.run_case([observation()], scopes=[scope])
        self.assertEqual(row["deletion_status"], "INCOMPLETE")

    def test_unrelated_subject_with_similar_user_id_does_not_join(self):
        with self.assertRaises(InsufficientEvidence):
            self.run_case([observation(ids={"another"})])

    def test_explicit_resource_link_finds_identifier_free_export(self):
        rules = RULES + [{"data_category": "USER_EXPORT", "required_action": "DELETE"}]
        export = observation("export_a", "USER_EXPORT", "PRESENT", ids=set(), system="export_service", source_resource_id="account_a")
        row = audit_request(REQUEST, SUBJECT, EvidenceStore([observation(state="ABSENT"), export]), rules, True)
        self.assertEqual(row["deletion_status"], "INCOMPLETE")
        self.assertTrue(any(s["resource_id"] == "export_a" and s["phase"] == "FINDING" for s in json.loads(row["steps_json"])))

    def test_complete_different_collection_cannot_erase_known_row(self):
        scope = {"system": "account_service", "category": "USER_PROFILE", "scope": "customer_profiles_subset", "resources": set(), "captured_at": NOW, "observed_at": NOW, "evidence_id": "snapshot", "complete": True}
        row, _ = self.run_case([observation(scope="customer_profiles")], scopes=[scope])
        self.assertEqual(row["deletion_status"], "INCOMPLETE")

    def test_reused_resource_with_different_stable_owner_is_not_deleted(self):
        before = observation(state="ABSENT", ids={"subject"}, user_id="subject")
        reused = observation(state="PRESENT", when=NOW, ids={"someone-else"}, user_id="someone-else")
        with self.assertRaisesRegex(InsufficientEvidence, "ownership"):
            self.run_case([before, reused])

    def test_redacted_tombstone_without_stable_reference_is_not_complete(self):
        event = {"event_time": BEFORE, "details": "Linked subject to tombstone", "resource_id": "tombstone", "target_system": "identity_service"}
        tombstone = observation("tombstone", "ACCOUNT_TOMBSTONE", "REDACTED", ids=set(), system="identity_service")
        with self.assertRaisesRegex(InsufficientEvidence, "stable subject reference"):
            self.run_case([tombstone], activities=[event])

    def test_empty_scope_cannot_erase_an_independent_present_copy(self):
        scope = {"system": "account_service", "category": "USER_PROFILE", "scope": "profiles_a", "resources": set(), "captured_at": NOW, "observed_at": NOW, "evidence_id": "snapshot", "complete": True}
        row, steps = self.run_case([observation(scope="profiles_a"), observation(scope="profiles_b")], scopes=[scope])
        self.assertEqual(row["deletion_status"], "INCOMPLETE")
        self.assertEqual(steps[0]["operation"], "REPORT_REMAINING_RECORD")

    def test_catalog_alias_maps_media_filename_without_number_guessing(self):
        event = {"event_type": "LINK_RESOURCE_IDENTITY", "event_time": BEFORE, "details": "Linked object_q (delivery.pdf) to subject", "resource_id": "object_q", "target_system": "object_storage"}
        media = observation("delivery.pdf", "SUPPORT_ATTACHMENT", "PRESENT", system="object_storage", _media=True, _manifest_origin="object_storage")
        rules = RULES + [{"data_category": "SUPPORT_ATTACHMENT", "required_action": "DELETE"}]
        row = audit_request(REQUEST, SUBJECT, EvidenceStore([media], activities=[event]), rules, True)
        self.assertEqual(json.loads(row["steps_json"])[0]["resource_id"], "object_q")

    def test_tombstone_query_reference_is_not_a_preserved_stored_reference(self):
        from evidence import parse_log
        meta = {"file_id": "fixture", "captured_at": BEFORE}
        text = f'{BEFORE} service=identity_service trace_id=x event=lookup_started subject_selector=subject\n{BEFORE} service=identity_service trace_id=x event=lookup_completed resource_id=tombstone_a record_type=ACCOUNT_TOMBSTONE rows=1 subject_reference=null'
        records, _ = parse_log(text, meta)
        self.assertTrue(records)
        with self.assertRaisesRegex(InsufficientEvidence, "stable subject reference"):
            self.run_case(records)

    def test_indexed_activity_mentions_preserve_original_regex_boundaries(self):
        details = ["subject", "not-subject", "subject extra", "user_1", "user_10",
                   "old@example.org", "OLD@EXAMPLE.ORG.", "15550001111", "1555 000 1111",
                   "ſubject", "İNDEX", "STRAßE", "subject name", "a/b"]
        activities = [{"event_time": BEFORE, "details": detail, "resource_id": f"resource_{number}",
                       "target_system": "account_service"} for number, detail in enumerate(details)]
        store = EvidenceStore(activities=activities)
        for identifier in ("subject", "user_1", "old@example.org", "15550001111", "index", "straße", "subject name", "a/b"):
            subject = Subject("custom", {identifier})
            expected = set()
            for event in activities:
                value = event["details"]
                mentioned = norm(value) in subject.identifiers or re.search(
                    r"(?<![\w@.+-])" + re.escape(identifier) + r"(?![\w@.+-])", value, re.I)
                if identifiers(event) & subject.identifiers or mentioned:
                    expected.add((event["target_system"], event["resource_id"]))
            with self.subTest(identifier=identifier):
                self.assertEqual(related_resources(subject, store, NOW), expected)

    def test_indexed_graph_is_cutoff_aware_and_matches_fresh_shuffled_store(self):
        from copy import deepcopy
        account = observation()
        export = observation("export_a", "USER_EXPORT", "PRESENT", when=AFTER, captured=AFTER,
                             ids=set(), system="export_service", source_resource_id="account_a")
        store = EvidenceStore([account, export])
        rules = RULES + [{"data_category": "USER_EXPORT", "required_action": "DELETE"}]
        for cutoff in (NOW, AFTER, BEFORE, AFTER, NOW):
            request = {**REQUEST, "audit_at": cutoff}
            fresh = EvidenceStore(deepcopy(list(reversed(store.observations))))
            with self.subTest(cutoff=cutoff):
                self.assertEqual(audit_request(request, SUBJECT, store, rules, True),
                                 audit_request(request, SUBJECT, fresh, rules, True))
                expected = {("account_service", "account_a")}
                if cutoff == AFTER:
                    expected.add(("export_service", "export_a"))
                self.assertEqual(related_resources(SUBJECT, store, cutoff), expected)

    def test_canonical_views_share_only_exact_eligible_catalog_alias_set(self):
        event = {"event_type": "LINK_RESOURCE_IDENTITY", "event_time": NOW,
                 "details": "Linked object_q (delivery.pdf) to subject", "resource_id": "object_q", "target_system": "object_storage"}
        media = observation("delivery.pdf", "SUPPORT_ATTACHMENT", "PRESENT", system="object_storage",
                            _media=True, _manifest_origin="object_storage")
        store = EvidenceStore([media], activities=[event])
        before = _canonical_view(store, BEFORE)
        now = _canonical_view(store, NOW)
        self.assertIs(before, store)
        self.assertIs(now, _canonical_view(store, AFTER))
        self.assertIsNot(before, now)
        self.assertEqual(now.observations[0].resource, "object_q")
        self.assertIs(_canonical_view(store, BEFORE), before)

    def test_same_length_media_rehydration_invalidates_indexes_and_alias_views(self):
        event = {"event_type": "LINK_RESOURCE_IDENTITY", "event_time": BEFORE,
                 "details": "Linked object_q (delivery.pdf) to subject", "resource_id": "object_q", "target_system": "object_storage"}
        store = EvidenceStore(activities=[event])
        meta = {"file_id": "media_fixture", "captured_at": BEFORE, "origin": "object_storage"}
        record = {"system_id": "object_storage", "resource_id": "delivery.pdf", "record_type": "SUPPORT_ATTACHMENT",
                  "observed_at": BEFORE, "state": "PRESENT", "identifiers": ["old@example.org"], "notes": "Fixture"}
        rules = RULES + [{"data_category": "SUPPORT_ATTACHMENT", "required_action": "DELETE"}]
        hydrate_media(store, meta, {"records": [record]})
        previous_view = _canonical_view(store, NOW)
        self.assertEqual(audit_request(REQUEST, SUBJECT, store, rules, True)["deletion_status"], "INCOMPLETE")
        hydrate_media(store, meta, {"records": [{**record, "state": "ABSENT"}]})
        self.assertEqual(len(store.observations), 1)
        self.assertIsNot(_canonical_view(store, NOW), previous_view)
        self.assertEqual(audit_request(REQUEST, SUBJECT, store, rules, True)["deletion_status"], "COMPLETE")

    def test_refresh_after_in_place_record_edit_rebuilds_relationship_index(self):
        account = observation()
        export = observation("export_a", "USER_EXPORT", "PRESENT", ids=set(), system="export_service")
        store = EvidenceStore([account, export])
        self.assertEqual(related_resources(SUBJECT, store, NOW), {("account_service", "account_a")})
        export.data["source_resource_id"] = "account_a"
        store.refresh()
        self.assertEqual(related_resources(SUBJECT, store, NOW), {("account_service", "account_a"), ("export_service", "export_a")})


if __name__ == "__main__":
    unittest.main()
