import csv
import json
import tempfile
import unittest
from pathlib import Path
from ingest import ingest

class IngestTests(unittest.TestCase):
    def test_valid_local_import_and_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.csv'; dest=Path(d)/'players.csv'
            src.write_text('player,team,position,competition,season,minutes,tries,points,tackles,missed_tackles,meters,source_url\nJoueur Exemple,Club Exemple,9,top14,2025-2026,800,5,25,50,5,300,https://example.org/stats\n',encoding='utf-8')
            manifest=ingest(str(src),dest,'TEST-PERMISSION')
            self.assertEqual(manifest['rows'],1)
            self.assertEqual(json.loads(dest.with_suffix('.provenance.json').read_text())['sha256'],manifest['sha256'])
    def test_rejects_unlicensed(self):
        with self.assertRaises(ValueError): ingest('missing.csv','dest.csv','')
    def test_rejects_remote_not_allowlisted(self):
        with self.assertRaises(ValueError): ingest('https://example.org/data.csv','dest.csv','permission',[])
    def test_rejects_invalid_without_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'bad.csv'; dest=Path(d)/'players.csv'
            src.write_text('bad,columns\n1,2\n')
            dest.write_text('existing')
            with self.assertRaises(ValueError): ingest(str(src),dest,'TEST')
            self.assertEqual(dest.read_text(),'existing')
if __name__=='__main__': unittest.main()
