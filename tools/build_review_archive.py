"""Build the incomplete review bundle from tracked code, excluding private state."""
from pathlib import Path
import os
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    names = subprocess.check_output(['git', 'ls-files', '-z', 'code'], cwd=ROOT).decode().split('\0')
    files = [Path(name) for name in names if name]
    secrets = [value.encode() for key, value in os.environ.items()
               if any(token in key.upper() for token in ('API_KEY', 'TOKEN', 'SECRET', 'PASSWORD')) and len(value) >= 16]
    for file in files:
        if any(part in {'.cache', '.venv', '__pycache__', 'dataset'} for part in file.parts) or file.name.startswith('.env'):
            raise ValueError('Private state must not be archived')
        if any(secret in (ROOT/file).read_bytes() for secret in secrets):
            raise ValueError('Injected credential found in archive source')
    required = {Path('code/evaluation/evaluation_report.md'), Path('code/evaluation/usage_report.md')}
    if not required <= set(files):
        raise ValueError('Required evaluation reports are missing')
    readme = (ROOT/'code/README.md').read_text(encoding='utf-8')
    for target in ('ARCHITECTURE.md', 'INTERVIEW_NOTES.md', 'FRESH_ENVIRONMENT.md', 'evaluation/archive_verification.md'):
        readme = readme.replace(f']({target})', f'](code/{target})')
    checkpoint = ('# Development review bundle\n\n'
                  'This archive contains runnable code and review documentation, not a completed submission. '
                  'No output.csv is included inside the code archive. A separately supplied output.csv may be an explicitly assumption-dependent prediction candidate; it is not a completed strict audit. Read code/evaluation/approach_comparison.md and its assumptions ledger. The original518-row requirement and excluded-row format remain pending organizer clarification.\n\n'
                  'Supply the original participant dataset alongside code/. Start with README.md and code/FRESH_ENVIRONMENT.md. '
                  'Read evaluation/archive_verification.md for actually tested versus documented behavior. '
                  'Partial predictions, detailed diagnostics and the transcript are preserved separately as review artifacts. '
                  'No dataset, credentials, model caches, virtual environment or nested archive is included. Paid API budget:$0.\n')
    target = ROOT/'code.zip'
    temporary = target.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(ROOT/file, file.as_posix())
        archive.writestr('README.md', readme)
        archive.writestr('REVIEW_CHECKPOINT.md', checkpoint)
        # Keep the requested evaluation/report paths at the archive root too,
        # while retaining the runnable repository layout and its commands.
        for file in files:
            if file.parent == Path('code/evaluation') and file.suffix == '.md':
                archive.write(ROOT/file, file.relative_to('code').as_posix())
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise ValueError('Archive integrity check failed')
    temporary.replace(target)
    print(f'Built review archive: {target.stat().st_size} bytes')


if __name__ == '__main__':
    main()
