import csv
import tempfile
import unittest
from pathlib import Path
from quality import validate_csv, stats

class QualityTests(unittest.TestCase):
    def test_metrics(self):
        r={'minutes':'800','tries':'5','points':'25','meters':'400','tackles':'90','missed_tackles':'10'}
        s=stats(r)
        self.assertEqual(s['tries_per_80'],0.5)
        self.assertEqual(s['tackle_success_pct'],90)
    def test_minimum_playing_time(self):
        self.assertIsNone(stats({'minutes':'40','tries':'3'})['tries_per_80'])
    def test_missing_is_not_zero(self):
        self.assertIsNone(stats({'minutes':'500','tries':''})['tries_per_80'])
    def test_bad_source_rejected(self):
        fields=['player','team','position','competition','season','minutes','tries','points','tackles','missed_tackles','meters','source_url']
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.csv'
            with path.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerow(dict(dict.fromkeys(fields,''),player='Test',team='Club',competition='top14',season='2025-2026',source_url='http://example.com'))
            self.assertFalse(validate_csv(path)['valid'])
if __name__=='__main__': unittest.main()
