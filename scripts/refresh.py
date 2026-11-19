"""Publish regional comparisons from five survey tables with independent units and frequencies."""
from source import rows,publish
from collections import defaultdict

SOURCES={
 '34100143':('Monthly','CMHC Starts and Completions Survey in centres of 10,000 or more. Starts and completions count units during the month. Under construction counts units at the survey date.'),
 '34100148':('Monthly','CMHC housing starts in centres of 10,000 or more. The intended market describes the housing at construction start.'),
 '34100149':('Monthly','CMHC Market Absorption Survey of newly completed units. Inventory is the reported stock of unabsorbed units at the survey date.'),
 '34100130':('Annual','CMHC weighted vacancy rate for privately initiated row and apartment structures with three or more units in the published metropolitan areas.'),
 '46100092':('Quarterly','Statistics Canada experimental rent estimates. Asking rents describe advertised units. Paid rents describe the published paid-rent estimate. Quarterly observations are shown by quarter.')}
def definition(code,r):
    if code=='34100143':return r['Housing estimates'],r['Type of unit']
    if code=='34100148':return 'Starts by intended market',r['Type of market']+' · '+r['Type of dwelling unit']
    if code=='34100149':return r['Completed dwelling units'],r['Type of dwelling unit']
    if code=='34100130':return 'Rental vacancy rate','Surveyed structures'
    return r['Estimates'],r['Rental unit type']

def main():
    metrics={};values={};all_months=[];count=0
    for code,(frequency,note) in SOURCES.items():
        stream=rows(code);head=next(stream)
        for record in stream:
            if len(record)!=len(head):continue
            r=dict(zip(head,record));date=r['REF_DATE']; g=r['GEO']
            if date<'2010':continue
            metric,kind=definition(code,r); u={'Units':'units','Rate':'%','Dollars':'CAD/month'}[r['UOM']]
            info=metrics.setdefault(metric,{'table':code,'frequency':frequency,'unit':u,'note':note})
            if info['table']!=code or info['unit']!=u:raise ValueError('Unexpected unit or table')
            events=values.setdefault(metric,{}).setdefault(kind,{}).setdefault(g,{})
            if date in events:raise ValueError(f'Duplicate {code} {g} {date}')
            raw=r['VALUE'];quality=r['STATUS']
            v=float(raw) if raw and '.' in raw else int(raw) if raw else None
            events[date]=[v,quality] if quality else v
            if v is not None:count+=1
            if frequency=='Monthly':all_months.append(date)
    if count<50000 or 'Halifax, Nova Scotia' not in values['Starts by intended market']['Rental · Total units']:
        raise ValueError('Incomplete housing snapshot')
    publish({'metrics':metrics,'series':values},dict(start=min(all_months),end=max(all_months),count=count))
if __name__=='__main__':main()
