"""Deterministic, cutoff-aware policy reasoning over participant observations.

Activities establish identity/resource links, never successful deletion state.
Missing state evidence raises an error rather than creating a fourth verdict.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from functools import lru_cache

from audit_core import Observation, STATES, Subject, norm, serialize_steps, timestamp
from evidence import ALIASES, EvidenceStore, identifiers, resource_kind, stored_identifiers


class InsufficientEvidence(ValueError):
    """An authorized request cannot yet be assessed from grounded evidence."""


def _copy(scope: str) -> str:
    """Separate source scopes unless the evidence explicitly equates them."""
    return scope or "unscoped-readback"


_LINK_KEYS = {"source_resource_id", "target_resource_id", "upstream_resource_id", "downstream_resource_id",
              "parent_resource_id", "dependent_resource_ids", "depends_on", "resource_ids"}
_TOKEN = re.compile(r"[\w@.+-]+")
_ASCII_CASE_EQUIVALENTS = str.maketrans({"İ": "i", "ı": "i", "ſ": "s", "K": "k"})
DELETABLE_CATEGORIES = {"USER_PROFILE", "SECONDARY_IDENTIFIER", "SEARCH_INDEX_ENTRY", "CACHE_ENTRY",
                        "USER_EXPORT", "MARKETING_PROFILE", "SUPPORT_ATTACHMENT"}


def _links(value):
    result = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _LINK_KEYS:
                if isinstance(child, str):
                    result.add(child)
                elif isinstance(child, list):
                    result.update(item for item in child if isinstance(item, str))
            if isinstance(child, (dict, list)):
                result.update(_links(child))
    elif isinstance(value, list):
        for child in value:
            result.update(_links(child))
    return result


def _store_cache(store):
    # Hydration replaces media observations and calls refresh(). Tracking both
    # record references and rebuilt resource lists also invalidates views after
    # an in-place record edit followed by the store's normal refresh contract.
    # Activity fields used for matching are cheap to compare directly.
    signature = (id(store.observations), tuple(id(o) for o in store.observations),
                 id(store.scopes), tuple(id(scope) for scope in store.scopes),
                 id(store.activities), tuple((id(event), event.get("event_time"), event.get("event_type"),
                                             event.get("resource_id"), event.get("target_system"), event.get("details"))
                                            for event in store.activities),
                 tuple(id(records) for records in store.by_resource.values()))
    cached = getattr(store, "_reasoning_cache", None)
    if cached is None or cached["signature"] != signature:
        # Keep old objects alive until invalidation; otherwise Python can reuse
        # the identity of a just-cleared list during a same-size refresh.
        cached = {"signature": signature, "views": {},
                  "references": (tuple(store.observations), tuple(store.scopes), tuple(store.activities),
                                 tuple(store.by_resource.values()))}
        store._reasoning_cache = cached
    return cached


def _index(store):
    cache = _store_cache(store)
    if "index" in cache:
        return cache["index"]
    observation_ids, activity_ids = defaultdict(set), defaultdict(set)
    detail_tokens, detail_exact = defaultdict(set), defaultdict(set)
    by_resource, scopes = defaultdict(list), defaultdict(list)
    available = {}
    for number, observation in enumerate(store.observations):
        available[id(observation)] = observation.available_at
        by_resource[observation.resource].append(observation)
        for identifier in observation.identifiers:
            observation_ids[identifier].add(number)
    event_times = []
    catalog = []
    for number, event in enumerate(store.activities):
        event_times.append(timestamp(event["event_time"]))
        for identifier in identifiers(event):
            activity_ids[identifier].add(number)
        details = event.get("details", "")
        detail_exact[norm(details)].add(number)
        for token in _TOKEN.findall(details):
            detail_tokens[token.translate(_ASCII_CASE_EQUIVALENTS).lower()].add(number)
        if event.get("event_type") == "LINK_RESOURCE_IDENTITY":
            catalog.append(number)
    for scope in store.scopes:
        scopes[(scope["system"], scope["category"])].append(
            (scope, max(timestamp(scope["captured_at"]), timestamp(scope["observed_at"]))))
    # An edge exists exactly when both endpoint observations have become
    # eligible. The earliest such pair is sufficient for an undirected link.
    graph = defaultdict(dict)
    for observation in store.observations:
        origin = (observation.system, observation.resource)
        for resource in _links(observation.data):
            for other in by_resource.get(resource, ()):
                target = (other.system, other.resource)
                when = max(available[id(observation)], available[id(other)])
                previous = graph[origin].get(target)
                if previous is None or when < previous:
                    graph[origin][target] = graph[target][origin] = when
    cache["index"] = {"observation_ids": observation_ids, "activity_ids": activity_ids,
                      "detail_tokens": detail_tokens, "detail_exact": detail_exact,
                      "event_times": event_times, "catalog": catalog, "available": available,
                      "by_resource": by_resource, "scopes": scopes, "graph": graph}
    return cache["index"]


def _canonical_view(store, cutoff):
    """Resolve business keys only through explicit eligible catalog aliases."""
    from dataclasses import replace
    cache = _store_cache(store)
    index = _index(store)
    limit = timestamp(cutoff)
    eligible_aliases = set()
    for number in index["catalog"]:
        if index["event_times"][number] > limit:
            continue
        event = store.activities[number]
        for alias in re.findall(r"\(([^()]+)\)", event.get("details", "")):
            if alias != event["resource_id"]:
                eligible_aliases.add((alias, event["target_system"], event["resource_id"]))
    view_key = frozenset(eligible_aliases)
    if view_key in cache["views"]:
        return cache["views"][view_key]
    aliases = defaultdict(set)
    for alias, system, resource in eligible_aliases:
        aliases[alias].add((system, resource))
    observations = []
    changed = False
    for observation in store.observations:
        targets = aliases.get(observation.resource, set())
        # A filename/key reused in another source is not the same resource.
        targets = {(system, resource) for system, resource in targets
                   if observation.data.get("_media") and
                   (observation.data.get("_manifest_origin") == system or
                    resource_kind(resource)[1] == observation.category)}
        if len(targets) > 1:
            raise InsufficientEvidence("Ambiguous participant catalog alias")
        if targets:
            system, resource = next(iter(targets))
            _, category = resource_kind(resource)
            category = category or observation.category
            data = {**observation.data, "source_resource_alias": observation.resource}
            if category != observation.category:
                data["_category_reclassified"] = True
            observations.append(replace(observation, system=system, resource=resource, category=category, data=data))
            changed = True
        else:
            observations.append(observation)
    view = EvidenceStore(observations, store.scopes, store.activities) if changed else store
    cache["views"][view_key] = view
    return view


@lru_cache(maxsize=1024)
def _mention_patterns(identifiers):
    return tuple(re.compile(r"(?<![\w@.+-])" + re.escape(identifier) + r"(?![\w@.+-])", re.I)
                 for identifier in identifiers)


def _mentions(value: str, subject: Subject) -> bool:
    text = norm(value)
    if text in subject.identifiers:
        return True
    # Boundary checks prevent e.g. user_1 joining user_10 or email substrings.
    return any(pattern.search(value) for pattern in _mention_patterns(tuple(sorted(subject.identifiers))))


def _stable_owners(value) -> set[str]:
    owners = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "user_id" and isinstance(child, str) and child.strip():
                owners.add(norm(child))
            elif key in {"customer_reference", "subject_reference", "subject_ref"} and isinstance(child, str) and child.startswith("user_"):
                owners.add(norm(child))
            if isinstance(child, (dict, list)):
                owners.update(_stable_owners(child))
    elif isinstance(value, list):
        for child in value:
            owners.update(_stable_owners(child))
    return owners


def related_resources(subject: Subject, store, cutoff: str) -> set[tuple[str, str]]:
    index = _index(store)
    limit = timestamp(cutoff)
    observation_numbers, event_numbers = set(), set()
    needs_regex_scan = False
    for identifier in subject.identifiers:
        observation_numbers.update(index["observation_ids"].get(identifier, ()))
        event_numbers.update(index["activity_ids"].get(identifier, ()))
        event_numbers.update(index["detail_exact"].get(identifier, ()))
        if identifier.isascii() and _TOKEN.fullmatch(identifier):
            event_numbers.update(index["detail_tokens"].get(identifier.lower(), ()))
        else:
            # Non-token or non-ASCII identifiers retain the original regex
            # semantics. Common email/user/hash/phone keys use indexed tokens.
            needs_regex_scan = True
    if needs_regex_scan:
        event_numbers.update(number for number, event in enumerate(store.activities)
                             if _mentions(event.get("details", ""), subject))
    found = set()
    for number in observation_numbers:
        observation = store.observations[number]
        if index["available"][id(observation)] <= limit:
            found.add((observation.system, observation.resource))
    for number in event_numbers:
        if index["event_times"][number] > limit:
            continue
        event = store.activities[number]
        if identifiers(event) & subject.identifiers or _mentions(event.get("details", ""), subject):
            system = ALIASES.get(event["target_system"], event["target_system"])
            if event.get("resource_id"):
                found.add((system, event["resource_id"]))
    # Traverse only explicit resource relationships, never resource-like tokens
    # in prose, filenames, or identifiers belonging to unrelated people.
    queue = list(found)
    while queue:
        for target, when in index["graph"].get(queue.pop(), {}).items():
            if when <= limit and target not in found:
                found.add(target)
                queue.append(target)
    return found


def select_states(subject: Subject, store, cutoff: str) -> list[Observation]:
    """Select the last eligible direct observation for every linked physical copy.

    An explicit exhaustive snapshot can establish absence for a *known* resource.
    A missing identifier search and an unscoped list cannot do so.
    """
    store = _canonical_view(store, cutoff)
    index = _index(store)
    limit = timestamp(cutoff)
    related = related_resources(subject, store, cutoff)
    if not related:
        raise InsufficientEvidence("No eligible evidence links this subject to a resource")
    selected = []
    for system, resource in sorted(related):
        eligible = [o for o in index["by_resource"].get(resource, ())
                    if o.system == system and index["available"][id(o)] <= limit]
        if not eligible:
            # An explicitly owned key can be absent from its first complete
            # snapshot. A prior positive row is not a prerequisite for a
            # negative read, but the key and collection coverage must be real.
            _, category = resource_kind(resource)
            if category in DELETABLE_CATEGORIES:
                for scope, available_at in index["scopes"].get((system, category), ()):
                    if available_at <= limit and resource in scope["resources"]:
                        raise InsufficientEvidence(f"Snapshot lists linked resource {system}/{resource} without parsed state evidence")
                    if scope.get("complete", False) and available_at <= limit and resource not in scope["resources"]:
                        eligible.append(Observation(system, resource, category, "ABSENT", scope["evidence_id"],
                                                    scope["captured_at"], scope["observed_at"], set(),
                                                    {"_negative_scope": scope["scope"]}, scope["scope"]))
            if not eligible:
                raise InsufficientEvidence(f"Linked resource {system}/{resource} has no eligible state evidence")
        categories = {o.category for o in eligible}
        if len(categories) != 1:
            # A generic support prefix may have been refined to an attachment or
            # identifier by a source that actually specifies its record type.
            refined = categories - {"SUPPORT_MESSAGE"}
            if len(refined) != 1:
                raise InsufficientEvidence(f"Conflicting categories for {system}/{resource}")
            category = refined.pop()
        else:
            category = next(iter(categories))
        copies = defaultdict(list)
        for observation in eligible:
            copies[_copy(observation.scope)].append(observation)
        for scope, available_at in index["scopes"].get((system, category), ()):
            if available_at <= limit and resource in scope["resources"] and not any(
                    observation.scope == scope["scope"] and observation.evidence_id == scope["evidence_id"]
                    for observation in eligible):
                raise InsufficientEvidence(f"Snapshot lists linked resource {system}/{resource} without parsed state evidence for scope {scope['scope']}")
            if not scope.get("complete", False):
                continue
            if available_at > limit:
                continue
            physical = _copy(scope["scope"])
            # Only compare a snapshot to a copy that has already been linked.
            # This does not invent a new subject-specific resource or replica.
            if physical not in copies or resource in scope["resources"]:
                continue
            # Matching a service/category alone does not establish collection
            # coverage. In particular, a filtered list cannot erase a known row.
            covered = set(scope.get("covers_scopes", ())) | {scope["scope"]}
            if not any(observation.scope in covered for observation in copies[physical]):
                continue
            if category not in DELETABLE_CATEGORIES:
                continue
            copies[physical].append(Observation(system, resource, category, "ABSENT", scope["evidence_id"],
                                               scope["captured_at"], scope["observed_at"], set(), {}, scope["scope"]))
        for observations in copies.values():
            latest_time = max(timestamp(o.observed_at) for o in observations)
            latest = [o for o in observations if timestamp(o.observed_at) == latest_time]
            states = {o.state for o in latest}
            if len(states) > 1:
                raise InsufficientEvidence(f"Conflicting simultaneous states for {system}/{resource}")
            # Stable tie breaking makes filesystem and input ordering irrelevant.
            winner = sorted(latest, key=lambda o: (timestamp(o.captured_at), o.evidence_id))[0]
            owners = _stable_owners(winner.data)
            if owners and subject.user_id not in owners:
                raise InsufficientEvidence(f"Conflicting stable ownership for {system}/{resource}")
            if winner.category != category:
                from dataclasses import replace
                winner = replace(winner, category=category)
            selected.append(winner)
    return selected


def _policy(observation: Observation, rules: list[dict], cutoff: str) -> str:
    category = observation.category
    if category == "DATA_FLOW":
        return "DISABLE"
    actions = {rule["required_action"] for rule in rules if rule["data_category"] == category}
    if len(actions) != 1:
        raise InsufficientEvidence(f"Missing or ambiguous policy for {category}")
    action = actions.pop()
    # Never convert an expired retention condition into permission to delete.
    until = observation.data.get("retention_until", "")
    if category == "SECURITY_AUDIT_LOG" and until and timestamp(until) < timestamp(cutoff):
        raise InsufficientEvidence("Expired retention period has no supplied replacement policy")
    bounds = observation.data.get("retention_until_bounds")
    if category == "SECURITY_AUDIT_LOG" and bounds:
        lower, upper, audit = timestamp(bounds["lower"]), timestamp(bounds["upper"]), timestamp(cutoff)
        if lower > upper:
            raise InsufficientEvidence("Invalid date-only retention bounds")
        if audit > upper:
            raise InsufficientEvidence("Expired retention period has no supplied replacement policy")
        if audit >= lower:
            raise InsufficientEvidence("Audit falls inside the date-only retention boundary; exact time or timezone is required")
    if category == "LEGAL_HOLD_RECORD" and observation.data.get("legal_hold_active") is False:
        raise InsufficientEvidence("Inactive legal hold has no supplied replacement policy")
    return "BLOCK" if category == "BACKUP_ARCHIVE" else action


def _treatment(observation: Observation, action: str):
    """Return violation finding, remediation and required verification operations."""
    state = observation.state
    mapping = {
        "DELETE": ("ABSENT", "REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT"),
        "REDACT": ("REDACTED", "REPORT_EXPOSED_PII", "REDACT_RECORD", "VERIFY_RECORD_REDACTED"),
        "ANONYMIZE": ("ANONYMIZED", "REPORT_EXPOSED_PII", "ANONYMIZE_RECORD", "VERIFY_RECORD_ANONYMIZED"),
        "DISABLE": ("DISABLED", "REPORT_ACTIVE_DATA_FLOW", "DISABLE_DATA_FLOW", "VERIFY_DATA_FLOW_DISABLED"),
        "BLOCK": ("BLOCKED", "REPORT_RESTORE_RISK", "BLOCK_RESTORE", "VERIFY_RESTORE_BLOCKED"),
        "RETAIN": ("PRESENT", None, None, "VERIFY_RECORD_PRESENT"),
    }
    if action not in mapping:
        raise InsufficientEvidence(f"Unsupported policy action {action}")
    expected, finding, remediation, verification = mapping[action]
    if state == expected:
        return None, None, verification
    if action == "RETAIN" or state == "ABSENT" and action != "DELETE":
        raise InsufficientEvidence(f"Required retained resource {observation.resource} is missing")
    if action == "BLOCK" and state == "PRESENT":
        raise InsufficientEvidence("Archive existence does not establish whether current subject restore access is allowed or blocked")
    supported = {"DELETE": {"PRESENT"}, "REDACT": {"PRESENT"}, "ANONYMIZE": {"PRESENT"},
                 "DISABLE": {"ACTIVE"}, "BLOCK": {"ACTIVE"}}
    if state not in supported.get(action, set()):
        raise InsufficientEvidence(f"Unsupported {observation.category} state {state}")
    return finding, remediation, verification


def audit_request(request: dict, subject: Subject | None, store, rules: list[dict], intent: bool,
                  *, full_subject_audit: bool = False) -> dict:
    if type(intent) is not bool:
        raise ValueError("Deletion intent must be a validated boolean")
    if not intent:
        return {"case_id": request["case_id"], "deletion_status": "NOT_APPLICABLE", "steps_json": "[]"}
    if subject is None:
        raise InsufficientEvidence("An authorized request requires a resolved subject")
    observations = select_states(subject, store, request["audit_at"])
    return plan_observations(request, subject, observations, rules, full_subject_audit=full_subject_audit)


def plan_observations(request, subject, observations, rules, *, full_subject_audit=False):
    """Plan only supplied eligible states; discovery/uncertainty is the caller's responsibility."""
    if not observations:
        raise InsufficientEvidence('No eligible resource states support a nonempty plan')
    for observation in observations:
        if not observation.eligible(request['audit_at']):
            raise InsufficientEvidence('An observation is available after the audit cutoff')
        if observation.state == "UNKNOWN":
            raise InsufficientEvidence(observation.data.get("_uncertainty", "Record treatment is not established by the visible evidence"))
        if observation.data.get("_category_reclassified"):
            raise InsufficientEvidence("Catalog alias changes the extracted record category; treatment needs source verification")
        if observation.category == "ACCOUNT_TOMBSTONE" and subject.user_id not in stored_identifiers(observation.data):
            raise InsufficientEvidence("Tombstone lacks evidence that its required stable subject reference is preserved")
    treatment = [(o, *_treatment(o, _policy(o, rules, request["audit_at"]))) for o in observations]
    incomplete = any(finding for _, finding, _, _ in treatment)
    if full_subject_audit and not incomplete:
        primary_absence = any(o.category == "USER_PROFILE" and o.system == "account_service" and
                              o.state == "ABSENT" and "replica" not in o.scope.casefold() for o in observations)
        tombstone = any(o.category == "ACCOUNT_TOMBSTONE" and o.state == "REDACTED" and
                        subject.user_id in stored_identifiers(o.data) for o in observations)
        if not (primary_absence or tombstone):
            raise InsufficientEvidence("Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone")
    steps = []
    def step(o, phase, operation, citation):
        steps.append({"phase": phase, "system_id": o.system, "resource_id": o.resource,
                      "operation": operation, "state": STATES[operation], "evidence_id": citation})
    # A noncompliant copy takes precedence over compliance of a different copy.
    # The output contract has one logical resource identifier; retain the full
    # physical-copy inventory internally and emit one required final treatment.
    ordered = sorted(treatment, key=lambda t: (t[1] is None, t[0].system, t[0].resource,
                                              timestamp(t[0].observed_at), t[0].evidence_id))
    for observation, finding, remediation, verification in ordered:
        if finding:
            step(observation, "FINDING", finding, observation.evidence_id)
            step(observation, "REMEDIATION", remediation, "")
        step(observation, "VERIFICATION", verification, "" if incomplete else observation.evidence_id)
    serialized = serialize_steps(steps)
    return {"case_id": request["case_id"], "deletion_status": "INCOMPLETE" if incomplete else "COMPLETE",
            "steps_json": json.dumps(serialized, ensure_ascii=False, separators=(",", ":"))}
