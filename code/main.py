"""Run the deletion audit without consulting expected sample answers."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from audit_core import IdentityIndex, read_csv, validate_citations, write_output
from evidence import hydrate_media, hydrate_media_reinspection, load_evidence
from model_client import GeminiClient, MissingModelResult, classify_requests, extract_media, extract_media_aliases, reinspect_media
from reasoning import InsufficientEvidence, audit_request

ROOT = Path(__file__).resolve().parents[1]


def usage_markdown(usage, count, completed, samples):
    label = "public sample development" if samples else "full evaluation dataset"
    values = {"Provider": usage["provider"], "Model": usage["model"],
              "Requested cases": count, "Completed cases": completed,
              "Referenced production model calls": usage["referenced_calls"],
              "New model calls in this process": usage["new_calls_this_process"],
              "Cached responses reused": usage.get("cached_results_reused", 0),
              "Production attempts including retries": usage.get("production_attempts", usage["referenced_calls"]),
              "Attempts with unavailable provider usage": usage.get("attempts_with_unavailable_usage", 0),
              "Input tokens": usage["input_tokens"], "Output tokens": usage["output_tokens"],
              "Thinking tokens": usage["thinking_tokens"], "Total tokens": usage["total_tokens"],
              "Total tokens per requested case": round(usage["total_tokens"] / count, 3) if count else 0,
              "Configured billed API budget (USD)": 0, "Paid fallback": "disabled"}
    text = "# Model usage\n\n" + f"Run: {label}. Completed {completed}/{count} cases.\n\n"
    text += "| Measure | Value |\n| --- | --- |\n" + "".join(f"| {key} | {value} |\n" for key, value in values.items())
    text += "\nToken totals include genuine response caches referenced by this run; cache reuse is not zero production work. "
    text += "New calls and reused responses are recorded separately in the machine-readable run ledger. "
    text += "Token sums include reported usage only; attempts without usage are unknown and are not silently estimated as zero. "
    text += "The participant configured a Gemini Free Tier project with billing disabled. "
    text += "Estimated billed cost is $0 total and $0 per case on that configuration; no billing settings are changed by the program.\n"
    if completed != count:
        text += "\nThis run did not produce a complete final submission. Its usage is development/attempt usage, not a successful final-dataset run.\n"
    return text


def run(args) -> int:
    root = ROOT
    dataset = args.dataset.resolve()
    request_path = dataset / ("sample_deletion_requests.csv" if args.samples else "deletion_requests.csv")
    requests = read_csv(request_path)
    if args.case:
        wanted = set(args.case)
        requests = [row for row in requests if row["case_id"] in wanted]
        if {row["case_id"] for row in requests} != wanted:
            raise ValueError("Unknown requested case ID")
    if not requests:
        raise ValueError("No requests selected")
    output = args.output or root / ("sample_predictions.csv" if args.samples else "output.csv")
    if args.case and args.output is None:
        raise ValueError("--case requires an explicit --output path for development results")
    if args.partial and args.output is None:
        raise ValueError("--partial requires an explicit --output path for development results")
    output = output.resolve()
    if args.partial and output == root / "output.csv":
        raise ValueError("Partial development results cannot replace the final root output.csv")
    if args.case and output == root / "output.csv":
        raise ValueError("Selected development cases cannot replace the final root output.csv")
    if args.samples and output == root / "output.csv":
        raise ValueError("Sample development results cannot replace the final root output.csv")
    if output.is_relative_to(dataset):
        raise ValueError("Output must not overwrite participant input data")
    if output.suffix.lower() != ".csv":
        raise ValueError("Prediction output must be a CSV file")
    if args.usage_report:
        args.usage_report = args.usage_report.resolve()
        if args.usage_report.is_relative_to(dataset):
            raise ValueError("Usage report must not overwrite participant input data")
        if args.usage_report == output or args.usage_report == root / "output.csv":
            raise ValueError("Usage report must not overwrite prediction output")
        if args.usage_report.suffix.lower() != ".md":
            raise ValueError("Usage report must be a Markdown file")
        if args.usage_report.is_relative_to(root) and args.usage_report.exists():
            permitted = root / "code" / "evaluation" / "usage_report.md"
            if args.usage_report != permitted and not args.usage_report.is_relative_to(root / ".cache"):
                raise ValueError("Usage report must not overwrite existing repository files")
    store = load_evidence(dataset)
    client = GeminiClient(root, prepare=args.prepare, offline=args.offline)
    reinspection = getattr(args, "reinspect_media", False)
    catalog = [event for event in store.activities if event.get("event_type") == "LINK_RESOURCE_IDENTITY"]
    aliases = set()
    subject_ids = {row["user_id"] for row in read_csv(dataset / "user_identities.csv")}
    for event in store.activities:
        if event.get("event_type") == "LINK_RESOURCE_IDENTITY":
            aliases.update(value for value in re.findall(r"\(([^()]+)\)", event.get("details", ""))
                           if value != event.get("resource_id") and value not in subject_ids)
    errors, rows, intents = [], [], {}
    # Generate every required extraction job even when one preparation stage has
    # no cached result yet. Preparation never fabricates a verdict.
    for offset in range(0, len(requests), 40):
        batch = requests[offset:offset + 40]
        try:
            intents.update(classify_requests(client, batch))
        except MissingModelResult as error:
            errors.append({"stage": "intent", "case_ids": [row["case_id"] for row in batch], "error": str(error)})
            if not args.offline and not args.prepare:
                # Reuse any already available media after a live prerequisite
                # fails, but do not issue further calls to that failed service.
                client.offline = True
                break
    for path, meta in store.media:
        try:
            result = extract_media(client, path, meta)
            if result is not None:
                if not result["records"] and aliases:
                    fallback = extract_media_aliases(client, path, meta, sorted(aliases))
                    if fallback is not None:
                        result = fallback
                hydrate_media(store, meta, result)
            if reinspection:
                # The model receives source facts only. Canonical catalog IDs
                # are joined deterministically after extraction, with their own
                # availability times, so they cannot become invented UI facts.
                reviewed = reinspect_media(client, path, meta, [])
                if reviewed is not None:
                    hydrate_media_reinspection(store, meta, reviewed, catalog)
        except (MissingModelResult, ValueError) as error:
            errors.append({"stage": "media", "evidence_id": meta["file_id"], "error": str(error)})
            if not args.offline and not args.prepare:
                # A missing quota/credential/network prerequisite applies to the
                # remaining jobs too. Resume from genuine caches after fixing it.
                break
    if args.prepare:
        queue = client.write_jobs()
        print(f"Prepared {len(client.pending)} missing model jobs: {queue}")
        return 0
    identities = IdentityIndex(read_csv(dataset / "user_identities.csv"), read_csv(dataset / "user_audit_log.csv"))
    rules = read_csv(dataset / "deletion_rules.csv")
    for request in requests:
        case_id = request["case_id"]
        try:
            if case_id not in intents:
                raise InsufficientEvidence("No validated request intent result")
            intent = intents[case_id]
            # Non-deletion requests need neither identity joins nor state checks.
            if not intent:
                rows.append(audit_request(request, None, store, rules, False))
                continue
            if len(store.hydrated_media) != len(store.media):
                raise InsufficientEvidence("Required business-artifact extraction is incomplete")
            if reinspection and len(store.reinspected_media) != len(store.media):
                raise InsufficientEvidence("Required source-fact media reinspection is incomplete")
            subject = identities.resolve(request["email"], request["audit_at"])
            rows.append(audit_request(request, subject, store, rules, intent, full_subject_audit=True))
        except (InsufficientEvidence, ValueError) as error:
            errors.append({"stage": "reasoning", "case_id": case_id, "error": str(error)})
    rows.sort(key=lambda row: row["case_id"])
    successful_ids = {row["case_id"] for row in rows}
    successful_requests = [row for row in requests if row["case_id"] in successful_ids]
    validate_citations(rows, successful_requests, read_csv(dataset / "evidence_files.csv"),
                       store.activities, read_csv(dataset / "user_audit_log.csv"), store.observations)
    label = "samples" if args.samples else "full"
    ledger = root / ".cache" / f"run_{label}.json"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    usage = client.usage()
    details = {"created_at": datetime.now(timezone.utc).isoformat(), "request_file": str(request_path),
               "requests": len(requests), "completed": len(rows), "errors": errors, "usage": usage,
               "observations": len(store.observations), "media_extracted": len(store.hydrated_media),
               "media_reinspected": len(store.reinspected_media),
               "media_reinspection_facts": store.media_reinspection_facts}
    ledger.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.usage_report:
        args.usage_report.parent.mkdir(parents=True, exist_ok=True)
        args.usage_report.write_text(usage_markdown(usage, len(requests), len(rows), args.samples), encoding="utf-8")
    if len(rows) != len(requests) and not args.partial:
        print(f"Audit incomplete: {len(rows)}/{len(requests)} cases resolved. Output was not written. Diagnostics: {ledger}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    # Write only fully validated results, and preserve an existing output if any
    # validation or extraction fails before this point.
    temporary = output.with_name(output.name + ".tmp")
    try:
        write_output(temporary, rows, successful_requests)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(rows)}/{len(requests)} cases to {output}. Diagnostics and usage: {ledger}")
    return 0 if len(rows) == len(requests) else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", action="store_true", help="Run the 32 public sample requests")
    parser.add_argument("--dataset", type=Path, default=ROOT / "dataset")
    parser.add_argument("--output", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare", action="store_true", help="Prepare missing model jobs without API calls")
    mode.add_argument("--offline", action="store_true", help="Use only genuine cached model responses")
    parser.add_argument("--case", action="append", help="Select a request for development; repeat for multiple cases")
    parser.add_argument("--partial", action="store_true", help="Save explicitly named partial development output; exits 2 if incomplete")
    parser.add_argument("--usage-report", type=Path)
    parser.add_argument("--reinspect-media", action="store_true", default=True,
                        help="Validate media field roles, scope and timestamps (enabled by default)")
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (OSError, ValueError, MissingModelResult) as error:
        print(f"Audit failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
