"""Opt-in licensed CSV ingestion. No scraping or scheduled network calls."""
import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from quality import validate_csv

ROOT = Path(__file__).resolve().parent

def ingest(source, dest, license_id, approved_hosts=(), max_bytes=5_000_000):
    if not license_id.strip():
        raise ValueError('An explicit dataset license or permission identifier is required')
    dest = Path(dest)
    if source.startswith('https://'):
        host = urlsplit(source).hostname
        if not host or host not in approved_hosts:
            raise ValueError('Remote host not in explicit allowlist')
        req = Request(source, headers={'User-Agent':'RugbyStatsExpert/0.5 (+licensed data import)'})
        with urlopen(req, timeout=15) as response:
            if urlsplit(response.geturl()).hostname not in approved_hosts:
                raise ValueError('Redirected to a non-allowlisted host')
            data = response.read(max_bytes + 1)
    else:
        data = Path(source).read_bytes()
    if len(data) > max_bytes: raise ValueError('CSV exceeds 5 MB limit')
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=dest.parent, suffix='.csv', delete=False) as tmp:
            temp_path = Path(tmp.name)
            tmp.write(data)
        check = validate_csv(temp_path)
        if not check['valid']: raise ValueError('Invalid CSV: ' + '; '.join(check['errors'][:10]))
        manifest = {
            'source':source, 'license_reference':license_id,
            'imported_at_utc':datetime.now(timezone.utc).isoformat(),
            'sha256':hashlib.sha256(data).hexdigest(),
            'rows':len(check['records']), 'warnings':check['warnings'],
            'note':'License must independently permit public redistribution; identifier is not proof.'
        }
        os.replace(temp_path, dest)
        temp_path = None
        dest.with_suffix('.provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        return manifest
    finally:
        if temp_path and temp_path.exists(): temp_path.unlink()

if __name__ == '__main__':
    p=argparse.ArgumentParser(description='Import an explicitly licensed rugby CSV')
    p.add_argument('--source',required=True,help='Local CSV path or HTTPS URL')
    p.add_argument('--license-reference',required=True,help='Your permission/license reference')
    p.add_argument('--allow-host',action='append',default=[],help='Explicitly permitted remote hostname')
    p.add_argument('--dest',default=str(ROOT/'data'/'players.csv'))
    args=p.parse_args()
    print(json.dumps(ingest(args.source,args.dest,args.license_reference,args.allow_host),indent=2,ensure_ascii=False))
