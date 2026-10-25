"""Reproduce unresolved-audit diagnostics using participant data and genuine caches.

This helper never reads expected answers, makes API calls, writes predictions,
constructs resource IDs, or changes credentials. Candidate raw records are leads
for parser review, not automatically accepted proof of deletion.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from audit_core import IdentityIndex, norm, read_csv, timestamp
from evidence import (EvidenceStore, SYSTEM_FOR_CATEGORY, category_for_table, hydrate_media, hydrate_media_reinspection, identifiers,
                      load_evidence, resource_kind, strings)
from model_client import GeminiClient, classify_requests, extract_media, extract_media_aliases, reinspect_media
from reasoning import InsufficientEvidence, _mentions, audit_request, select_states

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_CATEGORIES = {"USER_PROFILE", "ACCOUNT_TOMBSTONE"}
ANCHOR_ERROR = "Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone"
LABELS = {
    "history_identifier_gap": "Past identity identifier missing from resolved subject",
    "eligible_primary_evidence_not_selected": "Eligible direct primary evidence needs reasoning review",
    "raw_primary_record_not_parsed": "Eligible raw primary record needs parser review",
    "primary_query_without_resource_id": "Eligible negative primary lookup lacks an explicit resource ID",
    "primary_evidence_after_cutoff": "Direct primary evidence excluded by source/capture/observation cutoff",
    "negative_scope_without_owned_resource": "Post-request negative scope without an eligible primary resource ownership edge",
    "only_pre_request_negative_scope": "Only a pre-request negative primary scope is available",
    "no_primary_evidence_or_scope": "No eligible direct primary evidence or complete primary scope",
    "catalog_category_conflict": "Catalog alias changes extracted category",
    "media_field_coverage_uncertainty": "Reviewed image/PDF does not establish required fields, category, or state",
    "other": "Other unresolved reasoning or extraction prerequisite",
}


def load_context(root: Path, dataset: Path, samples: bool = False, reinspect: bool = False, with_usage: bool = False):
    """Use exactly the CLI's genuine intent/media cache requests, offline only."""
    store = load_evidence(dataset)
    snapshots = read_csv(dataset / "user_identities.csv")
    history = read_csv(dataset / "user_audit_log.csv")
    requests = read_csv(dataset / ("sample_deletion_requests.csv" if samples else "deletion_requests.csv"))
    client = GeminiClient(root, offline=True)
    intents = {}
    for offset in range(0, len(requests), 40):
        intents.update(classify_requests(client, requests[offset:offset + 40]))
    subject_ids = {row["user_id"] for row in snapshots}
    aliases = {value for event in store.activities if event.get("event_type") == "LINK_RESOURCE_IDENTITY"
               for value in re.findall(r"\(([^()]+)\)", event.get("details", ""))
               if value != event.get("resource_id") and value not in subject_ids}
    for path, meta in store.media:
        result = extract_media(client, path, meta)
        if not result["records"] and aliases:
            result = extract_media_aliases(client, path, meta, sorted(aliases))
        hydrate_media(store, meta, result)
    if reinspect:
        catalog_context = [event for event in store.activities if event.get("event_type") == "LINK_RESOURCE_IDENTITY"]
        for path, meta in store.media:
            # Canonical catalog IDs are joined only after extraction. Showing
            # them to the model can prime IDs not actually printed in a source.
            reviewed = reinspect_media(client, path, meta, [])
            hydrate_media_reinspection(store, meta, reviewed, catalog_context)
    context = (requests, store, IdentityIndex(snapshots, history), history, read_csv(dataset / "deletion_rules.csv"), intents)
    return (*context, client.usage()) if with_usage else context


def _raw_values(record):
    return identifiers(record) | {norm(value) for value in strings(record) if value}


def raw_primary_records(dataset: Path, manifest: list[dict]) -> list[dict]:
    """Independently inventory explicit primary rows and correlated log records.

    SQL/JSON dictionaries retain only their own entity context. Log joins use
    explicit trace IDs within the same source/service. No neighboring rows,
    resource suffixes, names, or artifact filenames supply ownership.
    """
    found = []

    def add(record, meta, locator, collection="", observed="", linked_ids=()):
        resource = str(record.get("resource_id", ""))
        category = record.get("record_type", record.get("category", ""))
        category = category or resource_kind(resource, collection)[1] or category_for_table(collection)
        if category not in PRIMARY_CATEGORIES:
            return
        when = record.get("observed_at", record.get("recorded_at", observed or meta["captured_at"]))
        found.append({"resource_id": resource, "category": category, "evidence_id": meta["file_id"],
                      "source_path": meta["file_path"], "locator": locator,
                      "captured_at": meta["captured_at"], "observed_at": when,
                      "identifiers": _raw_values(record) | set(linked_ids),
                      "explicit_negative": (str(record.get("rows", "")) == "0"
                                            or str(record.get("http_status", record.get("status_code", ""))) == "404"
                                            or str(record.get("state", record.get("result", ""))).upper() in {"ABSENT", "NOT_FOUND"})})

    for meta in manifest:
        path = dataset / meta["file_path"]
        if path.suffix == ".json":
            def walk(value, collection="", observed="", locator="$"):
                if isinstance(value, dict):
                    collection = value.get("collection", collection)
                    observed = value.get("captured_at", value.get("observed_at", value.get("recorded_at", observed)))
                    if "resource_id" in value:
                        add(value, meta, locator, collection, observed)
                    for key, child in value.items():
                        if isinstance(child, (dict, list)):
                            walk(child, collection or key, observed, f"{locator}.{key}")
                elif isinstance(value, list):
                    for number, child in enumerate(value):
                        walk(child, collection, observed, f"{locator}[{number}]")
            walk(json.loads(path.read_text(encoding="utf-8")))
        elif path.suffix == ".sql":
            db = sqlite3.connect(":memory:")
            db.row_factory = sqlite3.Row
            db.enable_load_extension(False)
            def authorize(action, arg1, arg2, database, source):
                if action in {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}:
                    return sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_FUNCTION and str(arg2).lower() in {"load_extension", "readfile", "writefile"}:
                    return sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_PRAGMA and str(arg1).lower() != "foreign_keys":
                    return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            db.set_authorizer(authorize)
            try:
                db.executescript(path.read_text(encoding="utf-8"))
                tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                declared = ({row["origin_system"]: row["captured_at"] for row in db.execute("SELECT * FROM snapshot_scope")}
                            if "snapshot_scope" in tables else {})
                for table in tables:
                    if table == "snapshot_scope":
                        continue
                    quoted = '"' + table.replace('"', '""') + '"'
                    for number, raw in enumerate(db.execute("SELECT * FROM " + quoted)):
                        record = dict(raw)
                        collection = record.get("collection_name", table)
                        system = record.get("origin_system", SYSTEM_FOR_CATEGORY.get(category_for_table(table), ""))
                        if "record_json" in record:
                            record = json.loads(record["record_json"])
                        add(record, meta, f"table {table}, row {number + 1}", collection,
                            declared.get(system, meta["captured_at"]))
            finally:
                db.close()
        elif path.suffix == ".log":
            lines = []
            trace_ids = defaultdict(set)
            pairs = re.compile(r'(\w+)=("(?:\\.|[^"\\])*"|\S+)')
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                time = re.match(r"(\d{4}-\d\d-\d\dT[\d:.]+Z)", line)
                if not time:
                    continue
                rest = line[len(time[1]):].strip()
                try:
                    record = json.loads(rest) if rest.startswith("{") else {
                        key: json.loads(value) if value.startswith('"') else value for key, value in pairs.findall(rest)}
                except json.JSONDecodeError:
                    continue
                if isinstance(record.get("message"), str):
                    for field, value in pairs.findall(record["message"]):
                        try:
                            record[field] = json.loads(value) if value.startswith('"') else value
                        except json.JSONDecodeError:
                            record[field] = value.strip('"')
                trace = record.get("trace_id", record.get("requestId", ""))
                if not trace:
                    match = re.search(r"\btr-[A-Za-z0-9]+\b", line)
                    trace = match[0] if match else ""
                service = re.search(r"\b(account_service|profile_service|identity_service)\b", line)
                key = (service[0] if service else record.get("service", ""), trace)
                own_ids = _raw_values(record)
                if trace:
                    trace_ids[key].update(own_ids)
                lines.append((record, number, time[1], key, own_ids))
            for record, number, when, key, own_ids in lines:
                negative_query = (key[0] in {"account_service", "profile_service"}
                                  and str(record.get("rows", "")) == "0"
                                  and str(record.get("event", "")).endswith("_completed"))
                if record.get("resource_id") or negative_query:
                    add(record, meta, f"line {number}", "customer_profiles" if negative_query else "", observed=when,
                        linked_ids=trace_ids.get(key, ()) if key[1] else own_ids)
        elif path.suffix == ".txt":
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                fields = [value.strip() for value in line.removeprefix("- ").split("|")]
                if len(fields) == 6 and re.match(r"\d{4}-", fields[0]):
                    add(dict(zip(("observed_at", "system", "resource_id", "record_type", "result", "subject_reference"), fields)), meta, f"line {number}")
    return found


def _reference(observation, paths):
    return {"evidence_id": observation.evidence_id, "source_path": paths.get(observation.evidence_id, ""),
            "resource_id": observation.resource, "category": observation.category, "state": observation.state,
            "scope": observation.scope, "captured_at": observation.captured_at, "observed_at": observation.observed_at,
            "catalog_available_at": observation.data.get("_catalog_event_time", ""),
            "media_review": bool(observation.data.get("_media_reinspection")),
            "uncertainty": observation.data.get("_uncertainty", "")}


def diagnose(requests, store: EvidenceStore, identities, history, rules, intents, manifest, raw_records=()):
    """Return diagnostic groups; never derive a prediction from missing proof."""
    paths = {row["file_id"]: row["file_path"] for row in manifest}
    history_by_user = defaultdict(list)
    for change in history:
        history_by_user[change["user_id"]].append(change)
    blockers, resolved = [], Counter()
    identity_checks, historical_requests = {}, set()
    for request in requests:
        try:
            subject = identities.resolve(request["email"], request["audit_at"])
            identity_checks[request["case_id"]] = subject
            if any(change["field_name"] == "email" and timestamp(change["event_time"]) <= timestamp(request["audit_at"])
                   and norm(change["old_value"]) == norm(request["email"]) for change in history_by_user[subject.user_id]):
                historical_requests.add(request["case_id"])
        except ValueError:
            pass
    for request in requests:
        case_id, cutoff = request["case_id"], request["audit_at"]
        subject = None
        try:
            intent = intents[case_id]
            subject = identities.resolve(request["email"], cutoff) if intent else None
            row = audit_request(request, subject, store, rules, intent, full_subject_audit=True)
            resolved[row["deletion_status"]] += 1
            continue
        except (KeyError, InsufficientEvidence, ValueError) as error:
            reason = str(error)
        detail = {"case_id": case_id, "requested_at": request["requested_at"], "audit_at": cutoff, "error": reason,
                  "group": "other", "account_observations": [], "raw_primary_candidates": [], "primary_scopes": [],
                  "media_uncertainties": [], "request_uses_historical_email": case_id in historical_requests}
        if subject is None:
            blockers.append(detail)
            continue
        detail["user_id"] = subject.user_id
        limit = timestamp(cutoff)
        expected_history = {norm(change[field]) for change in history_by_user[subject.user_id]
                            if change["field_name"] in {"email", "phone", "email_hash"} and timestamp(change["event_time"]) <= limit
                            for field in ("old_value", "new_value") if change[field]}
        detail["missing_past_identifier_count"] = len(expected_history - subject.identifiers)
        detail["historical_identifier_count"] = len(expected_history)
        account_obs = [o for o in store.observations if o.category in PRIMARY_CATEGORIES and o.identifiers & subject.identifiers]
        eligible = [o for o in account_obs if o.eligible(cutoff)]
        detail["account_observations"] = [_reference(o, paths) for o in account_obs]
        detail["primary_capture_after_cutoff_count"] = sum(timestamp(o.captured_at) > limit for o in account_obs)
        detail["primary_observation_after_cutoff_count"] = sum(timestamp(o.observed_at) > limit for o in account_obs)
        detail["primary_catalog_after_cutoff_count"] = sum(bool(o.data.get("_catalog_event_time")) and
                                                          timestamp(o.data["_catalog_event_time"]) > limit for o in account_obs)
        raw_matches = [record for record in raw_records if record["identifiers"] & subject.identifiers]
        detail["raw_primary_candidates"] = [{key: value for key, value in record.items() if key != "identifiers"} for record in raw_matches]
        raw_eligible = [record for record in raw_matches if timestamp(record["captured_at"]) <= limit and timestamp(record["observed_at"]) <= limit]
        parsed = {(o.evidence_id, o.resource) for o in account_obs}
        unparsed = [record for record in raw_eligible if record["resource_id"] and (record["evidence_id"], record["resource_id"]) not in parsed]
        negative_queries_without_id = [record for record in raw_eligible if not record["resource_id"] and record.get("explicit_negative")]
        scopes = [scope for scope in store.scopes if scope["category"] == "USER_PROFILE" and scope["system"] == "account_service"
                  and scope.get("complete", False) and "replica" not in scope["scope"].casefold()
                  and timestamp(scope["captured_at"]) <= limit and timestamp(scope["observed_at"]) <= limit]
        for scope in sorted(scopes, key=lambda value: timestamp(value["observed_at"]), reverse=True):
            detail["primary_scopes"].append({key: value for key, value in scope.items() if key not in {"resources", "covers_scopes"}} |
                                            {"resource_count": len(scope["resources"]), "source_path": paths.get(scope["evidence_id"], "")})
        post_request = [scope for scope in scopes if timestamp(scope["observed_at"]) >= timestamp(request["requested_at"])]
        detail["post_request_primary_scope_count"] = len(post_request)
        detail["eligible_primary_activity_count"] = sum(
            1 for event in store.activities if timestamp(event["event_time"]) <= limit
            and (identifiers(event) & subject.identifiers or _mentions(event.get("details", ""), subject))
            and (event.get("target_system") == "account_service" or event.get("resource_id", "").startswith("account_")))
        try:
            selected = select_states(subject, store, cutoff)
            detail["selected_categories"] = sorted({o.category for o in selected})
            detail["media_uncertainties"] = [_reference(o, paths) for o in selected
                                             if o.data.get("_media_reinspection") and o.state == "UNKNOWN"]
        except InsufficientEvidence:
            detail["selected_categories"] = []
        if detail["missing_past_identifier_count"]:
            detail["group"] = "history_identifier_gap"
        elif detail["media_uncertainties"]:
            detail["group"] = "media_field_coverage_uncertainty"
        elif "Catalog alias changes" in reason:
            detail["group"] = "catalog_category_conflict"
        elif reason == ANCHOR_ERROR:
            if unparsed:
                detail["group"] = "raw_primary_record_not_parsed"
            elif negative_queries_without_id:
                detail["group"] = "primary_query_without_resource_id"
            elif eligible:
                detail["group"] = "eligible_primary_evidence_not_selected"
            elif account_obs or raw_matches:
                detail["group"] = "primary_evidence_after_cutoff"
            elif post_request:
                detail["group"] = "negative_scope_without_owned_resource"
            elif scopes:
                detail["group"] = "only_pre_request_negative_scope"
            else:
                detail["group"] = "no_primary_evidence_or_scope"
        blockers.append(detail)
    anchor_blockers = [case for case in blockers if case["error"] == ANCHOR_ERROR]
    return {"request_count": len(requests), "resolved_count": sum(resolved.values()), "resolved_status_counts": dict(resolved),
            "blocked_count": len(blockers), "group_counts": dict(Counter(row["group"] for row in blockers)), "cases": blockers,
            "negative_scope_checks": {
                "anchor_blocked_count": len(anchor_blockers),
                "anchor_with_post_request_scope": sum(case.get("post_request_primary_scope_count", 0) > 0 for case in anchor_blockers),
                "anchor_with_only_pre_request_scope": sum(bool(case["primary_scopes"]) and not case.get("post_request_primary_scope_count", 0) for case in anchor_blockers),
                "anchor_without_scope": sum(not case["primary_scopes"] for case in anchor_blockers)},
            "checks": {"expected_answers_read": False, "network_calls": 0,
                       "raw_primary_record_count": len(raw_records), "media_hydrated": len(store.hydrated_media),
                       "media_reinspected": len(store.reinspected_media),
                       "identity_requests_resolved_uniquely": len(identity_checks),
                       "identity_resolution_failures": len(requests) - len(identity_checks),
                       "requests_using_past_historical_email": len(historical_requests),
                       "blocked_requests_using_past_historical_email": sum(case["request_uses_historical_email"] for case in blockers),
                       "historical_identifier_gap_cases": sum(case.get("missing_past_identifier_count", 0) > 0 for case in blockers),
                       "raw_primary_parser_review_cases": sum(case["group"] == "raw_primary_record_not_parsed" for case in blockers)}}


def markdown(result):
    lines = ["# Unresolved audit investigation", "",
             f"Reproduced {result['request_count']} requests using participant data and genuine offline model caches: "
             f"{result['resolved_count']} resolved, {result['blocked_count']} blocked.", "",
             "No expected answers or hidden labels were read. No API calls, billing changes, credential edits, "
             "prediction files, or manufactured resource IDs were produced.", "",
             "| Diagnostic group | Cases |", "| --- | ---: |"]
    for group, count in sorted(result["group_counts"].items()):
        lines.append(f"| {LABELS[group]} | {count} |")
    lines += ["", "The groups identify the next missing proof; they do not establish that an unresolved case is COMPLETE or INCOMPLETE. "
              "A SQL table tagged complete by the adapter is scoped snapshot evidence, not permission to guess an absent user's resource ID. "
              "A missing row can prove absence only with applicable exhaustive coverage and a grounded identity/resource relationship. "
              "A snapshot before the request is separately identified; evidence captured after audit_at remains excluded even when its event is earlier.", "",
              "Historical email, phone, and hash values at or before each cutoff are checked against the resolved subject. "
              "Raw SQL/JSON entities and explicit log traces are independently inventoried for primary records missed by parsing. "
              "Screenshots/PDFs use their genuine cached interpretation; this is not independent verification that a model extracted every visual fact.", ""]
    lines += [f"Independent raw inventory: {result['checks']['raw_primary_record_count']} explicit primary SQL/JSON/log/text records. "
              f"Historical identifier gaps among blocked cases: {result['checks']['historical_identifier_gap_cases']}. "
              f"Eligible raw primary records requiring parser review: {result['checks']['raw_primary_parser_review_cases']}.", ""]
    lines += [f"Identity checks: {result['checks']['identity_requests_resolved_uniquely']} requests resolve to exactly one subject; "
              f"{result['checks']['identity_resolution_failures']} fail identity resolution. "
              f"{result['checks']['requests_using_past_historical_email']} request emails match an old email in an eligible past change; "
              f"{result['checks']['blocked_requests_using_past_historical_email']} of those requests remain blocked. "
              f"Hydrated media: {result['checks']['media_hydrated']}; source-fact reinspections: {result['checks']['media_reinspected']}.", ""]
    negatives = result["negative_scope_checks"]
    lines += [f"Primary-anchor blockers were separately reviewed for negative snapshots: {negatives['anchor_with_post_request_scope']} "
              f"of {negatives['anchor_blocked_count']} have eligible complete primary scopes at or after the request, "
              f"{negatives['anchor_with_only_pre_request_scope']} have only pre-request scopes, and "
              f"{negatives['anchor_without_scope']} have none. These counts identify useful scoped negative evidence, "
              "rather than asserting that all anchor blockers lack every kind of evidence. No scope supplies an unprinted resource ID "
              "or an absent person's ownership link merely because no identifier matched a row.", ""]
    for group in sorted(result["group_counts"]):
        cases = [case for case in result["cases"] if case["group"] == group]
        lines += [f"## {LABELS[group]}", "", "Cases: " + ", ".join(case["case_id"] for case in cases) + ".", ""]
        for case in cases[:3]:
            lines += [f"**{case['case_id']}** ({case.get('user_id', 'identity unresolved')}); request `{case['requested_at']}`, audit cutoff `{case['audit_at']}`.", "",
                      f"Missing proof: {case['error']}.", ""]
            if case["account_observations"]:
                for source in case["account_observations"]:
                    catalog = f", required catalog link `{source['catalog_available_at']}`" if source["catalog_available_at"] else ""
                    lines.append(f"- `{source['evidence_id']}`: `{source['source_path']}`, resource `{source['resource_id']}` ({source['state']}); capture `{source['captured_at']}`, observation `{source['observed_at']}`{catalog}.")
                lines.append("")
            if case["media_uncertainties"]:
                for source in case["media_uncertainties"]:
                    lines += [f"Reviewed source `{source['evidence_id']}`, `{source['source_path']}`, resource `{source['resource_id']}`: "
                              f"{source['uncertainty'] or 'Required source fields or current treatment remain unknown.'} "
                              f"Capture `{source['captured_at']}`, observation `{source['observed_at']}`.", ""]
            if case["primary_scopes"]:
                scope = case["primary_scopes"][0]
                lines += [f"Latest eligible primary scope: `{scope['evidence_id']}`, `{scope['source_path']}`, table/collection `{scope['scope']}`, "
                          f"capture `{scope['captured_at']}`, observation `{scope['observed_at']}`, {scope['resource_count']} resource rows. "
                          "No account resource ownership edge is inferred from that row count or from an identifier suffix.", ""]
            if not case["account_observations"] and not case["primary_scopes"]:
                lines += ["No eligible direct account/tombstone row or complete primary scope was found for this subject.", ""]
    command = "python3 code/investigate.py" + (" --reinspect-media" if result['checks']['media_reinspected'] else "")
    lines += ["## Reproduction", "", "```bash", command, "```", "",
              "The JSON companion contains every blocked case, provenance, scope timestamps, and history checks. "
              "This report records a development investigation, not final prediction accuracy or a completed submission.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "dataset")
    parser.add_argument("--samples", action="store_true")
    parser.add_argument("--reinspect-media", action="store_true", help="Use genuine cached source-fact reinspection of every PDF/image")
    parser.add_argument("--report", type=Path, default=ROOT / "code/evaluation/blocker_report.md")
    parser.add_argument("--json", type=Path, default=ROOT / ".cache/blocker_report.json", dest="json_path")
    args = parser.parse_args(argv)
    dataset = args.dataset.resolve()
    for output, suffix, permitted in ((args.report, ".md", ROOT / "code/evaluation/blocker_report.md"),
                                       (args.json_path, ".json", ROOT / ".cache/blocker_report.json")):
        target = output.resolve()
        if target.is_relative_to(dataset):
            parser.error("Diagnostic reports must not overwrite participant input data")
        if target.suffix.lower() != suffix:
            parser.error(f"Diagnostic output must use the {suffix} extension")
        if target.is_relative_to(ROOT) and target.exists() and target != permitted and not target.is_relative_to(ROOT / ".cache"):
            parser.error("Diagnostic output must not overwrite an existing repository file")
    if args.report.resolve() == args.json_path.resolve():
        parser.error("Markdown and JSON reports require different paths")
    requests, store, identities, history, rules, intents = load_context(ROOT, dataset, args.samples, args.reinspect_media)
    manifest = read_csv(dataset / "evidence_files.csv")
    result = diagnose(requests, store, identities, history, rules, intents, manifest, raw_primary_records(dataset, manifest))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(markdown(result), encoding="utf-8")
    args.json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Investigated {result['request_count']} requests: {result['blocked_count']} blocked; groups {result['group_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
