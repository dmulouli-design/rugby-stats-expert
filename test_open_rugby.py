import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from open_rugby import browse, source_status, request_json
class OpenRugbyTests(unittest.TestCase):
    def test_status_license_not_assumed(self):
        x=source_status(lambda url: {"html_url":"https://github.com/transientlunatic/Rugby-Data","pushed_at":"2026-10-01","license":None})
        self.assertFalse(x["redistribution_approved"])
    def test_browse(self):
        r=browse("json",lambda url:[{"name":"top14","path":"json/top14","type":"dir","html_url":"https://github.com/example"}])
        self.assertEqual(r[0]["name"],"top14")
    def test_reject_traversal(self):
        with self.assertRaises(ValueError): browse("json/../private")
    def test_reject_external(self):
        with self.assertRaises(ValueError): request_json("https://example.com/a")
if __name__=='__main__': unittest.main()
