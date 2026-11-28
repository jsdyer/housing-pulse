"""Render metro rent comparisons and province-matched annual housing reports."""
from collections import defaultdict
from html import escape
from itertools import chain
import json
import re
import unicodedata
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

ORIGIN = 'https://coolcode.ca/housing-pulse/'
TABLE = 'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid='
RENT_SOURCE = TABLE + '4610009201'
ASK, PAID = 'Average asking rent', 'Average paid rent'
TWO = 'Apartment - 2 bedrooms'
AGGREGATE = 'All census metropolitan areas'
# Geography groups for directory navigation only. Numeric comparisons use exact source keys.
REGIONS = {
    'Newfoundland and Labrador': ["St. John's"],
    'Nova Scotia': ['Halifax'],
    'New Brunswick': ['Moncton', 'Saint John', 'Fredericton'],
    'Quebec': ['Montréal', 'Québec', 'Saguenay', 'Sherbrooke', 'Trois-Rivières', 'Drummondville', 'Ottawa - Gatineau (Quebec part)'],
    'Ontario': ['Toronto', 'Ottawa - Gatineau (Ontario part)', 'Hamilton', 'London', 'Oshawa', 'Windsor', 'Kitchener - Cambridge - Waterloo', 'St. Catharines - Niagara', 'Kingston', 'Guelph', 'Barrie', 'Thunder Bay', 'Greater Sudbury', 'Brantford', 'Peterborough', 'Belleville - Quinte West'],
    'Manitoba': ['Winnipeg'],
    'Saskatchewan': ['Regina', 'Saskatoon'],
    'Alberta': ['Calgary', 'Edmonton', 'Lethbridge', 'Red Deer'],
    'British Columbia': ['Vancouver', 'Victoria', 'Abbotsford - Mission', 'Kelowna', 'Nanaimo', 'Kamloops', 'Chilliwack'],
}


def slug(text):
    ascii_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return re.sub('[^a-z0-9]+', '-', ascii_text.lower().replace("'", '')).strip('-')


def link(url, label):
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def quarter(date):
    year, month = date.split('-')
    return f'Q{(int(month) - 1) // 3 + 1} {year}'


def unpack(cell):
    return tuple(cell) if isinstance(cell, list) else (cell, '')


def cash(value):
    return f'${value:,.0f}'


def amount(cell):
    value, flag = unpack(cell)
    label = 'Unavailable' if value is None else cash(value)
    return label + (f' [{escape(flag)}]' if flag else '')


def table(headers, rows):
    heads = ''.join(f'<th scope="col">{escape(text)}</th>' for text in headers)
    body = ''.join('<tr><th scope="row">' + row[0] + '</th>' + ''.join(f'<td>{value}</td>' for value in row[1:]) + '</tr>' for row in rows)
    return f'<div class="scroll"><table><thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table></div>'


def write_page(stage, key, title, headline, description, body):
    path = 'records/' + (key + '/' if key else '')
    base = '../../' if key else '../'
    canonical = ORIGIN + path
    directory = link('../', 'Housing reports') if key else link('../', 'Housing Pulse')
    page = f'''<!doctype html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Housing Pulse</title><meta name="description" content="{escape(description, quote=True)}"><link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="{base}style.css"><script defer src="/assets/tool-metrics.js" referrerpolicy="no-referrer"></script></head>
<body data-tool-id="housing-pulse"><a class="skip" href="#main">Skip to figures</a><header><nav aria-label="Site">{directory} {link('https://coolcode.ca/', 'CoolCode.ca')}</nav>
<div class="heading"><p class="over">Housing Pulse</p><h1>{escape(headline)}</h1><p>{escape(description)}</p></div></header>
<main id="main">{body}</main><footer><p>{link(base, 'Open Housing Pulse')} · {link('/report/?tool=housing-pulse', 'Report an issue')}</p></footer></body></html>'''
    dest = stage / path
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / 'index.html').exists():
        raise ValueError(f'Duplicate report URL: {canonical}')
    (dest / 'index.html').write_text(page, encoding='utf-8')
    return canonical


def market_key(place):
    return slug(place) + '-rent'


def annual_key(place):
    return slug(place) + '-rent-and-earnings'


def links(items):
    return '<ul class="place-list">' + ''.join(f'<li>{link(url, label)}</li>' for url, label in items) + '</ul>'


def metro_views(stage, data, checked, province_names):
    source = data['series']
    stores = [source[ASK], source[PAID]]
    geos = set(chain.from_iterable(by_kind for store in stores for by_kind in store.values()))
    periods = sorted({d for store in stores for by_kind in store.values() for years in by_kind.values() for d in years})
    latest = periods[-1]
    groups = {name: group for group, names in REGIONS.items() for name in names}
    result = {}
    order = [TWO, 'Apartment - 1 bedroom', 'Apartment - No bedroom', 'Apartment - 3 or more bedrooms', 'House - 2 bedrooms', 'House - 3 or more bedrooms', 'Room']
    kinds = list(dict.fromkeys(order + sorted(set(source[ASK]) | set(source[PAID]))))
    for geo in sorted(geos - {AGGREGATE}):
        name = geo.split(',')[0]
        series = {(metric, k): source[metric].get(k, {}).get(geo, {}) for metric in [ASK, PAID] for k in kinds}
        def present(metric, kind, date):
            return unpack(series[metric, kind].get(date))[0] is not None
        # A gap in a new quarter must not remove a previously useful URL.
        date = next((d for d in reversed(periods) if any(present(m, k, d) for k in kinds for m in (ASK, PAID))), None)
        if date is None:
            continue
        metric, kind = next((m, k) for k in kinds for m in (ASK, PAID) if present(m, k, date))
        metric_label = 'asking' if metric == ASK else 'paid'
        value = series[metric, kind][date]
        subject = kind.replace('Apartment - ', '').replace('2 bedrooms', 'two-bedroom apartment').replace('1 bedroom', 'one-bedroom apartment') if kind in [TWO, 'Apartment - 1 bedroom'] else kind.lower().replace(' - ', ', ')
        description = f'Average {metric_label} rent for a {subject} was {amount(value)} per month in {quarter(date)}. Compare unit sizes, published paid rents and earlier quarters.'
        query = urlencode({'market': geo, 'unit': kind, 'measure': metric, 'quarter': date})
        body = '<section><h2>What would a renter see?</h2>'
        if date != latest:
            body += f'<p>The latest quarter in the table is {quarter(latest)}. The newest local figure available is from {quarter(date)}.</p>'
        other = source[ASK].get(kind, {}).get(AGGREGATE, {}).get(date)
        if metric == ASK and unpack(other)[0] is not None:
            body += f'<p>For the same unit type and quarter, the asking rent across all census metropolitan areas combined was {amount(other)} per month. Use the local asking figure to put a listing in context.</p>'
        else:
            body += '<p>Compare a listing with the asking estimate for its unit type. The paid estimate describes what existing renters pay.</p>'
        paired = all(present(m, kind, date) for m in (ASK, PAID))
        if paired:
            a = unpack(series[ASK, kind][date])[0]
            p = unpack(series[PAID, kind][date])[0]
            diff = a - p
            gap = f'{cash(abs(diff))} {"above" if diff > 0 else "below"}' if diff else 'the same as'
            body += f'<p>For this unit type, average asking rent was {gap} average paid rent ({amount(series[PAID, kind][date])} per month). The two averages cover different groups of homes. Lease dates, unit features and included utilities can affect the gap.</p>'
        before = str(int(date[:4]) - 1) + date[4:]
        if present(metric, kind, before):
            past = series[metric, kind][before]
            diff = unpack(value)[0] - unpack(past)[0]
            change = 'unchanged' if diff == 0 else f'{"up" if diff > 0 else "down"} {cash(abs(diff))} per month'
            body += f'<p>A year earlier the {metric_label} estimate for this unit type was {amount(past)} in {quarter(before)}, so the published average is {change}.</p>'
        body += '<p>' + link('../../?' + query + '#content', 'Compare this market with another') + '</p></section>'
        rows = [(escape(k), amount(series[ASK,k].get(date)), amount(series[PAID,k].get(date))) for k in kinds if geo in source[ASK].get(k,{}) or geo in source[PAID].get(k,{})]
        heading = ('Census metropolitan area part' if ' part)' in geo else 'Census metropolitan area')
        body += f'<section><h2>Monthly rents by unit type</h2><p>{escape(heading)} · {quarter(date)} · Canadian dollars per month</p>' + table(['Unit type', 'Average asking rent', 'Average paid rent'], rows)
        body += '<p>Unavailable means no usable estimate for that cell. E indicates use with caution, F indicates too unreliable to publish, and .. means unavailable for that period.</p></section>'
        history = [d for d in periods if d <= date and (d in series[ASK,kind] or d in series[PAID,kind])][-8:]
        body += f'<section><h2>Recent quarters for {escape(kind.lower())}</h2>' + table(['Quarter', 'Average asking rent', 'Average paid rent'], [(quarter(d),amount(series[ASK, kind].get(d)),amount(series[PAID, kind].get(d))) for d in reversed(history)]) + '</section>'
        group = groups.get(name)
        more = [('../', 'All Canadian housing reports'), ('/movebench/', 'Compare moving costs using your own rent and job offers')]
        if name == 'Halifax':
            more.insert(0, ('/field-notes/comparing-halifax-rent-and-child-care/', 'Compare Halifax rent and child care'))
        if group in province_names:
            more.insert(0, ('../' + annual_key(group) + '/', f'Rent and earnings growth in {group}'))
        body += '<section><h2>Source and next comparisons</h2><p>' + link(RENT_SOURCE, 'Statistics Canada table 46-10-0092-01') + f' · Experimental estimates · Source retrieved {escape(checked)}. The geography is {escape(geo)}. Listings and occupied homes can differ in neighbourhood, size and amenities.</p>' + links(more) + '</section>'
        result[name] = write_page(stage, market_key(name), f'{name} average apartment rents by bedroom', f'What does it cost to rent in {name}?', description, body)
    return result


def annual_views(stage, context, markets):
    result = {}
    for name, series in context['geographies'].items():
        def observation(metric, year):
            return series[metric].get(year, {}).get('value')
        def numeric(metric, year):
            return observation(metric, year) is not None
        def display(metric, year):
            value = observation(metric, year)
            if value is None:
                return 'Unavailable'
            label = {'rent': '{:,.2f}', 'earnings': '${:,.2f}', 'completions': '{:,.0f}'}[metric].format(value)
            flags = series[metric][year]['flags']
            return label + (f' [{escape(flags)}]' if flags else '')
        years = sorted(set(series['rent']) | set(series['earnings']) | set(series['completions']))
        common = [y for y in years if all(numeric(k,y) for k in ('rent','earnings'))]
        if len(common) < 2:
            continue
        end = common[-1]
        earlier = [y for y in common[:-1] if int(y) >= int(end)-5]
        start = earlier[0] if earlier else common[-2]
        changes = {k: (observation(k,end)/observation(k,start)-1)*100 for k in ('rent','earnings') if observation(k,start) > 0}
        def movement(value):
            return 'held steady' if abs(value) < 0.05 else ('rose' if value > 0 else 'fell') + f' {abs(value):.1f}%'
        description = f'Compare {start}–{end} rental price growth with average weekly earnings in {name} using complete calendar years.'
        if len(changes) == 2:
            description = f'From {start} to {end}, rent prices {movement(changes["rent"])} and average weekly earnings {movement(changes["earnings"])} in {name}.'
        body = f'<section><h2>How did pay compare with rent prices?</h2><p>The rent index went from {display("rent",start)} to {display("rent",end)} (2002 = 100). Average weekly earnings went from {display("earnings",start)} to {display("earnings",end)} over the same years.</p>'
        source_label = 'Canada' if name == 'Canada' else 'the whole province'
        body += f'<p>These figures cover {source_label}. They show how rental prices changed alongside gross payroll earnings, including overtime. To budget for a home, use your own take-home pay and the advertised monthly rent.</p><p>' + link('../../?' + urlencode({'province':name}) + '#annual', 'Choose a different period in Housing Pulse') + '</p></section>'
        completion_years = [y for y in years if numeric('completions', y)]
        if completion_years:
            year = completion_years[-1]
            body += f'<section><h2>How many homes were completed?</h2><p>The latest published all-area count in this series is {display("completions",year)} completed homes in {year}. It counts completed dwelling units across all intended markets, including owner-occupied housing.</p></section>'
        rows = [(y,display('rent',y),display('earnings',y),display('completions',y)) for y in reversed(years) if y <= end]
        body += '<section><h2>Annual figures</h2>' + table(['Year','Rent index (2002 = 100)','Average earnings (CAD/week)','Completed homes'], rows)
        body += '<p>The index and earnings are averages of 12 numeric monthly observations. Missing values remain unavailable. Brackets retain source flags, including flags on contributing months.</p></section>'
        source_links = [link(TABLE + context['sources'][k]['table'] + '01', context['sources'][k]['label']) for k in ('rent','earnings','completions')]
        more = [('../' + market_key(m) + '/', f'{m} rent by bedroom') for m in REGIONS.get(name,[]) if m in markets]
        more += [('../', 'All housing reports'), ('/wagewindow/', 'Compare your raise with provincial inflation')]
        body += '<section><h2>Sources and next comparisons</h2><p>Official Statistics Canada tables · ' + ' · '.join(source_links) + '. Source files checked ' + escape(context['checked_at'][:10]) + '.</p>' + links(more) + '</section>'
        result[name] = write_page(stage, annual_key(name), name + ' rent prices, average earnings and housing completions', f'Rent prices and earnings in {name}', description, body)
    return result


def publish(stage, data, status):
    context = json.loads((stage / 'data/context.json').read_text(encoding='utf-8'))
    provinces = {name for name, series in context['geographies'].items()
                 if sum(cell['value'] is not None and series['earnings'].get(year,{}).get('value') is not None
                        for year,cell in series['rent'].items()) >= 2}
    metros = metro_views(stage, data, status['retrieved'], provinces)
    annual = annual_views(stage, context, metros)
    if not metros or not annual:
        raise ValueError('No usable housing reports in this edition')
    body = '<section><h2>Find your rental market</h2><p>Choose a metropolitan area to see monthly rents for apartments, houses and rooms wherever estimates are available.</p>'
    grouped = set()
    for label, places in REGIONS.items():
        available = [place for place in sorted(places) if place in metros]
        if available:
            grouped.update(available)
            body += f'<h3>{escape(label)}</h3>' + links([(market_key(place)+'/', place) for place in available])
    if extras := sorted(set(metros)-grouped):
        body += '<h3>Other published markets</h3>' + links([(market_key(place)+'/', place) for place in extras])
    body += '</section><section><h2>Rent and earnings by province</h2><p>Compare the change in rent prices with weekly earnings over the same complete calendar years, and look up annual housing completions.</p>' + links([(annual_key(place)+'/',place) for place in annual]) + '</section>'
    description = 'Find apartment asking rents, rents paid by existing tenants and quarterly histories by metro area, or compare rent and earnings growth by province.'
    directory = write_page(stage, '', 'Canadian apartment rents by city and housing trends by province', 'Canadian rent and housing reports', description, body)
    mapping = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for url in [directory, *sorted(metros.values()), *sorted(annual.values())]:
        ET.SubElement(ET.SubElement(mapping, 'url'), 'loc').text = url
    ET.ElementTree(mapping).write(stage / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    examples = [name for name in ('Halifax', 'Toronto', 'Vancouver') if name in metros]
    return ' · '.join(link('records/' + market_key(name) + '/', name + ' rents') for name in examples)
