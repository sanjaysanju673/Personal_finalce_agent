import unittest

from database.repository import get_connection, get_recent_top_candidates, save_scan_result, should_refresh_market_cache


class RepositoryCacheTests(unittest.TestCase):
    def setUp(self):
        conn = get_connection()
        conn.execute("DELETE FROM stock_results")
        conn.execute("DELETE FROM scan_runs")
        conn.commit()
        conn.close()

    def test_recent_results_are_available_for_fast_mode(self):
        save_scan_result({
            "symbol": "NIFTY500",
            "top_n": 5,
            "top_candidates": [{
                "symbol": "TCS",
                "company_name": "Tata Consultancy Services",
                "industry": "IT",
                "fundamental_score": 80,
                "technical_score": 70,
                "preliminary_score": 77.0,
                "report_score": 70,
                "news_score": 80,
                "risk_score": 85,
                "final_score": 76.5,
            }],
        }, mode="fast")

        cached = get_recent_top_candidates(top_n=5, max_age_hours=24)
        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0]["symbol"], "TCS")
        self.assertFalse(should_refresh_market_cache(top_n=5, max_age_hours=24))


if __name__ == "__main__":
    unittest.main()
