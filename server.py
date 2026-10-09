"""Rugby Stats Expert — MCP read-only server, Python 3.11+."""
import csv
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

app = FastMCP('Rugby Stats Expert', host='0.0.0.0', port=int(os.getenv('PORT', '10000')), stateless_http=True)
DATA = Path(os.getenv('RUGBY_DATA_CSV', Path(__file__).parent / 'data' / 'players.csv'))
ALLOWED = {'top14', 'prod2', 'nationale'}
METRICS = {'points', 'tries', 'tackles', 'missed_tackles', 'meters', 'minutes', 'turnovers_won'}

def records():
    if not DATA.exists():
        return []
    with DATA.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def metric(row, key):
    try:
        return float(row[key])
    except (ValueError, KeyError, TypeError):
        return None

def enrich(row):
    r = dict(row)
    minutes = metric(r, 'minutes')
    tackles = metric(r, 'tackles')
    missed = metric(r, 'missed_tackles')
    r['tries_per_80'] = round(metric(r, 'tries') * 80 / minutes, 3) if minutes and metric(r, 'tries') is not None else None
    r['meters_per_80'] = round(metric(r, 'meters') * 80 / minutes, 1) if minutes and metric(r, 'meters') is not None else None
    r['tackle_success_pct'] = round(100 * tackles / (tackles + missed), 1) if tackles is not None and missed is not None and tackles + missed > 0 else None
    return r

@app.tool()
def competitions() -> dict:
    """List supported French rugby competitions and available dataset status."""
    rows = records()
    return {'competitions': sorted(ALLOWED), 'records_loaded': len(rows), 'data_status': 'imported' if rows else 'no_data', 'note': 'No licensed data is bundled.'}

@app.tool()
def find_players(query: str, competition: str = '', season: str = '') -> dict:
    """Search player names or teams in the imported dataset."""
    q = query.casefold().strip()
    rows = [enrich(r) for r in records() if q in (r.get('player','') + ' ' + r.get('team','')).casefold() and (not competition or r.get('competition') == competition) and (not season or r.get('season') == season)]
    return {'results': rows[:50], 'total': len(rows), 'data_status': 'imported' if rows else 'not_available'}

@app.tool()
def leaderboard(competition: str, season: str, statistic: str = 'tries', limit: int = 10) -> dict:
    """Rank players by a numeric statistic; missing values are excluded."""
    if competition not in ALLOWED or statistic not in METRICS | {'tries_per_80', 'meters_per_80', 'tackle_success_pct'}:
        return {'error': 'Invalid competition or statistic'}
    rows = [enrich(r) for r in records() if r.get('competition') == competition and r.get('season') == season]
    ranked = [(r, metric(r, statistic)) for r in rows]
    ranked = sorted([(r, v) for r, v in ranked if v is not None], key=lambda rv: rv[1], reverse=True)
    return {'competition': competition, 'season': season, 'statistic': statistic, 'results': [{'player': r.get('player'), 'team': r.get('team'), 'value': v, 'source_url': r.get('source_url')} for r, v in ranked[:max(1,min(limit,50))]], 'data_status': 'imported' if rows else 'not_available'}

@app.tool()
def compare_players(player_a: str, player_b: str, competition: str, season: str) -> dict:
    """Compare two player records for the same competition and season."""
    rows = [enrich(r) for r in records() if r.get('competition') == competition and r.get('season') == season]
    def get(name):
        matches = [r for r in rows if r.get('player','').casefold() == name.casefold()]
        return matches[0] if len(matches) == 1 else None
    return {'player_a': get(player_a), 'player_b': get(player_b), 'note': 'Null indicates unavailable data or ambiguous player. Metrics are not position-adjusted.'}


# Source discovery tools are read-only; do not claim that this is a licensed player feed.
from open_rugby import source_status, browse

@app.tool()
def external_source_status() -> dict:
    """Check public Rugby-Data source metadata and its license verification status."""
    try: return source_status()
    except Exception as exc: return {"error": type(exc).__name__, "data_status": "source_unavailable"}

@app.tool()
def external_source_files(path: str = "json") -> dict:
    """Browse public Rugby-Data match dataset directories; does not import or redistribute files."""
    try: return {"path": path, "files": browse(path), "redistribution_approved": False}
    except Exception as exc: return {"error": type(exc).__name__, "data_status": "source_unavailable"}

if __name__ == "__main__":
    app.run(transport="streamable-http")
