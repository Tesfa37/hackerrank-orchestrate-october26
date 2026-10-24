import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence import parse_json, parse_log, parse_sql


META = {"file_id": "evidence_test", "captured_at": "2026-09-10T12:00:00Z"}


class EvidenceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
