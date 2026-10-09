import unittest
from api import query_data

class APITests(unittest.TestCase):
    def test_empty_status(self):
        code,data=query_data('/api/status',{})
        self.assertIn(code,(200,422))
        self.assertIn('ready',data)
    def test_leaderboard_empty(self):
        code,data=query_data('/api/leaderboard',{'metric':['tries']})
        self.assertEqual(code,200)
        self.assertEqual(data['total'],0)
    def test_bad_metric(self):
        code,data=query_data('/api/leaderboard',{'metric':['password']})
        self.assertEqual(code,400)
    def test_teams_empty(self):
        code,data=query_data('/api/teams',{})
        self.assertEqual(code,200)
        self.assertEqual(data['total'],0)
    def test_filter_empty(self):
        code,data=query_data('/api/players',{'competition':['top14']})
        self.assertEqual(code,200)
        self.assertEqual(data['total'],0)
