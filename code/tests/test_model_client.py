import sys
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_client import GeminiClient, MissingModelResult, classify_requests, extract_media, extract_media_aliases, reinspect_media, validate_media_reinspection, MEDIA_SCHEMA, read_key, validate_schema, quota_metadata


SCHEMA = {"type": "object", "properties": {"ready": {"type": "boolean"}}, "required": ["ready"], "additionalProperties": False}


def provider_response(answer=None, finish="STOP", usage=None):
    return {"candidates": [{"finishReason": finish, "content": {"parts": [{"text": json.dumps(answer if answer is not None else {"ready": True})}]}}], "usageMetadata": usage or {"promptTokenCount": 5, "candidatesTokenCount": 2, "totalTokenCount": 7}}


def provider_stream(raw):
    return io.BytesIO(json.dumps(raw).encode("utf-8"))


def quota_response(quota_id="GenerateRequestsPerMinutePerProjectPerModel-FreeTier", delay="12s"):
    return {"error": {"message": "sensitive-sentinel-not-for-logs", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests", "quotaId": quota_id, "quotaDimensions": {"project": "sensitive-sentinel-not-for-logs"}, "description": "sensitive-sentinel-not-for-logs"}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay},
    ]}}


def review_result():
    return {"captured_at": "2026-09-10T12:00:00Z", "source_summary": "Retained customer reference registry", "review_complete": True, "uncertainties": [], "records": [{
        "resource_id": "", "literal_reference": "user_fixture", "reference_kind": "STABLE_SUBJECT_REFERENCE",
        "category": "account_reference", "record_type": "ACCOUNT_TOMBSTONE", "system_id": "", "source_system_label": "Reference Registry", "state": "UNKNOWN", "stable_reference": "user_fixture",
        "stored_fields": [{"field_name": "user_id", "value": "user_fixture", "source_quote": "Customer key user_fixture", "identifier_role": "STABLE_REFERENCE", "visibility": "VALUE"}],
        "direct_identifiers_visible": [], "context_identifiers": [{"field_name": "search", "value": "lookup@example.org", "source_quote": "Search lookup@example.org"}],
        "field_coverage": "PARTIAL", "direct_fields_coverage": "partial_view", "observed_at": "2026-09-10T12:00:00Z", "time_basis": "CAPTURE_TIME", "observation_time_label": "Supplied artifact capture",
        "last_modified_at": "2026-09-10T13:00:00Z", "last_modified_label": "Most recent update", "last_modified_quote": "Most recent update 10 Sep 2026 13:00 UTC",
        "events": [{"kind": "MODIFIED", "timestamp": "2026-09-10T13:00:00Z", "raw": "10 Sep 2026 13:00 UTC", "source_quote": "Most recent update 10 Sep 2026 13:00 UTC"}],
        "scope": {"kind": "LINKED_REFERENCES", "label": "Selected customer key", "completeness": "PARTIAL", "subject_bound": True, "source_quote": "Customer key user_fixture"},
        "related_references": [{"literal_reference": "ORDER-FIXTURE", "relationship": "Linked to customer", "system_label": "Orders", "source_quote": "Orders ORDER-FIXTURE Linked to customer Active"}],
        "uncertainties": ["Direct identifier fields are not displayed.", "Displayed update time is later than the supplied capture."],
    }]}


class ModelClientTests(unittest.TestCase):
    def test_content_changes_cache_key(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder), prepare=True)
            one = client.job("intent", [{"text": "Delete my account"}], {"type": "object"})
            two = client.job("intent", [{"text": "Keep my account"}], {"type": "object"})
            self.assertNotEqual(one["key"], two["key"])
            self.assertNotIn("api_key", one)

    def test_missing_offline_result_is_not_an_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder), offline=True)
            with self.assertRaises(MissingModelResult):
                client.request("intent", [{"text": "Delete my account"}], {"type": "object"})

    def test_prepare_records_pending_without_fake_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder), prepare=True)
            self.assertIsNone(client.request("intent", [{"text": "Delete my account"}], {"type": "object"}))
            self.assertEqual(len(client.pending), 1)

    def test_truncated_result_is_not_cached_and_usage_is_not_lost(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            raw = provider_response(finish="MAX_TOKENS")
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(raw)):
                with self.assertRaisesRegex(MissingModelResult, "finish"):
                    client.request("smoke", [{"text": "test"}], SCHEMA)
            self.assertEqual(list(client.cache.glob("*.json")), [])
            self.assertEqual(client.usage()["new_calls_this_process"], 1)
            self.assertEqual(client.usage()["total_tokens"], 7)
            rejected = list((Path(folder) / ".cache/rejected").glob("*.json"))
            self.assertEqual(len(rejected), 1)
            envelope = json.loads(rejected[0].read_text(encoding="utf-8"))
            self.assertEqual(envelope["status"], "rejected")
            self.assertEqual(envelope["response"]["candidates"][0]["finishReason"], "MAX_TOKENS")
            offline = GeminiClient(Path(folder), offline=True)
            with self.assertRaisesRegex(MissingModelResult, "Missing genuine"):
                offline.request("smoke", [{"text": "test"}], SCHEMA)

    def test_wrong_json_type_is_not_cached(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            raw = provider_response({"ready": "true"})
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(raw)):
                with self.assertRaisesRegex(MissingModelResult, "type"):
                    client.request("smoke", [{"text": "test"}], SCHEMA)
            self.assertFalse(list(client.cache.glob("*.json")))

    def test_corrupt_completed_response_is_quarantined_and_never_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            raw = provider_response()
            raw["candidates"][0]["content"]["parts"][0]["text"] = "{broken"
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(raw)):
                with self.assertRaisesRegex(MissingModelResult, "quarantined"):
                    client.request("smoke", [{"text": "test"}], SCHEMA)
            self.assertFalse(list(client.cache.glob("*.json")))
            rejected = list((Path(folder) / ".cache/rejected").glob("*.json"))
            self.assertEqual(len(rejected), 1)
            envelope = json.loads(rejected[0].read_text(encoding="utf-8"))
            self.assertEqual(envelope["response"]["candidates"][0]["content"]["parts"][0]["text"], "{broken")
            with self.assertRaisesRegex(MissingModelResult, "Missing genuine"):
                GeminiClient(Path(folder), offline=True).request("smoke", [{"text": "test"}], SCHEMA)

    def test_genuine_response_is_atomic_reused_and_attributed(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response())) as network:
                self.assertEqual(client.request("smoke", [{"text": "test"}], SCHEMA), {"ready": True})
                self.assertEqual(client.request("smoke", [{"text": "test"}], SCHEMA), {"ready": True})
                self.assertEqual(network.call_count, 1)
            self.assertFalse(list(client.cache.glob("*.tmp")))
            offline = GeminiClient(Path(folder), offline=True)
            self.assertEqual(offline.request("smoke", [{"text": "test"}], SCHEMA), {"ready": True})
            self.assertEqual(offline.usage()["new_calls_this_process"], 0)
            self.assertEqual(offline.usage()["cached_results_reused"], 1)
            self.assertEqual(offline.usage()["total_tokens"], 7)
            self.assertEqual(client.usage()["total_tokens"], 7)

    def test_cache_task_or_content_mismatch_does_not_trigger_network(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            job = client.job("smoke", [{"text": "test"}], SCHEMA)
            Path(job["cache_file"]).write_text(json.dumps({**job, "task": "wrong-task", "response": provider_response()}), encoding="utf-8")
            with patch("model_client.urllib.request.urlopen") as network:
                with self.assertRaisesRegex(MissingModelResult, "metadata"):
                    client.request("smoke", [{"text": "test"}], SCHEMA)
                network.assert_not_called()

    def test_retry_usage_is_included_in_cached_production_cost(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            error = HTTPError("https://example.invalid", 503, "unavailable", {}, provider_stream({"usageMetadata": {"promptTokenCount": 3, "totalTokenCount": 3}}))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.time.sleep"), patch("model_client.urllib.request.urlopen", side_effect=[error, provider_stream(provider_response())]):
                client.request("smoke", [{"text": "test"}], SCHEMA)
            self.assertEqual(client.usage()["new_calls_this_process"], 2)
            self.assertEqual(client.usage()["production_attempts"], 2)
            self.assertEqual(client.usage()["input_tokens"], 8)
            self.assertEqual(client.usage()["total_tokens"], 10)
            offline = GeminiClient(Path(folder), offline=True)
            offline.request("smoke", [{"text": "test"}], SCHEMA)
            self.assertEqual(offline.usage()["total_tokens"], 10)

    def test_network_failure_stops_without_fallback_or_fake_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", side_effect=URLError("unavailable")) as network:
                with self.assertRaisesRegex(MissingModelResult, "network access"):
                    client.request("smoke", [{"text": "test"}], SCHEMA)
            self.assertEqual(network.call_count, 1)
            self.assertFalse(list(client.cache.glob("*.json")))
            self.assertEqual(client.usage()["attempts_with_unavailable_usage"], 1)

    def test_daily_quota_stops_immediately_and_retains_only_sanitized_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            error = HTTPError("https://example.invalid", 429, "rate limited", {}, provider_stream(quota_response("GenerateRequestsPerDayPerProjectPerModel-FreeTier")))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.time.sleep") as sleep, patch("model_client.urllib.request.urlopen", side_effect=error) as network:
                with self.assertRaisesRegex(MissingModelResult, "daily quota") as caught:
                    client.request("smoke", [{"text": "test"}], SCHEMA)
            self.assertEqual(network.call_count, 1)
            sleep.assert_not_called()
            self.assertEqual(caught.exception.http_status, 429)
            self.assertEqual(caught.exception.quota_metadata["quotaScope"], "daily")
            ledger = (Path(folder) / ".cache/gemini_attempts.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("sensitive-sentinel", ledger + str(caught.exception))
            self.assertIn("quotaMetric", ledger)
            self.assertIn("quotaId", ledger)

    def test_rate_limit_honors_longer_server_delay_within_one_minute(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            error = HTTPError("https://example.invalid", 429, "rate limited", {"Retry-After": "18"}, provider_stream(quota_response(delay="12.5s")))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.time.sleep") as sleep, patch("model_client.urllib.request.urlopen", side_effect=[error, provider_stream(provider_response())]):
                client.request("smoke", [{"text": "test"}], SCHEMA)
            sleep.assert_called_once_with(18)
            self.assertEqual(client.attempts[0]["quota"]["retryInfoSeconds"], 12.5)
            self.assertEqual(client.attempts[0]["quota"]["retryAfterSeconds"], 18)

    def test_server_delay_over_one_minute_is_reported_without_blocking(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            error = HTTPError("https://example.invalid", 429, "rate limited", {}, provider_stream(quota_response(delay="120s")))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.time.sleep") as sleep, patch("model_client.urllib.request.urlopen", side_effect=error) as network:
                with self.assertRaisesRegex(MissingModelResult, "120 seconds"):
                    client.request("smoke", [{"text": "test"}], SCHEMA)
            sleep.assert_not_called()
            self.assertEqual(network.call_count, 1)

    def test_retry_after_http_date_is_sanitized_and_resolved(self):
        metadata = quota_metadata({}, {"Retry-After": "Sun, 25 Oct 2026 00:00:30 GMT"}, now=datetime(2026, 10, 25, tzinfo=timezone.utc))
        self.assertEqual(metadata["retryAfterSeconds"], 30)
        self.assertEqual(metadata["retryAfterAt"], "2026-10-25T00:00:30+00:00")

    def test_intent_rejects_duplicate_and_nonboolean_responses(self):
        requests = [{"case_id": "a", "request_text": "erase me"}, {"case_id": "b", "request_text": "export only"}]
        for result in ({"requests": [{"case_id": "a", "authorizes_deletion": True}] * 2}, {"requests": [{"case_id": "a", "authorizes_deletion": "false"}, {"case_id": "b", "authorizes_deletion": False}]}):
            client = unittest.mock.Mock()
            client.request.return_value = result
            with self.assertRaises(MissingModelResult):
                classify_requests(client, requests)

    def test_duplicate_intent_input_stops_before_model_call(self):
        client = unittest.mock.Mock()
        with self.assertRaises(ValueError):
            classify_requests(client, [{"case_id": "a", "request_text": "one"}, {"case_id": "a", "request_text": "two"}])
        client.request.assert_not_called()

    def test_duplicate_model_intent_is_never_cached_and_retry_after_restart_keeps_usage(self):
        requests = [{"case_id": "a", "request_text": "Check my earlier deletion."}, {"case_id": "b", "request_text": "Export only, keep the account."}]
        invalid = {"requests": [{"case_id": "a", "authorizes_deletion": True}, {"case_id": "a", "authorizes_deletion": False}]}
        valid = {"requests": [{"case_id": "a", "authorizes_deletion": True}, {"case_id": "b", "authorizes_deletion": False}]}
        with tempfile.TemporaryDirectory() as folder:
            first = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(invalid))):
                with self.assertRaisesRegex(MissingModelResult, "exactly once"):
                    classify_requests(first, requests)
            self.assertFalse(list(first.cache.glob("*.json")))
            second = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(valid))):
                self.assertEqual(classify_requests(second, requests), {"a": True, "b": False})
            offline = GeminiClient(Path(folder), offline=True)
            self.assertEqual(classify_requests(offline, requests), {"a": True, "b": False})
            self.assertEqual(offline.usage()["production_attempts"], 2)
            self.assertEqual(offline.usage()["total_tokens"], 14)

    def test_media_requires_known_category_and_explicit_timestamp(self):
        good = {"system_id": "account_service", "resource_id": "account_fixture", "record_type": "USER_PROFILE", "observed_at": "2026-09-10T00:00:00Z", "state": "PRESENT", "identifiers": ["user_fixture"], "notes": "visible record"}
        validate_schema({"records": [good]}, MEDIA_SCHEMA)
        for bad in ({**good, "record_type": "INVENTED"}, {**good, "observed_at": "2026-09-10"}, {**good, "resource_id": ""}):
            with self.assertRaises(MissingModelResult):
                validate_schema({"records": [bad]}, MEDIA_SCHEMA)

    def test_alias_extraction_rejects_unoffered_id_before_caching(self):
        record = {"system_id": "export_service", "resource_id": "invented-canonical-id", "record_type": "USER_EXPORT", "observed_at": "2026-09-10T00:00:00Z", "state": "PRESENT", "identifiers": ["fixture@example.org"], "notes": "business document"}
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            with patch("model_client.media_content", return_value=[{"text": "Document number BIZ-2026-001 with customer data"}]), patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response({"records": [record]}))):
                with self.assertRaises(MissingModelResult):
                    extract_media_aliases(client, Path("fixture.pdf"), {"captured_at": "2026-09-10T00:00:00Z"}, ["BIZ-2026-001"])
            self.assertFalse(list(client.cache.glob("*.json")))

    def test_alias_prepare_is_stable_and_separate_from_primary_media_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder), prepare=True)
            meta = {"captured_at": "2026-09-10T00:00:00Z"}
            with patch("model_client.media_content", return_value=[{"text": "Document aliases BIZ-A and BIZ-B"}]):
                extract_media(client, Path("fixture.pdf"), meta)
                primary_key = client.pending[0]["key"]
                extract_media_aliases(client, Path("fixture.pdf"), meta, ["BIZ-B", "BIZ-A"])
                alias_key = client.pending[1]["key"]
                extract_media_aliases(client, Path("fixture.pdf"), meta, ["BIZ-A", "BIZ-B", "BIZ-A"])
                extract_media(client, Path("fixture.pdf"), meta)
            self.assertEqual(len(client.pending), 2)
            self.assertEqual(client.pending[0]["key"], primary_key)
            self.assertEqual(client.pending[1]["key"], alias_key)
            self.assertNotEqual(primary_key, alias_key)
            self.assertEqual(client.pending[1]["task"], "business-alias-extraction")
            schema = client.pending[1]["body"]["generationConfig"]["responseFormat"]["text"]["schema"]
            self.assertEqual(schema["properties"]["records"]["items"]["properties"]["resource_id"]["enum"], ["BIZ-A", "BIZ-B"])

    def test_alias_not_literally_in_complete_pdf_text_does_not_call_model(self):
        client = unittest.mock.Mock()
        with patch("model_client.media_content", return_value=[{"text": "No candidate document numbers occur in this complete PDF text."}]):
            self.assertEqual(extract_media_aliases(client, Path("fixture.pdf"), {"captured_at": "2026-09-10T00:00:00Z"}, ["BIZ-UNSEEN"]), {"records": []})
        client.request.assert_not_called()

    def test_review_preserves_stable_reference_context_and_modified_time_separately(self):
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            meta = {"captured_at": "2026-09-10T12:00:00Z", "origin": "identity_service"}
            with patch("model_client.media_content", return_value=[{"text": "Reference Registry Customer key user_fixture"}]), patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(review_result()))):
                result = reinspect_media(client, Path("fixture.png"), meta, [])
            record = result["records"][0]
            self.assertEqual(record["resource_id"], "")
            self.assertEqual(record["direct_identifiers_visible"], [])
            self.assertEqual(record["observed_at"], meta["captured_at"])
            self.assertGreater(record["last_modified_at"], meta["captured_at"])
            self.assertEqual(record["context_identifiers"][0]["field_name"], "search")
            self.assertEqual(record["direct_fields_coverage"], "partial_view")

    def test_review_rejects_stable_id_as_direct_pii_before_cache_publication(self):
        raw = review_result()
        record = raw["records"][0]
        record["stored_fields"][0]["identifier_role"] = "DIRECT_IDENTIFIER"
        record["direct_identifiers_visible"] = [{key: record["stored_fields"][0][key] for key in ("field_name", "value", "source_quote")}]
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            with patch("model_client.media_content", return_value=[{"text": "Reference Registry Customer key user_fixture"}]), patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(raw))):
                with self.assertRaisesRegex(MissingModelResult, "stable internal user reference"):
                    reinspect_media(client, Path("fixture.png"), {"captured_at": raw["captured_at"]}, [])
            self.assertFalse(list(client.cache.glob("*.json")))

    def test_review_cannot_replace_capture_with_modified_time_or_invent_unshown_value(self):
        changed_time = review_result()
        changed_time["records"][0]["observed_at"] = changed_time["records"][0]["last_modified_at"]
        incomplete = review_result()
        incomplete["records"][0]["field_coverage"] = "COMPLETE"
        invented = review_result()
        invented["records"][0]["stored_fields"].append({"field_name": "email", "value": "invented@example.org", "source_quote": "not displayed", "identifier_role": "DIRECT_IDENTIFIER", "visibility": "NOT_SHOWN"})
        fake_resource = review_result()
        fake_resource["records"][0]["resource_id"] = "user_fixture"
        for invalid in (changed_time, incomplete, invented, fake_resource):
            with self.assertRaises(MissingModelResult):
                validate_media_reinspection(invalid)

    def test_invalid_review_timestamp_is_quarantined_with_precise_field_path(self):
        raw = review_result()
        raw["records"][0]["last_modified_at"] = "10 Sep 2026 13:00 UTC"
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            with patch("model_client.media_content", return_value=[{"text": "Reference Registry Customer key user_fixture"}]), patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(raw))):
                with self.assertRaisesRegex(MissingModelResult, r"response.records\[0\].last_modified_at"):
                    reinspect_media(client, Path("fixture.png"), {"captured_at": raw["captured_at"]}, [])
            self.assertFalse(list(client.cache.glob("*.json")))
            rejected = list((Path(folder) / ".cache/rejected").glob("*.json"))
            self.assertEqual(len(rejected), 1)
            envelope = json.loads(rejected[0].read_text(encoding="utf-8"))
            self.assertEqual(envelope["status"], "rejected")
            self.assertEqual(envelope["task"], "business-artifact-semantic-reinspection-v1")
            self.assertEqual(envelope["response"]["candidates"][0]["finishReason"], "STOP")
            self.assertNotIn("test-only", rejected[0].read_text(encoding="utf-8"))

    def test_optional_review_event_time_can_be_empty_but_not_ui_prose_or_bad_date(self):
        empty = review_result()
        empty["records"][0]["events"][0]["timestamp"] = ""
        validate_media_reinspection(empty)
        for value in ("10 Sep 2026 13:00 UTC", "2026-09-10", "2026-13-10T13:00:00Z"):
            invalid = review_result()
            invalid["records"][0]["events"][0]["timestamp"] = value
            with self.assertRaisesRegex(MissingModelResult, r"response.records\[0\].events\[0\].timestamp"):
                validate_media_reinspection(invalid)

    def test_review_refuses_expected_decisions_in_catalog_context(self):
        client = unittest.mock.Mock()
        with self.assertRaises(ValueError):
            reinspect_media(client, Path("fixture.png"), {"captured_at": "2026-09-10T12:00:00Z"}, [{"expected_status": "COMPLETE"}])
        client.request.assert_not_called()

    def test_review_accepts_only_source_quoted_display_blank_markers(self):
        for marker in ("", "—", "–", "-"):
            raw = review_result()
            raw["records"][0]["stored_fields"].append({"field_name": "email", "value": marker, "source_quote": marker, "identifier_role": "DIRECT_IDENTIFIER", "visibility": "BLANK"})
            validate_media_reinspection(raw)
        for value, quote, visibility in (("person@example.org", "person@example.org", "BLANK"), ("—", "not displayed", "BLANK"), ("—", "—", "NOT_SHOWN"), ("null", "null", "BLANK")):
            raw = review_result()
            raw["records"][0]["stored_fields"].append({"field_name": "email", "value": value, "source_quote": quote, "identifier_role": "DIRECT_IDENTIFIER", "visibility": visibility})
            with self.assertRaises(MissingModelResult):
                validate_media_reinspection(raw)

    def test_review_object_name_is_not_confused_with_a_personal_name(self):
        raw = review_result()
        record = raw["records"][0]
        record.update(resource_id="document.pdf", literal_reference="document.pdf", reference_kind="BUSINESS_ALIAS", category="record", record_type="SUPPORT_ATTACHMENT")
        record["stored_fields"] = [{"field_name": "Name", "value": "document.pdf", "source_quote": "document.pdf", "identifier_role": "STABLE_REFERENCE", "visibility": "VALUE"}]
        validate_media_reinspection(raw)
        record["record_type"] = "USER_PROFILE"
        with self.assertRaisesRegex(MissingModelResult, "direct identifier"):
            validate_media_reinspection(raw)

    def test_recover_genuine_rejected_blank_marker_without_requerying_or_changing_response(self):
        raw = review_result()
        raw["records"][0]["stored_fields"].append({"field_name": "display_name", "value": "—", "source_quote": "—", "identifier_role": "DIRECT_IDENTIFIER", "visibility": "BLANK"})
        received = provider_response(raw)
        meta = {"captured_at": raw["captured_at"]}
        with tempfile.TemporaryDirectory() as folder, patch("model_client.media_content", return_value=[{"text": "Source fixture"}]):
            prepared = GeminiClient(Path(folder), prepare=True)
            self.assertIsNone(reinspect_media(prepared, Path("fixture.png"), meta, []))
            job = prepared.pending[0]
            first = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(received)), patch("model_client.validate_media_reinspection", side_effect=MissingModelResult("old blank-marker validation")):
                with self.assertRaises(MissingModelResult):
                    reinspect_media(first, Path("fixture.png"), meta, [])
            with patch("model_client.urllib.request.urlopen") as network:
                self.assertEqual(prepared.recover_rejected(job), raw)
                self.assertEqual(prepared.recover_rejected(job), raw)
                network.assert_not_called()
            envelope = json.loads(Path(job["cache_file"]).read_text(encoding="utf-8"))
            self.assertEqual(envelope["response"], received)
            self.assertIn("recovery", envelope)
            self.assertEqual(prepared.pending, [])
            self.assertEqual(prepared.usage()["new_calls_this_process"], 0)
            self.assertEqual(prepared.usage()["total_tokens"], 7)
            offline = GeminiClient(Path(folder), offline=True)
            self.assertEqual(reinspect_media(offline, Path("fixture.png"), meta, []), raw)
            self.assertEqual(offline.usage()["total_tokens"], 7)

    def test_recover_rejected_still_refuses_unprinted_canonical_ids_and_truncation(self):
        invalid = review_result()
        invalid["records"][0]["resource_id"] = "tombstone_fixture"
        with tempfile.TemporaryDirectory() as folder, patch("model_client.media_content", return_value=[{"text": "Source fixture"}]):
            prepared = GeminiClient(Path(folder), prepare=True)
            reinspect_media(prepared, Path("fixture.png"), {"captured_at": invalid["captured_at"]}, [])
            job = prepared.pending[0]
            client = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(invalid))):
                with self.assertRaises(MissingModelResult):
                    client.request(job["task"], job["body"]["contents"][0]["parts"], job["body"]["generationConfig"]["responseFormat"]["text"]["schema"])
            with self.assertRaisesRegex(MissingModelResult, "canonical resource"):
                prepared.recover_rejected(job)
            self.assertFalse(list(client.cache.glob("*.json")))

    def test_incomplete_review_is_quarantined_and_never_marked_ready(self):
        raw = review_result()
        raw["review_complete"] = False
        with tempfile.TemporaryDirectory() as folder, patch("model_client.media_content", return_value=[{"text": "Source fixture"}]):
            client = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(raw))) as network:
                with self.assertRaisesRegex(MissingModelResult, "did not complete"):
                    reinspect_media(client, Path("fixture.png"), {"captured_at": raw["captured_at"]}, [])
            self.assertEqual(network.call_count, 1)
            self.assertFalse(list(client.cache.glob("*.json")))
            self.assertEqual(client.used, {})
            rejected = list((Path(folder) / ".cache/rejected").glob("*.json"))
            self.assertEqual(len(rejected), 1)

    def test_review_one_stage_repair_skips_known_bad_base_and_reuses_same_hash_offline(self):
        bad = review_result()
        bad["records"][0]["resource_id"] = "tombstone_fixture"
        meta = {"captured_at": bad["captured_at"]}
        with tempfile.TemporaryDirectory() as folder, patch("model_client.media_content", return_value=[{"text": "Source fixture"}]):
            prepared = GeminiClient(Path(folder), prepare=True)
            reinspect_media(prepared, Path("fixture.png"), meta, [])
            base = prepared.pending[0]
            schema = base["body"]["generationConfig"]["responseFormat"]["text"]["schema"]
            first = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(bad))):
                with self.assertRaises(MissingModelResult):
                    first.request(base["task"], base["body"]["contents"][0]["parts"], schema)
            online = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(review_result()))) as network:
                self.assertEqual(reinspect_media(online, Path("fixture.png"), meta, []), review_result())
            self.assertEqual(network.call_count, 1)
            caches = list(online.cache.glob("*.json"))
            self.assertEqual(len(caches), 1)
            envelope = json.loads(caches[0].read_text(encoding="utf-8"))
            self.assertEqual(envelope["repair_of"], [base["key"]])
            self.assertEqual(envelope["repair_stage"], 1)
            self.assertNotEqual(envelope["key"], base["key"])
            self.assertEqual(online.usage()["total_tokens"], 14)
            offline = GeminiClient(Path(folder), offline=True)
            with patch("model_client.urllib.request.urlopen") as network:
                self.assertEqual(reinspect_media(offline, Path("fixture.png"), meta, []), review_result())
                network.assert_not_called()
            self.assertEqual(offline.usage()["total_tokens"], 14)
            self.assertEqual(offline.usage()["new_calls_this_process"], 0)

    def test_failed_semantic_repair_does_not_repeat_base_or_create_second_stage(self):
        bad = review_result()
        bad["records"][0]["field_coverage"] = "COMPLETE"
        meta = {"captured_at": bad["captured_at"]}
        with tempfile.TemporaryDirectory() as folder, patch("model_client.media_content", return_value=[{"text": "Source fixture"}]):
            client = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", side_effect=[provider_stream(provider_response(bad)), provider_stream(provider_response(bad))]) as network:
                with self.assertRaises(MissingModelResult):
                    reinspect_media(client, Path("fixture.png"), meta, [])
            self.assertEqual(network.call_count, 2)
            self.assertFalse(list(client.cache.glob("*.json")))
            retry = GeminiClient(Path(folder))
            with patch("model_client.urllib.request.urlopen") as network:
                with self.assertRaises(MissingModelResult):
                    reinspect_media(retry, Path("fixture.png"), meta, [])
                network.assert_not_called()
            prepared = GeminiClient(Path(folder), prepare=True)
            with self.assertRaises(MissingModelResult):
                reinspect_media(prepared, Path("fixture.png"), meta, [])
            self.assertEqual(prepared.pending, [])
        with tempfile.TemporaryDirectory() as folder:
            client = GeminiClient(Path(folder))
            with patch("model_client.read_key", return_value="test-only"), patch("model_client.urllib.request.urlopen", return_value=provider_stream(provider_response(finish="MAX_TOKENS"))):
                with self.assertRaises(MissingModelResult):
                    client.request("smoke", [{"text": "test"}], SCHEMA)
            with self.assertRaisesRegex(MissingModelResult, "finish successfully"):
                client.recover_rejected(client.job("smoke", [{"text": "test"}], SCHEMA))
            self.assertFalse(list(client.cache.glob("*.json")))

    def test_environment_credential_wins_without_needing_dotenv(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"GEMINI_API_KEY": "test-only"}):
            self.assertEqual(read_key(Path(folder)), "test-only")

    @unittest.skipUnless(shutil.which("node"), "Optional Node transport requires Node")
    def test_node_transport_uses_environment_key_and_writes_python_readable_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            client = GeminiClient(root, prepare=True)
            client.request("smoke", [{"text": "test"}], SCHEMA)
            client.write_jobs()
            helper = (Path(__file__).resolve().parents[1] / "process_model_jobs.mjs").as_uri()
            script = """
import {processJobs} from HELPER;
globalThis.fetch = async () => ({ok:true, status:200, json:async () => (RAW)});
const results = await processJobs(ROOT, {limit:1});
if (results.length !== 1) throw new Error('One missing job should run');
globalThis.fetch = async () => { throw new Error('Cache was not reused'); };
await processJobs(ROOT);
""".replace("HELPER", json.dumps(helper)).replace("ROOT", json.dumps(str(root))).replace("RAW", json.dumps(provider_response()))
            env = dict(os.environ, GEMINI_API_KEY="test-only")
            completed = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, env=env)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            offline = GeminiClient(root, offline=True)
            self.assertEqual(offline.request("smoke", [{"text": "test"}], SCHEMA), {"ready": True})
            self.assertEqual(offline.usage()["total_tokens"], 7)

    @unittest.skipUnless(shutil.which("node"), "Optional Node transport requires Node")
    def test_node_transport_does_not_cache_duplicate_intent_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            client = GeminiClient(root, prepare=True)
            classify_requests(client, [{"case_id": "a", "request_text": "Delete"}, {"case_id": "b", "request_text": "Keep"}])
            client.write_jobs()
            helper = (Path(__file__).resolve().parents[1] / "process_model_jobs.mjs").as_uri()
            invalid = {"requests": [{"case_id": "a", "authorizes_deletion": True}, {"case_id": "a", "authorizes_deletion": False}]}
            script = """
import {processJobs} from HELPER;
globalThis.fetch = async () => ({ok:true, status:200, json:async () => (RAW)});
await processJobs(ROOT);
""".replace("HELPER", json.dumps(helper)).replace("ROOT", json.dumps(str(root))).replace("RAW", json.dumps(provider_response(invalid)))
            completed = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, env=dict(os.environ, GEMINI_API_KEY="test-only"))
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("exactly once", completed.stderr)
            self.assertFalse(list(client.cache.glob("*.json")))
            rejected = list((root / ".cache/rejected").glob("*.json"))
            self.assertEqual(len(rejected), 1)
            self.assertEqual(json.loads(rejected[0].read_text(encoding="utf-8"))["status"], "rejected")

    @unittest.skipUnless(shutil.which("node"), "Optional Node transport requires Node")
    def test_node_daily_quota_stops_before_retry_and_logs_only_public_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            client = GeminiClient(root, prepare=True)
            client.request("smoke", [{"text": "test"}], SCHEMA)
            client.write_jobs()
            helper = (Path(__file__).resolve().parents[1] / "process_model_jobs.mjs").as_uri()
            raw = quota_response("GenerateRequestsPerDayPerProjectPerModel-FreeTier")
            script = """
import {processJobs} from HELPER;
let calls = 0;
globalThis.fetch = async () => { calls++; return {ok:false, status:429, json:async () => (RAW)}; };
globalThis.setTimeout = () => { throw new Error('Daily quota must not sleep/retry'); };
let caught;
try { await processJobs(ROOT); } catch (error) { caught = error; }
if (!caught?.message.includes('daily quota') || calls !== 1 || caught.quotaMetadata?.quotaScope !== 'daily') throw new Error('Daily quota was not diagnosed');
""".replace("HELPER", json.dumps(helper)).replace("ROOT", json.dumps(str(root))).replace("RAW", json.dumps(raw))
            completed = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, env=dict(os.environ, GEMINI_API_KEY="test-only"))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            ledger = (root / ".cache/gemini_attempts.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("sensitive-sentinel", ledger)
            self.assertIn('"quotaScope":"daily"', ledger)
            self.assertFalse(list(client.cache.glob("*.json")))


if __name__ == "__main__":
    unittest.main()
