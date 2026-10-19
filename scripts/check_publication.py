"""Check staged source for private artifacts and common credential patterns.

This is a defense in depth check, not a guarantee. Prints paths/rule names only.
Run from any directory in a Git checkout after explicitly staging reviewed files.
"""
import re
import subprocess
import sys
from pathlib import PurePosixPath

DENIED_PARTS = {'settings', 'exports', 'automation', 'archive', 'image-history',
    '.local', '.runtime', '.build', '.venv', '.build-venv', '.webview-session', '__pycache__', 'node_modules', 'dist', 'build'}
DENIED_NAMES = {'desktop-install.json', 'desktop-status.json', 'source.json', 'article.json', 'materials.json', 'status.json'}
PATTERNS = {
    'provider-token': re.compile(r'\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'wechat-account-id': re.compile(r'\bwx[0-9a-f]{16}\b'),
    'personal-local-path': re.compile(r'(?i)\b[A-Z]:[/\\](?:Users|DataAPPs|user)[/\\]'),
    'credential-literal': re.compile(r'''(?i)(?:api[_-]?key|appsecret|access[_-]?token|password)\s*[=:]\s*["'][A-Za-z0-9_+/=-]{24,}["']'''),
}


def issues(path, data):
    parts=PurePosixPath(path).parts
    problems=[]
    if path.startswith('paper-studio/'):
        if any(x in DENIED_PARTS or x.startswith('implement-stage') for x in parts): problems.append('private-runtime-directory')
        if 'data' in parts or PurePosixPath(path).name in DENIED_NAMES: problems.append('private-runtime-file')
        if PurePosixPath(path).suffix.lower() in {'.pdf','.zip','.log','.dpapi','.db','.sqlite','.pem','.key','.exe','.dll','.pyc'}: problems.append('private-or-build-artifact')
    if any(x.startswith('.env') for x in parts): problems.append('environment-file')
    # Checked-in icons are permitted; text rules do not decode arbitrary binaries.
    try: text=data.decode('utf-8')
    except UnicodeDecodeError: return problems
    for name,pattern in PATTERNS.items():
        if pattern.search(text): problems.append(name)
    return problems


def git(*args):
    return subprocess.check_output(['git',*args])


def main():
    names=git('diff','--cached','--name-only','--diff-filter=ACMR','-z').decode('utf8').split('\0')
    failures=[]
    for path in filter(None,names):
        for rule in issues(path,git('show',':'+path)):failures.append((path,rule))
    for path,rule in failures:print(f'{path}: {rule}')
    if failures:
        print(f'Publication check blocked: {len(failures)} findings (values omitted).');return 1
    print(f'Publication pattern check passed: {len([n for n in names if n])} staged files. Review the staged diff as well.')
    return 0


if __name__=='__main__':sys.exit(main())
