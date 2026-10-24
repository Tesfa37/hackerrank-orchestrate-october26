"""Public-reference mismatch review. Expected answers never enter prediction code."""
from pathlib import Path
from collections import Counter
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import timestamp, read_csv, IdentityIndex
from evidence import identifiers
from investigate import load_context
from reasoning import related_resources, _canonical_view

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ('phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id')


def step_differences(actual, expected):
    left = Counter(tuple(s[f] for f in FIELDS) for s in actual)
    right = Counter(tuple(s[f] for f in FIELDS) for s in expected)
    return [('missing', dict(zip(FIELDS, key))) for key, n in (right-left).items() for _ in range(n)] + [('extra', dict(zip(FIELDS, key))) for key, n in (left-right).items() for _ in range(n)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case')
    parser.add_argument('--mre-case01', action='store_true', help='Participant-file-only evidence check; requires no model caches')
    parser.add_argument('--report', type=Path, default=ROOT/'code/evaluation/sample_mismatch_review.md')
    args = parser.parse_args()
    target = args.report.resolve()
    if target.suffix != '.md' or target.is_relative_to(ROOT/'dataset') or (target.is_relative_to(ROOT) and target not in {ROOT/'code/evaluation/sample_mismatch_review.md', ROOT/'code/evaluation/case_01_mre.md'} and not target.is_relative_to(ROOT/'.cache')):
        parser.error('Use the designated review report, .cache, or an external Markdown path')
    if args.mre_case01:
        dataset = ROOT/'dataset'
        request = next(r for r in read_csv(dataset/'sample_deletion_requests.csv') if r['case_id']=='case_01')
        answer = next(r for r in read_csv(dataset/'sample_output.csv') if r['case_id']=='case_01')
        expected_step = json.loads(answer['steps_json'])[0]
        subject = IdentityIndex(read_csv(dataset/'user_identities.csv'), read_csv(dataset/'user_audit_log.csv')).resolve(request['email'], request['audit_at'])
        source = next(r for r in read_csv(dataset/'evidence_files.csv') if r['file_id']==expected_step['evidence_id'])
        key = expected_step['resource_id']
        claims = [r for r in read_csv(dataset/'system_activity.csv') if r['resource_id']==key and timestamp(r['event_time'])<=timestamp(request['audit_at'])]
        bridges = [r for r in claims if identifiers(r)&subject.identifiers]
        text = (dataset/source['file_path']).read_text()
        report = f"# case_01 minimal reproduction\n\nNo model cache or network is required. Expected key is read only in this evaluation module.\n\nSubject: {subject.user_id}; cutoff: {request['audit_at']}. Public reference requests {key} in {source['file_id']} ({source['file_path']}).\n\nLiteral account-key occurrences in cited snapshot: {text.count(key)}. Eligible activity claims naming key: {len(claims)}. Claims containing a grounded subject identifier: {len(bridges)}.\n\n"
        for claim in claims:
            report += f"- {claim['activity_id']}: {claim['event_time']}, {claim['event_type']}, {claim['details']}\n"
        report += '\nA resource-only deletion claim does not establish ownership or resulting state. The identity snapshot/history does not supply an account resource key. A complete negative snapshot cannot supply the missing subject/account association. Required proof is an eligible explicit association or keyed readback; the public reference itself and a user-ID suffix are not permitted substitutes.\n'
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text(report);print('Wrote',target);return
    requests, store, identities, history, rules, intents = load_context(ROOT, ROOT/'dataset', True, True)
    # Only this evaluation module reads public reference steps.
    expected = {r['case_id']: r for r in read_csv(ROOT/'dataset/sample_output.csv')}
    actual = {r['case_id']: r for r in read_csv(ROOT/'.cache/sample_predictions_partial.csv')}
    manifest = {r['file_id']: r for r in read_csv(ROOT/'dataset/evidence_files.csv')}
    diagnostics = {e['case_id']: e['error'] for e in json.loads((ROOT/'.cache/run_samples.json').read_text())['errors'] if 'case_id' in e}
    lines = ['# Public-sample mismatch review', '', 'Expected answers are confined to evaluation. This report never supplies identity edges, resource IDs or labels to the predictor. Missing/extra content ignores step numbering; exact sequence still includes numbering and order.', '', '| Case | Returned / expected status | Missing / extra steps |', '| --- | --- | --- |']
    tables = []
    for request in requests:
        cid = request['case_id']
        if args.case and cid != args.case:
            continue
        gold = json.loads(expected[cid]['steps_json'])
        predicted = json.loads(actual[cid]['steps_json']) if cid in actual else []
        differences = step_differences(predicted, gold)
        lines.append(f"| {cid} | {actual.get(cid, {}).get('deletion_status', 'unresolved')} / {expected[cid]['deletion_status']} | {sum(d=='missing' for d,s in differences)} / {sum(d=='extra' for d,s in differences)} |")
        subject = identities.resolve(request['email'], request['audit_at'])
        view = _canonical_view(store, request['audit_at'])
        owned = related_resources(subject, view, request['audit_at'])
        section = [f'## {cid}', '', f"Audit cutoff: `{request['audit_at']}`. " + diagnostics.get(cid, 'A row was returned; review the step-level discrepancies below.'), '', '| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |', '| --- | --- | --- | --- | --- |']
        finding_sources = {s['resource_id']:s['evidence_id'] for s in gold if s['phase']=='FINDING'}
        for direction, step in differences:
            resource = step['resource_id']; evidence = step['evidence_id'] or finding_sources.get(resource, '')
            obs = [o for o in view.observations if o.resource == resource and o.system == step['system_id']]
            eligible = [o for o in obs if o.eligible(request['audit_at'])]
            linked = (step['system_id'], resource) in owned
            sources = [f"{o.evidence_id}: {manifest[o.evidence_id]['file_path']} ({o.category}/{o.state}; {'eligible' if o.eligible(request['audit_at']) else 'after cutoff'})" for o in obs]
            if evidence in manifest:
                source = manifest[evidence]
                sources.insert(0, f"{evidence}: {source['file_path']}; capture {source['captured_at']}")
            activities = [e for e in store.activities if e.get('resource_id') == resource]
            if not sources:
                sources = [f"{e['activity_id']}: dataset/system_activity.csv ({e['event_type']}; event {e['event_time']}; operation claim, not state proof)" for e in activities[:2]]
            if direction == 'extra':
                if any(o.category == 'SUPPORT_MESSAGE' and manifest[o.evidence_id]['file_path'].endswith('.pdf') for o in eligible):
                    cause = 'Unresolved document-body versus live-ticket interpretation: a customer-upload PDF contains a ticket reference, but independent current message state and ticket/attachment identity are not established.'
                elif eligible and linked:
                    cause = 'Additional source-backed physical object omitted by the reference; its visible filename differs from the support attachment, so a same-object alias is unproven.'
                else:
                    cause = 'Service/category/citation or evidence-scope interpretation needs review.'
            elif obs and not eligible:
                cause = 'Timestamp exclusion: available source/capture/observation is after cutoff.'
            elif not linked:
                cause = 'Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency.'
            elif eligible:
                kinds = {o.category for o in eligible}
                action = {r['required_action'] for r in rules if r['data_category'] in kinds}
                if step['operation'] in {'DELETE_RECORD','VERIFY_RECORD_ABSENT','REPORT_REMAINING_RECORD'} and action & {'ANONYMIZE','REDACT','RETAIN'}:
                    cause = 'Reference operation conflicts with the supplied treatment for this source category: '+','.join(sorted(action))+'.'
                elif cid not in actual:
                    cause = 'Case held by another unresolved obligation; this independently supported step was not emitted as a partial case.'
                else:
                    cause = 'State/citation/scope or serialization discrepancy; inspect the listed source rather than substituting the reference label.'
            else:
                cause = 'Owned resource lacks eligible direct state or an applicable exhaustive negative snapshot.'
            section.append(f"| {direction} | {step['phase']} / {step['operation']} | {step['system_id']} / {resource} | {'; '.join(dict.fromkeys(sources)) or 'No matching direct source row found; reference citation alone is not a join.'} | {cause} |")
        if not differences:
            section.append('| none | Exact content match | — | — | Check exact sequence independently for numbering/order. |')
        tables.extend(section+[''])
    lines += ['']+tables
    lines += ['## Uploaded-document source scope', '',
              'The source-scoped attachment correction removes the separate live-ticket observation previously inferred from an uploaded PDF body. '
              'See [case_07_attachment_review.md](case_07_attachment_review.md) for the literal participant proof, generic correction conditions and remaining independent storage-object/account-proof mismatches. '
              'The original extraction records remain in the audit trail. Expected answers do not drive this correction.', '',
              'Confirmed organizer exclusions are recorded separately in [organizer_guidance.md](organizer_guidance.md). Neither confirmed ID is in this 32-sample set; all 32 remain in its coverage and accuracy denominators.', '']
    lines += ['## Finance-register interpretation', '', 'The five sample-specific holds came from treating ordinary ORD business references as new privacy-resource observations. The source explicitly says Retain until, but supplies no privacy-resource category. They are now retained as non-destructive business constraints in source facts, without inventing a legal hold or generating deletion actions. Known account/analytics/support resources and uncertain primary privacy records still undergo ordinary policy and uncertainty checks.', '', '## Completeness guard', '', 'A mandatory primary-account absence/tombstone anchor is not stated literally by the contract. It is an implementation safeguard for these whole-account deletion requests, preventing peripheral retained-audit evidence alone from proving all relevant copies treated. It is neither a necessary condition for every conceivable scoped audit nor sufficient proof of exhaustive discovery. The reviewed blocked account cases independently lack eligible exact resource ownership/state proof; removing the guard would emit a verdict without recovering their missing verification steps. Scoped engine fixtures deliberately do not require it. No guard was disabled to improve coverage.', '', '## Minimal reproduction: case_01', '', 'Run `.venv/bin/python code/evaluation/review_mismatches.py --case case_01 --report /tmp/case_01_review.md`. This evaluation-only reproduction reads the public reference, then searches actual participant observations and activity for its resource; it does not pass that resource to the predictor.', '', 'The reference requires account_001 / evidence_54. The SQL snapshot can establish scoped absence only after that account key is grounded. The participant activity names account_001 but does not identify the request subject; the subject identity snapshot supplies user_01, email, phone and hash without an account key. No eligible current/historical identifier bridges them. user_01 -> account_001 would be a suffix assumption, not an evidence join. Required missing proof: an eligible catalog/API/record association between the subject and account_001, or an authoritative keyed negative lookup containing both. The expected key cannot currently be grounded independently from supplied participant evidence. A negative snapshot alone does not manufacture that missing key.', '', 'This is a minimal evidence-consistency reproduction, not a generator/hidden-answer investigation. Participant inputs remain unchanged.']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Wrote',target)


if __name__=='__main__':
    main()
