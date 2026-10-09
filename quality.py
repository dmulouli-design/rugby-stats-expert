"""Validation and reproducible expert metrics. No data acquisition or scraping."""
import csv
from pathlib import Path
from urllib.parse import urlparse

COMPETITIONS = {'top14', 'prod2', 'nationale'}
REQUIRED = {'player','team','position','competition','season','minutes','tries','points','tackles','missed_tackles','meters','source_url'}
NUMERIC = {'minutes','tries','points','tackles','missed_tackles','meters','turnovers_won'}

def number(value):
    if value is None or str(value).strip() == '':
        return None
    try:
        n = float(str(value).replace(',', '.'))
        return n if n == n and abs(n) != float('inf') else None
    except ValueError:
        return None

def validate_csv(path):
    path = Path(path)
    errors, warnings, cleaned = [], [], []
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            return {'valid': False, 'errors': ['Missing columns: '+', '.join(sorted(missing))], 'warnings': [], 'records': []}
        seen = set()
        for line, row in enumerate(reader, 2):
            if not any(row.values()): continue
            key = (row['player'].strip().casefold(), row['team'].strip().casefold(), row['competition'], row['season'])
            if key in seen: errors.append(f'Line {line}: duplicate player/team/competition/season')
            seen.add(key)
            if row['competition'] not in COMPETITIONS: errors.append(f'Line {line}: unknown competition')
            if not row['player'].strip() or not row['team'].strip() or not row['season'].strip(): errors.append(f'Line {line}: missing identity')
            for field in NUMERIC:
                value = row.get(field, '')
                if value and (number(value) is None or number(value) < 0): errors.append(f'Line {line}: invalid {field}')
            url = row.get('source_url','').strip()
            if url and (urlparse(url).scheme != 'https' or not urlparse(url).netloc): errors.append(f'Line {line}: source_url must be HTTPS')
            if not url: warnings.append(f'Line {line}: no source_url (not publicly verifiable)')
            cleaned.append(row)
    return {'valid': not errors, 'errors': errors, 'warnings': warnings, 'records': cleaned if not errors else []}

def stats(row, min_minutes=160):
    mins = number(row.get('minutes'))
    def per80(field):
        val = number(row.get(field))
        return round(val*80/mins, 3) if mins and mins >= min_minutes and val is not None else None
    won, missed = number(row.get('tackles')), number(row.get('missed_tackles'))
    return {'points_per_80':per80('points'), 'tries_per_80':per80('tries'), 'meters_per_80':per80('meters'),
            'tackle_success_pct': round(100*won/(won+missed), 2) if won is not None and missed is not None and won+missed > 0 and mins and mins >= min_minutes else None,
            'eligible': bool(mins is not None and mins >= min_minutes), 'minimum_minutes': min_minutes}
