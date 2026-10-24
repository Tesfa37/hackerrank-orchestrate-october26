"""Report original and organizer-exclusion coverage without changing predictions."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_core import read_csv
from evaluation.exclusions import load_guidance, run_views

ROOT = Path(__file__).resolve().parents[2]
GROUP_LABELS = {
    'negative_scope_without_owned_resource': 'Missing eligible account ownership edge despite negative scopes',
    'primary_evidence_after_cutoff': 'Primary evidence excluded by capture/observation cutoff',
    'no_primary_evidence_or_scope': 'Missing eligible direct primary proof or complete scope',
    'media_field_coverage_uncertainty': 'Unresolved image/PDF field or configuration proof',
}


def render(views, guidance):
    original, adjusted = views['original'], views['excluding_confirmed']
    lines = ['# Organizer guidance and full-run coverage', '',
             f"Recorded {guidance['recorded_date']}. Source: {guidance['source']}.", '',
             '- Confirmed evaluation exclusions: `case_39`, `case_55`.',
             '- Other invalid cases will be excluded, but no complete list was provided. No other exclusion is assumed.',
             '- Evaluation uses only the evidence supplied in the repository. No dataset change was announced.',
             '- The existing 518-row CSV requirement remains pending explicit clarification about excluded rows.', '',
             'Exclusions affect this evaluation view only. The predictor still processes all 518 requests, applies the same cutoff and policy checks, and neither reads this guidance nor assigns answers to excluded cases. No final output.csv has been produced.', '',
             '| View | Returned / requests | Coverage | Blocked |', '| --- | ---: | ---: | ---: |']
    for label, view in [('Original contract', original), ('Excluding confirmed cases only', adjusted)]:
        rate = f"{view['coverage_rate']:.4%}" if view['coverage_rate'] is not None else 'N/A'
        lines.append(f"| {label} | {view['covered_cases']}/{view['requested_cases']} | {rate} | {len(view['blocked_case_ids'])} |")
    excluded_blocked = sorted(set(original['blocked_case_ids']) - set(adjusted['blocked_case_ids']))
    lines += ['', f"Excluded returned requests: {', '.join(adjusted['excluded_returned_ids']) or 'none'}. "
              f"Excluded blocked requests: {', '.join(excluded_blocked) or 'none'}. "
              'Both numerator and denominator are recomputed from case IDs. An exclusion is not evidence of the correct deletion status.', '',
              '| Root cause | Original blockers | Blockers excluding confirmed cases |', '| --- | ---: | ---: |']
    for group in sorted(original['blocker_group_counts']):
        lines.append(f"| {GROUP_LABELS.get(group, group)} | {original['blocker_group_counts'][group]} | {adjusted['blocker_group_counts'].get(group, 0)} |")
    lines += ['', 'The media group originally contains two distinct cases: `case_46` lacks explicit tombstone direct-field removal proof; `case_55` lacks current subject-specific restore authorization. Only the latter has a confirmed exclusion. Permitted stable user_id alone is not exposed PII.', '',
              f"After confirmed exclusions, {len(adjusted['blocked_case_ids'])} blockers remain, grouped above. "
              'The unspecified invalid-case guidance does not establish that these are all invalid.', '',
              '## Remaining blocked request IDs after confirmed exclusions', '',
              ', '.join(adjusted['blocked_case_ids']) + '.', '',
              'See [blocker_report.md](blocker_report.md) for original diagnostics and representative exact missing proofs. Full-run coverage is not accuracy: no full-set expected answers were used. Neither exclusion appears among the 32 public sample IDs, so their scoring denominator remains 32.', '',
              'Reproduce offline after regenerating the partial full run and blocker diagnostics:', '',
              '```sh', '.venv/bin/python code/evaluation/coverage_report.py', '```', '',
              'Paid API budget: $0. This report performs no API calls and changes no credentials, participant data or predictions.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', type=Path, default=ROOT/'.cache/full_predictions_partial.csv')
    parser.add_argument('--blockers', type=Path, default=ROOT/'.cache/blocker_report.json')
    parser.add_argument('--report', type=Path, default=ROOT/'code/evaluation/organizer_guidance.md')
    parser.add_argument('--json', type=Path, default=ROOT/'.cache/coverage_views.json', dest='json_path')
    args = parser.parse_args()
    allowed = (ROOT/'code/evaluation/organizer_guidance.md').resolve()
    inputs = {args.predictions.resolve(), args.blockers.resolve()}
    for path, suffix in ((args.report, '.md'), (args.json_path, '.json')):
        target = path.resolve()
        if (target in inputs or target.suffix != suffix or target.is_relative_to(ROOT/'dataset')
                or (target.is_relative_to(ROOT) and target != allowed and not target.is_relative_to(ROOT/'.cache'))):
            parser.error('Use the designated coverage report, .cache, or external report paths')
    guidance = load_guidance()
    views = run_views([r['case_id'] for r in read_csv(ROOT/'dataset/deletion_requests.csv')],
                      [r['case_id'] for r in read_csv(args.predictions)],
                      json.loads(args.blockers.read_text(encoding='utf-8')),
                      guidance['confirmed_excluded_case_ids'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render(views, guidance), encoding='utf-8')
    args.json_path.write_text(json.dumps(views, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({name: {key: value for key, value in view.items() if not key.endswith('_ids')}
                      for name, view in views.items()}, indent=2))


if __name__ == '__main__':
    main()
