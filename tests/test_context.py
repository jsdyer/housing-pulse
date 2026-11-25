import csv,io,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh_context import collect
class ContextTests(unittest.TestCase):
 def blob(self,code,rows):
  s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);b=io.BytesIO()
  with zipfile.ZipFile(b,'w') as z:z.writestr(code+'.csv',s.getvalue())
  return b.getvalue()
 def data(self,missing=False):
  common={'GEO':'Extra province','STATUS':'','SYMBOL':'','VECTOR':'v1'}
  rent=[dict(common,REF_DATE=f'2025-{m:02}',**{'Products and product groups':'Rent','UOM':'2002=100','VALUE':str(100+m)}) for m in range(1,13)]
  earnings=[dict(common,REF_DATE=f'2025-{m:02}',**{'Estimate':'Average weekly earnings including overtime for all employees','North American Industry Classification System (NAICS)':'Industrial aggregate excluding unclassified businesses [11-91N]','VALUE':'1000'}) for m in range(1,12 if missing else 13)]
  completion=[dict(common,REF_DATE='2025',**{'Housing estimates':'Housing completions','Type of unit':'Total units','VALUE':''})]
  return {code:self.blob(code,rows) for code,rows in [('18100004',rent),('14100223',earnings),('34100126',completion)]}
 def test_full_year_mean_and_missing_completions(self):
  d=collect(self.data(),{'geographies':['Extra province'],'start_year':'2001'},'2026-01-01');s=d['geographies']['Extra province'];self.assertEqual(s['rent']['2025']['value'],106.5);self.assertEqual(s['earnings']['2025']['value'],1000);self.assertIsNone(s['completions']['2025']['value'])
 def test_incomplete_year_not_annualized(self):
  s=collect(self.data(True),{'geographies':['Extra province'],'start_year':'2001'},'2026-01-01')['geographies']['Extra province'];self.assertIsNone(s['earnings']['2025']['value']);self.assertEqual(s['earnings']['2025']['months'],11)
 def test_unmatched_geography_fails(self):
  with self.assertRaises(ValueError):collect(self.data(),{'geographies':['Different province'],'start_year':'2001'},'2026-01-01')
if __name__=='__main__':unittest.main()
