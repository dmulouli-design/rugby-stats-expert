"""Read-only rugby API. Local-first; public deployment requires auth and HTTPS proxy."""
import json, os, hmac
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from quality import validate_csv, stats, number

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('RUGBY_DATA_CSV', ROOT/'data'/'players.csv'))
PROVENANCE = DATA.with_suffix('.provenance.json')

def dataset():
    if not DATA.exists():
        return {'valid':False,'errors':['CSV not found'],'warnings':[],'records':[]}
    return validate_csv(DATA)

def query_data(route, params):
    result=dataset(); rows=result['records']
    competition=params.get('competition',[''])[0]; season=params.get('season',[''])[0]
    rows=[r for r in rows if (not competition or r['competition']==competition) and (not season or r['season']==season)]
    try: threshold=max(1,min(10000,int(params.get('min_minutes',['160'])[0])))
    except ValueError: threshold=160
    try: limit=max(1,min(100,int(params.get('limit',['20'])[0])))
    except ValueError: limit=20
    common={'errors':result['errors'],'warnings':result['warnings'],'source_type':'operator_authorized_csv','data_available':bool(result['records'])}
    if route=='/api/status':
        prov=None
        if PROVENANCE.exists():
            try: prov=json.loads(PROVENANCE.read_text(encoding='utf-8'))
            except (ValueError,OSError): pass
        return 200 if result['valid'] else 422,dict(common,ready=result['valid'] and bool(result['records']),count=len(result['records']),provenance=prov)
    if not result['valid']: return 422,dict(common,records=[])
    if route=='/api/players':
        name=params.get('q',[''])[0].casefold().strip()
        found=[dict(r,advanced=stats(r,threshold)) for r in rows if name in (r['player']+' '+r['team']).casefold()]
        return 200,dict(common,total=len(found),records=found[:limit])
    if route=='/api/leaderboard':
        metric=params.get('metric',['tries'])[0]
        allowed={'minutes','tries','points','tackles','missed_tackles','meters','turnovers_won','tries_per_80','points_per_80','meters_per_80','tackle_success_pct'}
        if metric not in allowed: return 400,{'error':'unsupported metric','allowed':sorted(allowed)}
        ranked=[]
        for r in rows:
            adv=stats(r,threshold)
            val=adv.get(metric) if metric in adv else number(r.get(metric))
            if val is not None: ranked.append({'player':r['player'],'team':r['team'],'position':r['position'],'value':val,'source_url':r.get('source_url','')})
        ranked.sort(key=lambda x:(-x['value'],x['player']))
        return 200,dict(common,metric=metric,total=len(ranked),results=ranked[:limit],min_minutes=threshold)
    if route=='/api/teams':
        teams={}
        for r in rows:
            k=(r['team'],r['competition'],r['season'])
            t=teams.setdefault(k,{'team':k[0],'competition':k[1],'season':k[2],'player_records':0,'minutes_sum':0,'points_sum':0,'tries_sum':0,'incomplete_fields':[]})
            t['player_records']+=1
            for field,target in [('minutes','minutes_sum'),('points','points_sum'),('tries','tries_sum')]:
                v=number(r.get(field))
                if v is None:
                    if field not in t['incomplete_fields']: t['incomplete_fields'].append(field)
                else: t[target]+=v
        # Sums of player records are NOT official team match statistics.
        return 200,dict(common,total=len(teams),teams=list(teams.values())[:limit],note='Player-record aggregates, not official team totals. Missing values are not imputed.')
    return 404,{'error':'not found'}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT/'web'),**kwargs)
    def do_GET(self):
        route=urlparse(self.path)
        if route.path not in ('/api/status','/api/players','/api/leaderboard','/api/teams'):
            return super().do_GET()
        token=os.getenv('RUGBY_API_KEY','')
        if token and not hmac.compare_digest(self.headers.get('X-API-Key',''),token):
            return self.reply(401,{'error':'unauthorized'})
        code,payload=query_data(route.path,parse_qs(route.query))
        self.reply(code,payload)
    def reply(self,code,payload):
        raw=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers();self.wfile.write(raw)

if __name__=='__main__':
    host=os.getenv('RUGBY_BIND','127.0.0.1')
    if host not in ('127.0.0.1','localhost','::1') and not os.getenv('RUGBY_API_KEY'):
        raise SystemExit('Public binding requires RUGBY_API_KEY and an HTTPS reverse proxy')
    ThreadingHTTPServer((host,int(os.getenv('PORT','8765'))),Handler).serve_forever()
