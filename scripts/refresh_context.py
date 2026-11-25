"""Province-matched annual rent-price, earnings and all-area completion context."""
import argparse,csv,io,json,math,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROVINCES=['Canada','Newfoundland and Labrador','Prince Edward Island','Nova Scotia','New Brunswick','Quebec','Ontario','Manitoba','Saskatchewan','Alberta','British Columbia']
def rows(raw,code):
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  info=z.getinfo(code+'.csv')
  if info.file_size>350_000_000:raise ValueError('Expanded source too large')
  with z.open(info) as f:yield from csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig'))
def collect(blobs,config,checked):
 out={g:{'rent':{},'earnings':{},'completions':{}} for g in config['geographies']};monthly={g:{'rent':{},'earnings':{}} for g in out};vectors={g:{} for g in out}
 for code in ['18100004','14100223','34100126']:
  for r in rows(blobs[code],code):
   g=r['GEO'];d=r['REF_DATE']
   if g not in out or d[:4]<config['start_year']:continue
   if code=='18100004':
    if r['Products and product groups']!='Rent' or r['UOM']!='2002=100':continue
    key='rent'
   elif code=='14100223':
    if r['Estimate']!='Average weekly earnings including overtime for all employees' or r['North American Industry Classification System (NAICS)']!='Industrial aggregate excluding unclassified businesses [11-91N]':continue
    key='earnings'
   else:
    if r['Housing estimates']!='Housing completions' or r['Type of unit']!='Total units':continue
    key='completions'
   value=float(r['VALUE']) if r['VALUE'] else None
   if value is not None and (not math.isfinite(value) or value<0):raise ValueError('Invalid statistic')
   target=out[g][key] if key=='completions' else monthly[g][key]
   if d in target:raise ValueError('Duplicate compatible series')
   target[d]={'value':value,'flags':r['STATUS'] or r['SYMBOL']}
   vectors[g][key]=r['VECTOR']
 for g in out:
  for key in ['rent','earnings']:
   years=sorted({d[:4] for d in monthly[g][key]})
   for year in years:
    months=[monthly[g][key].get(f'{year}-{m:02}') for m in range(1,13)]
    valid=[r for r in months if r is not None and r['value'] is not None]
    out[g][key][year]={'value':sum(r['value'] for r in valid)/12 if len(valid)==12 else None,'months':len(valid),'flags':','.join(sorted({r['flags'] for r in valid if r['flags']}))}
  if any(not out[g][key] for key in out[g]):raise ValueError('Missing configured geography/series')
 return {'schema':1,'checked_at':checked,'geographies':out,'vectors':vectors,'sources':{'rent':{'table':'18100004','label':'Rent price index','unit':'2002=100','method':'Arithmetic average of all 12 monthly rent CPI indexes, not seasonally adjusted. Measures existing rent prices, not advertised asking rent.'},'earnings':{'table':'14100223','label':'Average weekly earnings','unit':'CAD/week','method':'Arithmetic average of all 12 monthly seasonally adjusted average weekly earnings, including overtime; industrial aggregate excluding unclassified businesses.'},'completions':{'table':'34100126','label':'Housing completions','unit':'units/year','method':'Published annual completions, all areas, total units. Missing source years stay unavailable; starts are never substituted.'}}}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source-dir',type=Path);a=p.parse_args();c=json.loads((ROOT/'config/context.json').read_text());blobs={}
 for code in ['18100004','14100223','34100126']:
  if a.source_dir:raw=(a.source_dir/(code+'.zip')).read_bytes()
  else:
   with urllib.request.urlopen(urllib.request.Request(f'https://www150.statcan.gc.ca/n1/tbl/csv/{code}-eng.zip',headers={'User-Agent':'CoolCode HousingPulse (+https://coolcode.ca/housing-pulse/)'}),timeout=160) as response:
    if not response.url.startswith('https://www150.statcan.gc.ca/'):raise ValueError('Unexpected source redirect')
    raw=response.read(40_000_001)
   if len(raw)>40_000_000:raise ValueError('Source too large')
  blobs[code]=raw
 d=collect(blobs,c,datetime.now(timezone.utc).isoformat(timespec='seconds'));target=ROOT/'web/data/context.json';tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(d,separators=(',',':'))+'\n');tmp.replace(target);print(f"Compatible context: {len(d['geographies'])} geographies")
if __name__=='__main__':main()
