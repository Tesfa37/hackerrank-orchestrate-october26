"""Generic adapters for participant-visible business artifacts, with provenance."""
from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from audit_core import Observation, norm, read_csv, timestamp

PREFIXES = {
    "data_flow_": ("integration_service", "DATA_FLOW"), "audit_record_": ("security_service", "SECURITY_AUDIT_LOG"),
    "legal_hold_": ("legal_service", "LEGAL_HOLD_RECORD"), "tombstone_": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "account_": ("account_service", "USER_PROFILE"), "search_": ("search_service", "SEARCH_INDEX_ENTRY"),
    "analytics_": ("analytics_platform", "ANALYTICS_PROFILE"), "backup_": ("backup_service", "BACKUP_ARCHIVE"),
    "export_": ("export_service", "USER_EXPORT"), "support_": ("support_platform", "SUPPORT_MESSAGE"),
    "cache_": ("cache_service", "CACHE_ENTRY"), "marketing_": ("marketing_platform", "MARKETING_PROFILE"),
    "email_delivery_": ("email_delivery_service", "EMAIL_DELIVERY_LOG"), "identifier_": ("identity_service", "SECONDARY_IDENTIFIER"),
}
ALIASES = {"profile_service": "account_service", "support_replica": "support_platform", "search_index_service": "search_service"}
IDENTIFIER_KEYS = {"email", "email_hash", "phone", "user_id", "customer_reference", "subject_reference", "subject_ref", "subject_key", "subject_selector", "lookup_key", "lookup_value", "match_key", "correlation_key", "matched_value", "query", "owner_key", "owner_email", "owner_phone", "customer_email", "requester_email", "requester_phone", "uploaded_by"}
DIRECT_KEYS = {"email", "email_hash", "phone", "name", "full_name", "display_name", "owner_email", "owner_phone", "customer_email", "requester_email", "requester_phone", "requester_name"}
RESULTS = {"NOT_FOUND": "ABSENT", "ABSENT": "ABSENT", "FOUND": "PRESENT", "PRESENT": "PRESENT", "IDENTIFIABLE": "PRESENT", "REDACTED": "REDACTED", "ANONYMIZED": "ANONYMIZED", "DISABLED": "DISABLED", "BLOCKED": "BLOCKED", "ENABLED": "ACTIVE", "ACTIVE": "ACTIVE", "RESTORABLE": "ACTIVE"}
CATEGORIES = {kind[1] for kind in PREFIXES.values()} | {"SUPPORT_ATTACHMENT", "PRODUCT_TELEMETRY"}
CORRELATION_KEYS = {"lookup_key", "lookup_value", "match_key", "correlation_key", "query", "owner_key", "subject_key", "subject_selector"}
SYSTEM_FOR_CATEGORY = {category: system for system, category in PREFIXES.values()}
SYSTEM_FOR_CATEGORY.update({"SUPPORT_ATTACHMENT": "support_platform", "PRODUCT_TELEMETRY": "analytics_platform"})
KNOWN_SYSTEMS = set(SYSTEM_FOR_CATEGORY.values()) | {'object_storage'}


def has_value(value) -> bool:
    return value is not None and str(value).strip().casefold() not in {"", "null", "none", "[redacted]", "redacted"}


def record_payload(data):
    """Drop search inputs, which link an observation but do not expose its stored PII."""
    if isinstance(data, dict):
        return {key: record_payload(value) for key, value in data.items() if key not in CORRELATION_KEYS}
    if isinstance(data, list):
        return [record_payload(value) for value in data]
    return data


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from strings(value)


def identifiers(obj) -> set[str]:
    found = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in IDENTIFIER_KEYS and isinstance(value, (str, int)) and str(value).lower() not in {"null", "none", "[redacted]", "redacted", ""}:
                found.add(norm(value))
            if isinstance(value, (dict, list)):
                found.update(identifiers(value))
    elif isinstance(obj, list):
        for value in obj:
            found.update(identifiers(value))
    for text in strings(obj):
        found.update(norm(x) for x in re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text))
        found.update(re.findall(r"\buser_[A-Za-z0-9]+\b", text))
        found.update(re.findall(r"\b[a-f0-9]{64}\b", text))
    return found


def stored_identifiers(record) -> set[str]:
    """Return identifiers in stored fields, excluding search/trace attribution.

    ``Observation.identifiers`` intentionally includes lookup values for identity
    joins. That index cannot prove that a tombstone retains its stable reference.
    Media facts use the explicit extracted record identifier array; explanatory
    notes and raw log messages are provenance, not additional stored fields.
    """
    if isinstance(record, list):
        return set().union(*(stored_identifiers(item) for item in record)) if record else set()
    if not isinstance(record, dict):
        return set()
    if record.get('_media'):
        return {norm(value) for value in record.get('identifiers', []) if isinstance(value, str) and has_value(value)}
    found = set()
    context_keys = set(record.get('_trace_context_keys', []))
    for key, value in record.items():
        if key in CORRELATION_KEYS or key in context_keys or key.startswith('_'):
            continue
        if key in IDENTIFIER_KEYS and isinstance(value, (str, int)) and has_value(value):
            found.add(norm(value))
        if key in {'identifiers', 'stored_identifiers'} and isinstance(value, list):
            found.update(norm(item) for item in value if isinstance(item, str) and has_value(item))
        elif isinstance(value, (dict, list)):
            found.update(stored_identifiers(value))
        elif key in {'message_text', 'message_excerpt', 'body', 'text'} and isinstance(value, str):
            found.update(identifiers(value))
    return found


def resource_kind(resource: str, collection: str = "", explicit: str = "") -> tuple[str, str]:
    system, category = next((value for prefix, value in PREFIXES.items() if resource.startswith(prefix)), ("", ""))
    context = collection.lower()
    if "attachment" in context:
        category = "SUPPORT_ATTACHMENT"
    elif "contact_query" in context or "contact_lookup" in context or "legacy_contact_index" in context or "secondary_identifier" in context:
        category = "SECONDARY_IDENTIFIER"
    if explicit:
        category = explicit
    return system, category


def infer_state(data: dict, category: str) -> str:
    result = str(data.get("state", data.get("result", ""))).upper()

    def flag(value):
        text = str(value).strip().lower()
        if text in {'true', '1', 'enabled', 'allowed'}:
            return True
        if text in {'false', '0', 'disabled', 'denied', 'blocked'}:
            return False
        return None

    def exposed(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in DIRECT_KEYS and has_value(value):
                    return True
                if isinstance(value, (dict, list)) and exposed(value):
                    return True
                if key in {'message_text', 'message_excerpt', 'body', 'text'} and isinstance(value, str) and re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', value):
                    return True
        elif isinstance(obj, list):
            return any(exposed(item) for item in obj)
        return False

    # Stored configuration and visible payload values establish state more
    # directly than a generic compliance label on the same row.
    if category == 'DATA_FLOW':
        enabled = flag(data.get('enabled', data.get('active')))
        if enabled is not None:
            return 'ACTIVE' if enabled else 'DISABLED'
    if category == 'BACKUP_ARCHIVE':
        allowed = flag(data.get('restore_allowed'))
        if allowed is not None:
            return 'ACTIVE' if allowed else 'BLOCKED'
        blocked = flag(data.get('deletion_block'))
        if blocked is not None:
            return 'BLOCKED' if blocked else 'ACTIVE'
        if flag(data.get('eligible')) is True:
            return 'ACTIVE'
        if str(data.get('decision', '')).lower() in {'deny', 'denied', 'block', 'blocked'}:
            return 'BLOCKED'
    payload = record_payload(data)
    if result in {'REDACTED', 'ANONYMIZED'}:
        if category in {'ANALYTICS_PROFILE', 'PRODUCT_TELEMETRY'} and identifiers(payload):
            return 'PRESENT'
        if category in {'SUPPORT_MESSAGE', 'ACCOUNT_TOMBSTONE', 'EMAIL_DELIVERY_LOG'} and (exposed(payload) or data.get('pii_detected') in (True, 'true') or has_value(data.get('matched_value'))):
            return 'PRESENT'
    if result in RESULTS:
        if category not in {'DATA_FLOW', 'BACKUP_ARCHIVE'} and RESULTS[result] in {'ACTIVE', 'DISABLED', 'BLOCKED'}:
            # An active profile/export/audience row exists; process lifecycle
            # states are meaningful only for flows and restore controls.
            return 'PRESENT'
        return RESULTS[result]
    if data.get("status_code", data.get("http_status")) in (404, "404"):
        return "ABSENT"
    if "rows" in data and str(data["rows"]) == "0":
        return "ABSENT"
    if "hits" in data:
        hits = data["hits"]
        total = hits.get("total", 0) if isinstance(hits, dict) else hits
        return "ABSENT" if total in (0, "0") else "PRESENT"
    if result in {"MISS", "EMPTY"} or str(data.get("total_hits", "")) == "0":
        return "ABSENT"
    if category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"}:
        return "PRESENT" if identifiers(payload) else "ANONYMIZED"
    if category in {"SUPPORT_MESSAGE", "ACCOUNT_TOMBSTONE", "EMAIL_DELIVERY_LOG"}:
        if data.get("pii_detected") in (True, "true") or data.get("matched_value"):
            return "PRESENT"
        return "PRESENT" if exposed(payload) else "REDACTED"
    if str(data.get("available", "")).lower() in {"false", "0"}:
        return "ABSENT"
    return "PRESENT"


def make_observation(record: dict, meta: dict, system="", collection="", observed="", scope="") -> Observation | None:
    resource = str(record.get("resource_id", ""))
    if not resource:
        return None
    inferred_system, category = resource_kind(resource, collection, record.get("record_type", record.get("category", "")))
    system = record.get("system", record.get("system_id", system)) or inferred_system
    system = ALIASES.get(system, system)
    if not category or not system:
        return None
    when = record.get("observed_at", record.get("recorded_at", observed or meta["captured_at"]))
    return Observation(system, resource, category, infer_state(record, category), meta["file_id"], meta["captured_at"], when, identifiers(record), record, scope)


def parse_json(obj: dict, meta: dict):
    observations, scopes = [], []

    def walk(value, system="", collection="", observed="", parent_key=""):
        if isinstance(value, dict):
            system = value.get("data_store", value.get("system", value.get("system_id", system)))
            collection = value.get("collection", collection)
            observed = value.get("captured_at", value.get("observed_at", value.get("recorded_at", observed)))
            if "resource_id" in value:
                observation = make_observation(value, meta, system, collection, observed, collection)
                if observation:
                    observations.append(observation)
                return
            records = value.get("records")
            if isinstance(records, list) and collection and system:
                groups = defaultdict(set)
                for row in records:
                    if isinstance(row, dict) and row.get("resource_id"):
                        _, kind = resource_kind(str(row['resource_id']), collection, row.get('record_type', row.get('category', '')))
                        if kind:
                            groups[kind].add(str(row['resource_id']))
                kind = category_for_table(collection)
                if kind:
                    groups.setdefault(kind, set())
                # A dated collection may still be an excerpt or a scoped export.
                # Missing rows prove absence only when the artifact explicitly
                # declares exhaustive coverage, never from its wrapper or name.
                declarations = [value[key] for key in ('complete', 'exhaustive') if key in value]
                complete = bool(declarations) and all(flag is True for flag in declarations)
                for category, resources in groups.items():
                    scopes.append({"system": ALIASES.get(system, system), "category": category, "scope": collection, "resources": resources, "evidence_id": meta["file_id"], "captured_at": meta["captured_at"], "observed_at": observed or meta["captured_at"], "complete": complete})
            for key, child in value.items():
                if key == "service_exports" and isinstance(child, dict):
                    for service, export in child.items():
                        walk(export, service, "", observed)
                elif isinstance(child, (dict, list)):
                    walk(child, system, collection or (key if key != "records" else ""), observed, key)
        elif isinstance(value, list):
            for child in value:
                walk(child, system, collection, observed, parent_key)
    walk(obj)
    return observations, scopes


def category_for_table(name: str) -> str:
    name = name.lower()
    for token, category in [("tombstone", "ACCOUNT_TOMBSTONE"), ("deleted_customer", "ACCOUNT_TOMBSTONE"), ("audit", "SECURITY_AUDIT_LOG"), ("retained_order", "LEGAL_HOLD_RECORD"), ("legal", "LEGAL_HOLD_RECORD"), ("connector", "DATA_FLOW"), ("backup", "BACKUP_ARCHIVE"), ("restore", "BACKUP_ARCHIVE"), ("legacy_contact", "SECONDARY_IDENTIFIER"), ("secondary_identifier", "SECONDARY_IDENTIFIER"), ("analytics", "ANALYTICS_PROFILE"), ("telemetry", "PRODUCT_TELEMETRY"), ("search", "SEARCH_INDEX_ENTRY"), ("attachment", "SUPPORT_ATTACHMENT"), ("support", "SUPPORT_MESSAGE"), ("export", "USER_EXPORT"), ("marketing", "MARKETING_PROFILE"), ("email_delivery", "EMAIL_DELIVERY_LOG"), ("cache", "CACHE_ENTRY"), ("profile", "USER_PROFILE")]:
        if token in name:
            return category
    return ""


def parse_sql(text: str, meta: dict):
    observations, scopes = [], []
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.enable_load_extension(False)
    denied = {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
    def authorize(action, arg1, arg2, database, source):
        if action in denied:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and str(arg2).lower() in {'load_extension', 'readfile', 'writefile'}:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_PRAGMA and str(arg1).lower() != 'foreign_keys':
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    db.set_authorizer(authorize)
    try:
        db.executescript(text)
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        declared = None
        if 'snapshot_scope' in tables:
            declared = {row['origin_system']: row['captured_at'] for row in db.execute('SELECT * FROM snapshot_scope')}
        generic_groups = set()
        generic_tables = []
        table_groups = {}
        for table in tables:
            if table == "snapshot_scope":
                continue
            quoted = '"' + table.replace('"', '""') + '"'
            records = [dict(row) for row in db.execute("SELECT * FROM " + quoted)]
            category = category_for_table(table)
            table_system = SYSTEM_FOR_CATEGORY.get(category, "")
            groups = defaultdict(set)
            # The schema, rather than row presence, establishes an empty replica table.
            is_generic = bool(re.search(r'CREATE\s+TABLE\s+["`\[]?' + re.escape(table) + r'\b[^;]*\brecord_json\b', text, re.I | re.S))
            if is_generic:
                generic_tables.append(table)
            for row in records:
                if "record_json" in row:
                    record = json.loads(row["record_json"])
                    collection = row.get("collection_name", table)
                    system = row.get("origin_system", "")
                else:
                    record, collection, system = row, table, table_system
                scope_time = declared.get(system or table_system, meta['captured_at']) if declared is not None else meta['captured_at']
                observation = make_observation(record, meta, system, collection, scope_time, table)
                if observation:
                    observations.append(observation)
                    groups[(observation.system, observation.category)].add(observation.resource)
            if category and table_system and (declared is None or table_system in declared):
                groups.setdefault((table_system, category), set())
            table_groups[table] = groups
            if is_generic:
                generic_groups.update(groups)
        for table in generic_tables:
            for group in generic_groups:
                table_groups[table].setdefault(group, set())
        for table, groups in table_groups.items():
            for (system, group_category), resources in groups.items():
                if declared is not None and system not in declared:
                    continue
                observed = declared.get(system, meta['captured_at']) if declared is not None else meta['captured_at']
                scopes.append({"system": system, "category": group_category, "scope": table, "resources": resources, "evidence_id": meta["file_id"], "captured_at": meta["captured_at"], "observed_at": observed, "complete": True})
    finally:
        db.close()
    return observations, scopes


def parse_log(text: str, meta: dict):
    observations, traces = [], {}
    pair_pattern = re.compile(r'(\w+)=("(?:\\.|[^"\\])*"|\S+)')
    for line_number, line in enumerate(text.splitlines(), 1):
        time_match = re.match(r"(\d{4}-\d\d-\d\dT[\d:.]+Z)", line)
        if not time_match:
            continue
        observed = time_match[1]
        rest = line[len(observed):].strip()
        data = {}
        if rest.startswith("{"):
            try:
                data = json.loads(rest)
            except json.JSONDecodeError:
                continue
        else:
            for key, value in pair_pattern.findall(rest):
                if value.startswith('"'):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        value = value.strip('"')
                data[key] = value
            if "message" in data:
                for key, value in pair_pattern.findall(str(data["message"])):
                    data[key] = value.strip('"')
            bracket = re.match(r"\[\w+\]\s+\[([^]]+)\]\s+\[([^]]+)\]\s+(\w+):", rest)
            pipe = re.match(r'\|\s*\w+\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\w+)\s*\|', rest)
            syslog = re.match(r"<\d+>\d+\s+\S+\s+(\S+)\s+(\S+)\s+-\s+-", rest)
            if bracket:
                data.update(service=bracket[1], trace_id=bracket[2], event=bracket[3])
            elif pipe:
                data.update(service=pipe[1], trace_id=pipe[2], event=pipe[3])
            elif syslog:
                data.setdefault("service", syslog[1]); data.setdefault("trace_id", syslog[2])
        trace_id = data.get("trace_id", data.get("requestId", ""))
        event_data = dict(data)
        if trace_id:
            # Identity/search context belongs to the trace. Outcomes belong only to
            # their event: a cache miss must never become a primary-store miss.
            service = data.get('service', data.get('function', data.get('system', '')))
            previous = traces.setdefault((service, trace_id), {})
            context_keys = IDENTIFIER_KEYS | {'resource_id', 'service', 'system', 'system_id', 'function'}
            previous.update({key: value for key, value in data.items() if key in context_keys})
            data = {**previous, **data}
            data['_trace_context_keys'] = sorted(set(previous) - set(event_data))
        resource = data.get("resource_id", "")
        event = str(data.get("event", ""))
        if not resource or event.endswith("_started") or event in {"cache_lookup", "connection_acquired", "consumer_lag", "thumbnail_failed", "deletion_marker_check"}:
            continue
        if not any(key in event_data for key in ("rows", "result", "state", "enabled", "restore_allowed", "matched_value", "pii_detected", "email", "requester_email", "record_type", "integrity_check", "decision", "deletion_block", "eligible", "available", "message_text", "direct_identifiers")):
            continue
        system = data.get("system", data.get("service", data.get("function", "")))
        collection = event + " " + str(data.get("source", ""))
        _, category = resource_kind(str(resource), collection, data.get('record_type', data.get('category', '')))
        # Search keys remain available for ownership joins while the payload's
        # own contents determine whether identifiers remain stored.
        data['state'] = infer_state(event_data, category)
        data["observed_at"] = observed
        data["line_number"] = line_number
        copy_scope = str(data.get('scope', ''))
        if data.get('service') == 'support_replica':
            copy_scope = 'support_replica'
        observation = make_observation(data, meta, system, collection, observed, copy_scope)
        if observation:
            # The stored trace context supports attribution, while this event's
            # own payload alone establishes whether identifiers remain stored.
            observation.state = data['state']
            observations.append(observation)
    return observations, []


class EvidenceStore:
    def __init__(self, observations=None, scopes=None, activities=None):
        self.observations = observations or []
        self.scopes = scopes or []
        self.activities = activities or []
        self.media = []
        self.hydrated_media = set()
        self.media_reinspection_facts = {}
        self.reinspected_media = set()
        self.by_resource = defaultdict(list)
        self.refresh()

    def refresh(self):
        self.by_resource.clear()
        for observation in self.observations:
            self.by_resource[observation.resource].append(observation)


def hydrate_media(store: EvidenceStore, meta: dict, result: dict) -> list[Observation]:
    """Validate extracted facts and attach the source manifest's provenance.

    This accepts facts from a genuine extraction response, never output steps or
    case decisions. In particular, model-supplied citations cannot replace the
    source file ID or capture time. The caller must not invoke it for pending jobs.
    """
    if not isinstance(result, dict) or set(result) != {'records'} or not isinstance(result['records'], list):
        raise ValueError('Media extraction requires a structured records array')
    required = {'system_id', 'resource_id', 'record_type', 'observed_at', 'state', 'identifiers', 'notes'}
    states = {'PRESENT', 'ABSENT', 'REDACTED', 'ANONYMIZED', 'ACTIVE', 'DISABLED', 'BLOCKED'}
    captured = timestamp(meta['captured_at'])
    if captured.tzinfo is None:
        raise ValueError('Media capture timestamp must include a timezone')
    hydrated = []
    for record in result['records']:
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError('Media record fields differ from the extraction schema')
        if any(not isinstance(record[field], str) for field in required - {'identifiers'}):
            raise ValueError('Media record fields must match their declared string types')
        if record['record_type'] not in CATEGORIES or record['state'] not in states:
            raise ValueError('Media extraction contains an unknown category or state')
        if not re.fullmatch(r'[A-Za-z0-9_.:-]+', record['resource_id']):
            raise ValueError('Media extraction contains an invalid resource ID')
        system = ALIASES.get(record['system_id'], record['system_id'])
        source_title = None
        if not system.strip():
            raise ValueError('Media extraction requires a system ID or visible service title')
        if system not in KNOWN_SYSTEMS:
            # Product screens often identify a team or console, not its internal
            # service. The exact resource prefix and policy category can still
            # establish the canonical service without another model request.
            source_title = system
            inferred_system, _ = resource_kind(record['resource_id'])
            category_system = SYSTEM_FOR_CATEGORY.get(record['record_type'])
            manifest_origin = ALIASES.get(meta.get('origin', ''), meta.get('origin', ''))
            if manifest_origin in KNOWN_SYSTEMS:
                system = manifest_origin
            elif inferred_system and (category_system == inferred_system or record['record_type'] == 'SECONDARY_IDENTIFIER'):
                system = inferred_system
            elif not inferred_system and category_system and record['record_type'] != 'SECONDARY_IDENTIFIER':
                system = category_system
            else:
                raise ValueError('Media service title has no unambiguous grounded system mapping')
        if not isinstance(record['identifiers'], list) or not all(isinstance(value, str) for value in record['identifiers']):
            raise ValueError('Media identifiers must be strings')
        if not isinstance(record['notes'], str) or not isinstance(record['observed_at'], str):
            raise ValueError('Media notes and observation timestamp must be strings')
        observed_at = record['observed_at'] or meta['captured_at']
        if timestamp(observed_at).tzinfo is None:
            raise ValueError('Media observation timestamp must include a timezone')
        data = {**record, '_media': True, '_manifest_origin': meta.get('origin', '')}
        if source_title is not None:
            data['source_system_title'] = source_title
        state = record['state']
        if record['record_type'] not in {'DATA_FLOW', 'BACKUP_ARCHIVE'} and state in {'ACTIVE', 'DISABLED', 'BLOCKED'}:
            state = 'PRESENT'
        hydrated.append(Observation(system, record['resource_id'], record['record_type'], state, meta['file_id'], meta['captured_at'], observed_at, {norm(value) for value in record['identifiers'] if has_value(value)}, data, ''))
    # Hydrating the same genuine response twice is repeatable; reject all bad
    # records before changing a store used by a later audit.
    store.observations[:] = [o for o in store.observations if not (o.evidence_id == meta['file_id'] and o.data.get('_media'))]
    store.observations.extend(hydrated)
    store.hydrated_media.add(meta['file_id'])
    store.refresh()
    return hydrated


def _review_catalog(context):
    if isinstance(context, list):
        events, cutoff = context, None
    elif isinstance(context, dict):
        events, cutoff = context.get('activities', []), context.get('cutoff')
    else:
        raise ValueError('Reinspection catalog context must contain participant activities')
    if not isinstance(events, list):
        raise ValueError('Reinspection activities must be a list')
    catalog = []
    for event in events:
        if not isinstance(event, dict) or event.get('event_type') != 'LINK_RESOURCE_IDENTITY':
            continue
        when = timestamp(event['event_time'])
        if cutoff and when > timestamp(cutoff):
            continue
        if not event.get('resource_id') or not event.get('target_system'):
            continue
        aliases = set(re.findall(r'\(([^()]+)\)', event.get('details', '')))
        aliases.add(event['resource_id'])
        catalog.append((event, aliases))
    return catalog


def _review_field_name(value):
    return re.sub(r'[^a-z0-9]', '', value.casefold())


def retention_timestamp(value):
    try:
        return timestamp(value)
    except ValueError:
        match = re.fullmatch(r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s+(\d{2}):?(\d{2})\s+UTC', value.strip())
        bounds = retention_date_bounds(match[1]) if match else None
        if not bounds:
            raise ValueError('Retention timestamp is not explicit and zoned')
        return timestamp(f"{bounds['date']}T{match[2]}:{match[3]}:00Z")


def retention_date_bounds(value: str) -> dict | None:
    """Bound a source date without pretending its timezone or time is known.

    A retention date can denote any instant on that civil day. Modern civil
    timezone offsets range from UTC-12 to UTC+14, so the complete UTC interval
    spans more than one day. These are precision bounds, not observed events.
    """
    year = month = day = None
    iso = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', value.strip())
    if iso:
        year, month, day = map(int, iso.groups())
    else:
        text = re.fullmatch(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', value.strip())
        months = {name: number for number, names in enumerate([
            ('jan', 'january'), ('feb', 'february'), ('mar', 'march'), ('apr', 'april'),
            ('may',), ('jun', 'june'), ('jul', 'july'), ('aug', 'august'),
            ('sep', 'sept', 'september'), ('oct', 'october'), ('nov', 'november'), ('dec', 'december')], 1) for name in names}
        if text and text[2].casefold() in months:
            day, month, year = int(text[1]), months[text[2].casefold()], int(text[3])
    if year is None:
        return None
    try:
        calendar_midnight = datetime(year, month, day, tzinfo=timezone.utc)
        lower = calendar_midnight - timedelta(hours=14)
        upper = calendar_midnight + timedelta(days=1, hours=12) - timedelta(microseconds=1)
    except (ValueError, OverflowError):
        return None
    return {'date': calendar_midnight.date().isoformat(),
            'lower': lower.isoformat().replace('+00:00', 'Z'),
            'upper': upper.isoformat().replace('+00:00', 'Z')}


def _review_state(record, category, stored, uncertainties):
    """Derive policy-relevant state only from what this reviewed row displays."""
    stable_names = {'userid', 'subjectreference', 'subjectref', 'customerreference', 'customerkey', 'stablereference', 'internaluserid'}
    required_direct = {'name', 'email', 'phone', 'emailhash'}
    direct_aliases = {'fullname': 'name', 'displayname': 'name', 'requestername': 'name',
                      'owneremail': 'email', 'customeremail': 'email', 'requesteremail': 'email',
                      'ownerphone': 'phone', 'customerphone': 'phone', 'requesterphone': 'phone'}
    removed, direct_visible, stable_visible = set(), False, False
    config = {}
    config_names = {'enabled': 'enabled', 'active': 'active', 'restoreallowed': 'restore_allowed',
                    'deletionblock': 'deletion_block', 'eligible': 'eligible'}
    for field in record['stored_fields']:
        key = _review_field_name(field['field_name'])
        canonical = direct_aliases.get(key, key)
        visibility, role = field['visibility'], field['identifier_role']
        if field['field_name'] in CORRELATION_KEYS:
            continue
        quote = field['source_quote'].strip()
        if visibility == 'VALUE' and quote and has_value(field['value']):
            config[config_names.get(key, field['field_name'])] = field['value']
            if role == 'STABLE_REFERENCE' or key in stable_names:
                stable_visible = True
            elif role == 'DIRECT_IDENTIFIER' or canonical in required_direct:
                direct_visible = True
        if canonical in required_direct and visibility in {'BLANK', 'REDACTED'} and quote:
            removed.add(canonical)
    complete = (record['field_coverage'] == 'COMPLETE' and
                record['direct_fields_coverage'] in {'explicitly_redacted', 'all_field_values_shown'})
    state = record['state']
    if state == 'ABSENT':
        scope = record['scope']
        exact_lookup = scope['kind'] == 'SINGLE_RECORD' and scope['subject_bound'] and bool(scope['source_quote'].strip())
        exhaustive = scope['kind'] == 'COMPLETE_COLLECTION' and scope['completeness'] == 'COMPLETE' and bool(scope['source_quote'].strip())
        if not (exact_lookup or exhaustive):
            uncertainties.append('A partial or unscoped view does not establish absence of this record')
            return 'UNKNOWN'
    if category == 'ACCOUNT_TOMBSTONE':
        if direct_visible:
            return 'PRESENT'
        if stable_visible and complete and required_direct <= removed:
            return 'REDACTED'
        if not stable_visible:
            uncertainties.append('The reviewed tombstone does not establish a stored stable subject reference')
        if not (complete and required_direct <= removed):
            uncertainties.append('The reference view does not explicitly establish removal of name, email, phone and email hash; fields not shown are not redaction proof')
        return 'UNKNOWN'
    if category in {'ANALYTICS_PROFILE', 'PRODUCT_TELEMETRY'}:
        if stored:
            return 'PRESENT'
        if complete and required_direct <= removed and not stable_visible and state == 'ANONYMIZED':
            return 'ANONYMIZED'
        if state == 'ABSENT':
            return 'ABSENT'
        uncertainties.append('The reviewed analytics view does not establish complete irreversible removal of identifying links')
        return 'UNKNOWN'
    if category in {'SUPPORT_MESSAGE', 'EMAIL_DELIVERY_LOG'}:
        if direct_visible:
            return 'PRESENT'
        if complete and required_direct <= removed:
            return 'REDACTED'
        if state != 'ABSENT':
            uncertainties.append('The reviewed record does not show sufficient direct-field coverage to establish exposed PII or completed redaction')
            return 'UNKNOWN'
    if category in {'DATA_FLOW', 'BACKUP_ARCHIVE'}:
        # Explicit displayed configuration has priority over a status caption.
        if config:
            inferred = infer_state({**config, 'state': state}, category)
            if inferred in {'ACTIVE', 'DISABLED', 'BLOCKED'}:
                return inferred
        if state in {'ACTIVE', 'DISABLED', 'BLOCKED'}:
            return state
        if state == 'PRESENT':
            if category == 'BACKUP_ARCHIVE':
                uncertainties.append('Archive existence, health, retention or past restore events do not establish current restore authorization for this subject')
            else:
                uncertainties.append('Connector existence does not establish its current enabled/disabled configuration')
            return 'UNKNOWN'
    if category == 'UNKNOWN' or state == 'UNKNOWN':
        uncertainties.append('The reviewed source does not establish a policy category and current record state')
        return 'UNKNOWN'
    if category not in {'DATA_FLOW', 'BACKUP_ARCHIVE'} and state in {'ACTIVE', 'DISABLED', 'BLOCKED'}:
        return 'PRESENT'
    return state


def _attachment_document_records(meta, records):
    """Keep an uploaded document's body in its explicitly described file scope.

    A ticket reference printed in an uploaded PDF is not a read of the live
    ticket. Require a unique continued attachment-properties section, customer
    upload provenance, a quoted parent reference and the same document title.
    Ambiguous/multiple files and independent ticket views are left untouched.
    The original provider facts remain intact in the reinspection audit trail.
    """
    if Path(meta.get('file_path', '')).suffix.casefold() != '.pdf':
        return records, []
    attachments = [record for record in records
                   if record['record_type'] == 'SUPPORT_ATTACHMENT' and record['category'] == 'record']
    if len(attachments) != 1:
        return records, []
    attachment = attachments[0]
    filename = attachment['literal_reference'] or attachment['resource_id']
    section = attachment['scope']['source_quote'].casefold()
    customer_upload = any(_review_field_name(field['field_name']) == 'uploader'
                          and field['visibility'] == 'VALUE' and field['value'].casefold() == 'customer'
                          and 'customer' in field['source_quote'].casefold()
                          for field in attachment['stored_fields'])
    if not (attachment['state'] == 'PRESENT' and filename.casefold().endswith('.pdf') and 'continued' in section
            and 'attachment properties' in section and customer_upload):
        return records, []
    parents = {ref['literal_reference'] for ref in attachment['related_references']
               if ref['relationship'] == 'parent_ticket' and ref['literal_reference']
               and ref['literal_reference'] in ref['source_quote']}
    bodies = [record for record in records if record['record_type'] == 'SUPPORT_MESSAGE'
              and record['category'] == 'record' and record['state'] == 'PRESENT'
              and record['literal_reference'] in parents
              and record['source_system_label']
              and record['source_system_label'] == attachment['source_system_label']
              and record['scope']['label'] == record['source_system_label']]
    if len(bodies) != 1:
        return records, []
    body = bodies[0]
    # Accept a full, literally quoted technical support key, including a key in
    # a compound displayed reference. Never derive one from the customer ID.
    keys = {token for field in body['stored_fields'] if field['visibility'] == 'VALUE'
            for token in re.findall(r'(?<![\w.-])support_[A-Za-z0-9]+(?![\w.-])', field['value'])
            if token in field['source_quote']}
    if len(keys) != 1:
        return records, []
    resource = next(iter(keys))
    correction = {'role': 'uploaded_document_body', 'body_reference': body['literal_reference'],
                  'attachment_reference': filename, 'resource_id': resource,
                  'reason': 'The continued customer-upload attachment section scopes the document body; its ticket reference does not establish separate live-ticket state'}
    merged = {**attachment, 'resource_id': resource, 'state': 'PRESENT',
              'stored_fields': [*body['stored_fields'], *attachment['stored_fields']],
              'direct_identifiers_visible': [*body['direct_identifiers_visible'], *attachment['direct_identifiers_visible']],
              'context_identifiers': [*body['context_identifiers'], *attachment['context_identifiers']],
              'events': [*body['events'], *attachment['events']],
              'uncertainties': list(dict.fromkeys([*body['uncertainties'], *attachment['uncertainties']])),
              '_source_scope_correction': correction, '_document_body_source_fact': body}
    return [merged if record is attachment else record for record in records if record is not body], [correction]


def hydrate_media_reinspection(store: EvidenceStore, meta: dict, result: dict, catalog_context) -> list[Observation]:
    """Hydrate source-fact reviews without converting unshown fields into proof.

    Catalog events resolve literal business aliases, never invent a visible ID.
    Their availability times remain separate provenance for cutoff-aware callers.
    Only explicitly reviewed rows from this file supersede earlier extraction.
    """
    from model_client import validate_media_reinspection
    validate_media_reinspection(result)
    capture = timestamp(meta['captured_at'])
    catalog = _review_catalog(catalog_context)
    hydrated, superseded, unresolved, diagnostics = [], [], [], []
    remove_ids = set()
    records, scope_corrections = _attachment_document_records(meta, result['records'])
    for record in records:
        literal = record['literal_reference'] or record['resource_id']
        if not literal:
            unresolved.append(record)
            continue
        # A document/ticket number can label a view of a separately printed
        # technical record. Bind only one quoted reference of the same type;
        # business IDs and unrelated navigation links cannot supply this key.
        quoted = [(field['value'], field['source_quote']) for field in record['stored_fields']
                  if field['visibility'] == 'VALUE']
        quoted += [(ref['literal_reference'], ref['source_quote']) for ref in record['related_references']]
        technical = {value for value, quote in quoted if value and value in quote and
                     resource_kind(value)[1] == record['record_type'] and record['record_type'] != 'UNKNOWN'}
        primary_reference = next(iter(technical)) if len(technical) == 1 else ''
        source_key = primary_reference or record['resource_id'] or literal
        # A quoted retention instruction for an ordinary business reference is
        # a planning constraint, not evidence of a new privacy-resource type.
        # Preserve it without inventing a legal hold, export, or profile.
        retention_fields = [field for field in record['stored_fields']
                            if _review_field_name(field['field_name']) in {'retainuntil', 'retentionuntil'}
                            and field['visibility'] == 'VALUE' and field['source_quote'].strip()]
        if (record['record_type'] == 'UNKNOWN' and record['category'] == 'record'
                and record['reference_kind'] in {'BUSINESS_ALIAS', 'RESOURCE_ID'}
                and not resource_kind(source_key)[1] and retention_fields
                and not record['direct_identifiers_visible']):
            unresolved.append({**record, '_role': 'retained_business_constraint',
                               '_reason': 'Retain the supplied business record; no supplied privacy-resource category or destructive operation is established'})
            continue
        candidates = []
        for event, aliases in catalog:
            if literal not in aliases and source_key not in aliases:
                continue
            origin = ALIASES.get(meta.get('origin', ''), meta.get('origin', ''))
            system = ALIASES.get(event['target_system'], event['target_system'])
            if origin in KNOWN_SYSTEMS and origin != system:
                continue
            candidates.append(event)
        targets = {(ALIASES.get(e['target_system'], e['target_system']), e['resource_id']) for e in candidates}
        uncertainties = list(dict.fromkeys([*result['uncertainties'], *record['uncertainties']]))
        if len(targets) > 1:
            uncertainties.append('The literal source reference has ambiguous participant catalog mappings')
            candidates = []
        mapped = min(candidates, key=lambda e: (timestamp(e['event_time']), e.get('activity_id', ''))) if candidates else None
        resource = mapped['resource_id'] if mapped else source_key
        category = record['record_type']
        if mapped:
            system = ALIASES.get(mapped['target_system'], mapped['target_system'])
            _, canonical_category = resource_kind(resource)
            category = canonical_category or category
        else:
            explicit = ALIASES.get(record['system_id'], record['system_id'])
            origin = ALIASES.get(meta.get('origin', ''), meta.get('origin', ''))
            if explicit in KNOWN_SYSTEMS:
                system = explicit
            elif origin in KNOWN_SYSTEMS:
                system = origin
            else:
                # A producing portal/brand is provenance, not a new service.
                system = resource_kind(resource)[0] or SYSTEM_FOR_CATEGORY.get(category, 'unknown')
        source_aliases = {literal, resource}
        if record.get('_source_scope_correction'):
            source_aliases.add(record['_source_scope_correction']['body_reference'])
        matching = [o for o in store.observations if o.evidence_id == meta['file_id'] and o.data.get('_media') and
                    (o.resource in source_aliases or o.data.get('source_resource_alias') in source_aliases
                     or o.data.get('_source_resource_alias') in source_aliases)]
        for reference in record['related_references']:
            linked_literal = reference['literal_reference']
            if not linked_literal or linked_literal in {literal, resource} or not reference['source_quote'].strip():
                continue
            # A navigation link is not a separately observed order, finance or
            # support record. Correct only the first-pass pseudo-observations;
            # a prior focused review of actual contents is independent evidence.
            for old in store.observations:
                if old.evidence_id != meta['file_id'] or not old.data.get('_media') or old.data.get('_media_reinspection'):
                    continue
                if (old.resource == linked_literal or old.data.get('source_resource_alias') == linked_literal or
                        old.data.get('_source_resource_alias') == linked_literal):
                    if id(old) not in remove_ids:
                        superseded.append({'resource_id': old.resource, 'literal_reference': linked_literal,
                                           'role': 'linked_reference',
                                           'reason': 'The focused source review identifies this literal only as a linked business reference, not an observation of underlying record contents'})
                    remove_ids.add(id(old))
        if record['category'] == 'linked_reference':
            for old in matching:
                remove_ids.add(id(old))
                superseded.append({'resource_id': old.resource, 'literal_reference': literal,
                                   'role': 'linked_reference', 'reason': 'A navigation/business reference does not show the underlying record contents, category or current state'})
            continue
        for old in matching:
            remove_ids.add(id(old))
            superseded.append({'resource_id': old.resource, 'literal_reference': literal,
                               'role': record['category'], 'reason': 'Superseded by a focused source-fact review of this same visible row'})
        stored = set()
        for field in record['stored_fields']:
            if field['visibility'] == 'VALUE' and field['source_quote'].strip() and has_value(field['value']) and field['identifier_role'] in {'DIRECT_IDENTIFIER', 'STABLE_REFERENCE'} and field['field_name'] not in CORRELATION_KEYS:
                stored.add(norm(field['value']))
        context = {norm(field['value']) for field in record['context_identifiers'] if has_value(field['value'])}
        if record['stable_reference']:
            context.add(norm(record['stable_reference']))
        observed = meta['captured_at']
        if record['time_basis'] == 'EXPLICIT_SNAPSHOT_TIME':
            label = record['observation_time_label'].casefold()
            if any(word in label for word in ('modified', 'updated', 'created', 'refreshed', 'expires')):
                uncertainties.append('A lifecycle/history timestamp was supplied as an observation time; current view remains observed at manifest capture')
            else:
                observed = record['observed_at']
        if result['captured_at'] != meta['captured_at']:
            uncertainties.append('Reviewed capture timestamp differs from manifest; manifest capture was preserved')
        event_times = [event['timestamp'] for event in record['events'] if event['timestamp']]
        if record['last_modified_at']:
            event_times.append(record['last_modified_at'])
        if any(timestamp(value) > capture for value in event_times):
            uncertainties.append('A displayed lifecycle/event timestamp is later than manifest capture; both times are preserved without repair')
        state = _review_state(record, category, stored, uncertainties)
        if len(targets) > 1:
            state = 'UNKNOWN'
        policy_fields = {}
        for field in record['stored_fields']:
            if field['visibility'] != 'VALUE' or not field['source_quote'].strip():
                continue
            key = _review_field_name(field['field_name'])
            if key in {'retentionuntil', 'retainuntil'} and has_value(field['value']):
                try:
                    exact_retention = retention_timestamp(field['value'])
                except ValueError:
                    policy_fields['retention_until_raw'] = field['value']
                    bounds = retention_date_bounds(field['value'])
                    if bounds:
                        policy_fields['retention_until_date'] = bounds['date']
                        policy_fields['retention_until_bounds'] = {key: bounds[key] for key in ('lower', 'upper')}
                        policy_fields['_retention_precision_note'] = 'Source date only; UTC bounds cover any time on the stated day across civil offsets UTC-12 through UTC+14'
                    else:
                        uncertainties.append('The displayed retention-until value is preserved but is not a supported complete timestamp or date; no timezone or boundary was invented')
                        if category == 'SECURITY_AUDIT_LOG':
                            state = 'UNKNOWN'
                else:
                    policy_fields['retention_until'] = (field['value'] if re.match(r'^\d{4}-\d{2}-\d{2}[T ]', field['value'])
                                                        else exact_retention.isoformat())
            elif key == 'legalholdactive':
                flag = field['value'].strip().casefold()
                if flag in {'true', '1', 'active'}:
                    policy_fields['legal_hold_active'] = True
                elif flag in {'false', '0', 'inactive'}:
                    policy_fields['legal_hold_active'] = False
        data = {**record, '_media': True, '_media_reinspection': True,
                '_primary_source_reference': primary_reference,
                '_manifest_origin': meta.get('origin', ''), '_source_resource_alias': literal,
                '_source_fact_record': record, '_source_observed_at': record['observed_at'],
                'identifiers': sorted(stored), '_uncertainties': list(dict.fromkeys(uncertainties)), **policy_fields}
        if record['system_id'] and record['system_id'] != system:
            data['source_system_title'] = record['system_id']
        if uncertainties:
            data['_uncertainty'] = '; '.join(dict.fromkeys(uncertainties))
        if mapped:
            data['_catalog_event_time'] = mapped['event_time']
            data['_catalog_activity_id'] = mapped.get('activity_id', '')
        scopes = {o.scope for o in matching}
        physical_scope = next(iter(scopes)) if len(scopes) == 1 else ''
        hydrated.append(Observation(system, resource, category, state, meta['file_id'], meta['captured_at'], observed,
                                   stored | context, data, physical_scope))
        diagnostics.extend(uncertainties)
    store.observations[:] = [o for o in store.observations if id(o) not in remove_ids]
    store.observations.extend(hydrated)
    store.media_reinspection_facts[meta['file_id']] = {**result, 'superseded_rows': superseded,
                                                    'unmapped_records': unresolved,
                                                    'source_scope_corrections': scope_corrections,
                                                    'diagnostics': list(dict.fromkeys(diagnostics))}
    store.reinspected_media.add(meta['file_id'])
    store.refresh()
    return hydrated


def load_evidence(dataset: Path, model_client=None) -> EvidenceStore:
    store = EvidenceStore(activities=read_csv(dataset / "system_activity.csv"))
    for meta in read_csv(dataset / "evidence_files.csv"):
        path = (dataset / meta["file_path"]).resolve()
        if not path.is_relative_to(dataset.resolve()):
            raise ValueError("Evidence path escapes dataset")
        if path.suffix == ".json":
            observations, scopes = parse_json(json.loads(path.read_text(encoding="utf-8")), meta)
        elif path.suffix == ".sql":
            observations, scopes = parse_sql(path.read_text(encoding="utf-8"), meta)
        elif path.suffix == ".log":
            observations, scopes = parse_log(path.read_text(encoding="utf-8"), meta)
        elif path.suffix == ".txt":
            observations, scopes = [], []
            for line in path.read_text(encoding="utf-8").splitlines():
                fields = [x.strip() for x in line.removeprefix("- ").split("|")]
                if len(fields) == 6 and re.match(r"\d{4}-", fields[0]):
                    record = dict(zip(["observed_at", "system", "resource_id", "record_type", "result", "subject_reference"], fields))
                    observation = make_observation(record, meta)
                    if observation:
                        observations.append(observation)
        elif path.suffix in {".png", ".pdf"}:
            store.media.append((path, meta))
            observations, scopes = [], []
        else:
            raise ValueError(f"Unsupported evidence format: {path.suffix}")
        store.observations.extend(observations)
        store.scopes.extend(scopes)
    store.refresh()
    return store
