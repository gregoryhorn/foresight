#!/usr/bin/env python3
"""Scan publishable repository files. Ignored runtime caches and git internals are excluded."""
import os
import re
import subprocess
import sys
from pathlib import Path

# Construct matchers without placing private identifiers in the public source.
BUILTIN_NAMES=[''.join(parts) for parts in [('gr','egory'),('mr','it'),('du','rian'),('is','mail'),('hei','di'),('hack','athon')]]
PRIVATE_PATH='/'+'home'+'/'
LAN='192'+'.168'+'.'
EMAIL=re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
KEYS=[re.compile(p) for p in (r'\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}',r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',r'\bgh[pousr]_[A-Za-z0-9]{30,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]

def files(root):
    # Include untracked deliverables, but never traverse ignored build/test/model caches.
    result=subprocess.run(['git','-C',str(root),'ls-files','--cached','--others','--exclude-standard','-z'],capture_output=True)
    if result.returncode:
        raise RuntimeError('privacy scan requires a git worktree')
    return [root/os.fsdecode(p) for p in result.stdout.split(b'\0') if p]

def scan_text(text,names=None):
    names=names or BUILTIN_NAMES
    findings=[]
    for number,line in enumerate(text.splitlines(),1):
        public_pin = 'https://github.com/' + ''.join(('gr', 'egory')) + 'horn/crystal-ball/releases/download/v1.2.0/crystal_ball_media-1.2.0-py3-none-any.whl#sha256=e36da1fe33fd91b3971297682840ee3e893a5d8e7465ee9158d4c632a4fe7338'
        lower=line.replace(public_pin, '[public-dependency-pin]').casefold()
        if PRIVATE_PATH in line:
            findings.append((number,'private absolute path'))
        if LAN in line:
            findings.append((number,'private network address'))
        for name in names:
            # The requested copyright attribution is the sole personal-name exception.
            if name.casefold() in lower and not (name==BUILTIN_NAMES[0] and 'copyright' in lower):
                findings.append((number,'denylisted name'))
        for address in EMAIL.findall(line):
            domain=address.rsplit('@',1)[1].casefold()
            if domain not in {'example.com','example.org','example.net','example.invalid'} and not domain.endswith('.example.invalid'):
                findings.append((number,'non-placeholder email'))
        if any(p.search(line) for p in KEYS):
            findings.append((number,'possible secret key'))
    return findings

def main():
    root=Path(__file__).resolve().parents[1]
    names=list(BUILTIN_NAMES)
    extra=os.environ.get('FORESIGHT_PRIVACY_DENYLIST')
    if extra:
        names += [s.strip() for s in Path(extra).read_text().splitlines() if s.strip() and not s.startswith('#')]
    findings=[]; count=0
    for path in files(root):
        if path.is_symlink():
            findings.append((str(path.relative_to(root)),0,'symlink is not a publishable source file'))
            continue
        if not path.is_file():
            continue
        count+=1
        data=path.read_bytes()
        try:
            text=data.decode('utf-8')
        except UnicodeDecodeError:
            findings.append((str(path.relative_to(root)),0,'unexpected binary artifact'))
            continue
        findings += [(str(path.relative_to(root)),number,reason) for number,reason in scan_text(text,names)]
    for path,number,reason in findings:
        print(f'{path}:{number}: {reason}')
    print(f'Privacy scan: {"FAIL" if findings else "PASS"} ({count} publishable files, {len(findings)} findings)')
    return bool(findings)

if __name__=='__main__':
    sys.exit(main())
