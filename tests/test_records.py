import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from records import ASK, PAID, TWO, publish


class ReportTests(unittest.TestCase):
    def test_source_periods_and_geographies_stay_separate(self):
        metro = 'Halifax, Census metropolitan area (CMA)'
        asking = {'2024-04': [1000, 'E'], '2025-04': 1200, '2025-07': [None, 'F']}
        paid = {'2025-04': 950}
        data = {'series': {ASK: {TWO: {metro: asking}}, PAID: {TWO: {metro: paid}}}}
        series = {'rent': {'2024': {'value': 100, 'flags': ''}, '2025': {'value': 103, 'flags': ''}},
                  'earnings': {'2024': {'value': 900, 'flags': 'B'}, '2025': {'value': 945, 'flags': 'B'}},
                  'completions': {'2023': {'value': 1350, 'flags': ''}}}
        context = {'geographies': {'Nova Scotia': series}, 'checked_at': '2025-11-28',
                   'sources': {k: {'table': '12345678', 'label': k} for k in series}}
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            (stage / 'data').mkdir()
            (stage / 'data/context.json').write_text(json.dumps(context))
            publish(stage, data, {'retrieved': '2025-11-28'})
            report = (stage / 'records/halifax-rent/index.html').read_text()
            annual = (stage / 'records/nova-scotia-rent-and-earnings/index.html').read_text()
            self.assertIn('$250 above average paid rent ($950 per month)', report)
            self.assertIn('The latest quarter in the table is Q3 2025', report)
            self.assertIn('newest local figure available is from Q2 2025', report)
            self.assertIn('$1,000 [E] in Q2 2024', report)
            self.assertIn('From 2024 to 2025, rent prices rose 3.0% and average weekly earnings rose 5.0%', annual)
            self.assertIn('1,350 completed homes in 2023', annual)
            self.assertIn('Unavailable', annual)
            urls = [el.text for el in ElementTree.parse(stage / 'sitemap.xml').findall('.//{*}loc')]
            self.assertEqual(len(urls), 3)
            for url in urls:
                local = stage / url.split('/housing-pulse/')[1] / 'index.html'
                self.assertIn(f'rel="canonical" href="{url}"', local.read_text())
